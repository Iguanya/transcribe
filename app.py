from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import whisper
import subprocess
from threading import Thread
import threading
from queue import Queue, Empty
# import queue
import tempfile
import os
from dotenv import load_dotenv
import time
from datetime import datetime

# from dummymodel import DummyModel

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Get from environment
whisper_bin = os.path.expanduser(os.getenv("WHISPER_BIN"))
model_path = os.path.expanduser(os.getenv("MODEL_PATH"))

# whisper_bin = ''
# model_path = ''

output_queue = Queue()
stream_process = None

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = whisper.load_model("small")

# model = DummyModel("small")

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

@app.route("/upload_audio")
def upload_audio():
    return render_template("upload_audio.html")  # Ensure this exists

@app.route("/upload", methods=["POST"])
def upload():
    if "audio_data" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    file = request.files["audio_data"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        file.save(tmp.name)
        temp_path = tmp.name

    try:
        print(f"[INFO] Transcribing file: {temp_path}")
        result = model.transcribe(temp_path)
        transcription = result["text"]
    except Exception as e:
        print(f"[ERROR] Transcription failed: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(temp_path)

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
    app.run(debug=True, host="0.0.0.0", port=5000)
