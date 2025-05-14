from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import whisper
import subprocess
from threading import Thread
import threading
from queue import Queue, Empty
# import queue
import os
from dotenv import load_dotenv
import time
from datetime import datetime

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Get from environment
whisper_bin = os.path.expanduser(os.getenv("WHISPER_BIN"))
model_path = os.path.expanduser(os.getenv("MODEL_PATH"))

output_queue = Queue()
stream_process = None

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = whisper.load_model("small")

# output_queue = queue.Queue()
output_queue = Queue()
stream_process = None
stream_thread = None

# WHISPER_CPP_PATH = "/home/iguanya/Projects/whisper.cpp/build/bin/whisper-stream"
# MODEL_PATH = "/home/iguanya/Projects/whisper.cpp/models/ggml-medium.bin"

def run_whisper_stream():
    global stream_process

    # Validate environment variables
    if not os.path.isfile(whisper_bin):
        raise FileNotFoundError(f"whisper_bin not found: {whisper_bin}")
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"model_path not found: {model_path}")

    # Start whisper stream subprocess
    stream_process = subprocess.Popen(
        [whisper_bin, "-m", model_path, "-t", "4", "--step", "500", "--length", "5000", "--language", "auto"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Stream output lines into the queue
    for line in stream_process.stdout:
        output_queue.put(line)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    audio = request.files['audio_data']
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}.webm"
    audio_path = os.path.join(UPLOAD_FOLDER, filename)
    audio.save(audio_path)

    print(f"[INFO] Transcribing {filename}...")
    result = model.transcribe(audio_path)
    transcription = result["text"]
    print(f"[TRANSCRIPTION] {transcription}")

    # Save transcription to a text file
    transcript_filename = f"{timestamp}.txt"
    transcript_path = os.path.join("transcripts", transcript_filename)
    os.makedirs("transcripts", exist_ok=True)

    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcription)

    return jsonify({"transcription": transcription})

@app.route("/stream")
def stream():
    global stream_thread

    # Start the whisper stream thread once
    if stream_thread is None or not stream_thread.is_alive():
        stream_thread = threading.Thread(target=run_whisper_stream, daemon=True)
        stream_thread.start()
        print("[INFO] Whisper stream started.")

    def generate():
        try:
            while True:
                try:
                    line = output_queue.get(timeout=1)
                    print(f"[DEBUG] Whisper Output: {line.strip()}")  # log to terminal
                    yield f"data: {line.strip()}\n\n"
                except Empty:
                    continue  # no output yet
        except GeneratorExit:
            print("[INFO] Client disconnected")

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route('/live')
def live_transcription_page():
    return render_template('stream.html')

if __name__ == '__main__':
    app.run(debug=True)
