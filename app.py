from flask import Flask, request, Response, jsonify
import whisper
import google.generativeai as genai
from gtts import gTTS
from pydub import AudioSegment
import wave

app = Flask(__name__)

# Load Whisper model
whisper_model = whisper.load_model("base")

# Configure Gemini
genai.configure(api_key="AIzaSyCxA64e2X5EJn-d3i9GqOZo0iqancL53Ws")
model = genai.GenerativeModel("gemini-2.0-flash")

audio_buffer = bytearray()
ready = 0
session_history = [{"role": "system", "content": "Bạn đang trò chuyện với một đứa bé trong vai trò 1 người bạn, hãy trò chuyện ngắn gọn và không chứa các ký tự, đừng lặp lại câu trả lời nha"}]

@app.route('/get_ready', methods=['GET'])
def get_ready():
    return jsonify({'ready': ready})

@app.route('/send_audio_chunk', methods=['POST'])
def receive_audio_chunk():
    global audio_buffer, ready
    ready = 0
    try:
        chunk = request.data
        audio_buffer.extend(chunk)
        return Response("Chunk received")
    except Exception as e:
        print("Lỗi nhận chunk:", e)
        return Response("Error", status=500)

@app.route('/end_audio', methods=['POST'])
def end_audio():
    global audio_buffer, ready, session_history
    try:
        with wave.open("stream_audio.wav", "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(8000)
            wav_file.writeframes(audio_buffer)

        text = whisper_model.transcribe("stream_audio.wav", language="vi")["text"]
        print("Nội dung nhận diện:", text)

        session_history = [
            {"role": "system", "content": "Bạn đang trò chuyện với một đứa bé trong vai trò 1 người bạn, trả lời đúng trọng tâm, thân thiện, không chứa các ký tự, đừng lặp lại câu trả lời nha"},
            {"role": "user", "content": text}
        ]
        response = model.generate_content([m["content"] for m in session_history])
        reply = response.text

        tts = gTTS(reply, lang='vi')
        tts.save("response_audio.mp3")

        audio = AudioSegment.from_mp3("response_audio.mp3")
        audio = audio.set_channels(1).set_sample_width(2).set_frame_rate(8000)
        audio.export("response_audio.wav", format="wav")

        audio_buffer = bytearray()
        ready = 1

        return Response("Audio processed")
    except Exception as e:
        print("Lỗi xử lý cuối:", e)
        return Response("Error processing", status=500)

@app.route('/get_audio_response', methods=['GET'])
def send_audio_response():
    try:
        with open("response_audio.wav", "rb") as f:
            return Response(f.read(), content_type="audio/wav")
    except Exception as e:
        print("Lỗi phát âm thanh:", e)
        return Response("Error sending audio", status=500)

if __name__ == '__main__':
    pass  # Render sẽ dùng start.sh
