from flask import Flask, request, Response, jsonify
import whisper
import google.generativeai as genai
from gtts import gTTS
from pydub import AudioSegment
import wave
import io

app = Flask(__name__)

# Load Whisper model 1 lần duy nhất
whisper_model = whisper.load_model("base")

# Cấu hình Google Gemini
genai.configure(api_key="AIzaSyCxA64e2X5EJn-d3i9GqOZo0iqancL53Ws")
model = genai.GenerativeModel("gemini-2.0-flash")

# Buffer lưu dữ liệu audio dạng bytes
audio_buffer = bytearray()

# Biến trạng thái báo sẵn sàng phát âm thanh
ready = 0

# Lịch sử hội thoại
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
        audio_buffer.extend(chunk)  # thêm chunk vào buffer
        print(f"Nhận chunk audio, tổng {len(audio_buffer)} bytes")
        return Response("Chunk received")
    except Exception as e:
        print("Lỗi nhận chunk:", e)
        return Response("Error", status=500)

@app.route('/end_audio', methods=['POST'])
def end_audio():
    global audio_buffer, ready, session_history

    try:
        # Lưu audio_buffer thành file WAV
        with wave.open("stream_audio.wav", "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit PCM
            wav_file.setframerate(8000)
            wav_file.writeframes(audio_buffer)
        print("Đã lưu file âm thanh hoàn chỉnh!")

        # Xử lý chuyển giọng nói thành text với Whisper
        text = whisper_model.transcribe("stream_audio.wav", language="vi")["text"]
        print("Nội dung nhận diện:", text)

        # Gửi text đến Google Gemini
        session_history = [
            {"role": "system", "content": "Bạn đang trò chuyện với một đứa bé trong vai trò 1 người bạn, trả lời đúng trọng tâm, thân thiện, không chứa các ký tự, đừng lặp lại câu trả lời nha"},
            {"role": "user", "content": text}
        ]
        response = model.generate_content([m["content"] for m in session_history])
        reply = response.text
        print("Trợ lý trả lời:", reply)

        # Tạo audio trả lời từ text trả lời
        tts = gTTS(reply, lang='vi')
        tts.save("response_audio.mp3")

        audio = AudioSegment.from_mp3("response_audio.mp3")
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_sample_width(2)  # 16-bit
        audio = audio.set_frame_rate(8000)  # 8000 Hz
        audio.export("response_audio.wav", format="wav")

        # Xóa buffer chuẩn bị nhận đoạn mới
        audio_buffer = bytearray()
        ready = 1  # báo sẵn sàng phát audio

        return Response("Audio processed")
    except Exception as e:
        print("Lỗi xử lý cuối:", e)
        return Response("Error processing", status=500)

@app.route('/get_audio_response', methods=['GET'])
def send_audio_response():
    try:
        with open("response_audio.wav", "rb") as f:
            audio_data = f.read()
        return Response(audio_data, content_type="audio/wav")
    except Exception as e:
        print("Lỗi phát âm thanh:", e)
        return Response("Error sending audio", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
