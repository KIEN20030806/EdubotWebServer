#!/bin/bash
gunicorn app:app --workers 1 --preload --bind 0.0.0.0:$PORT
