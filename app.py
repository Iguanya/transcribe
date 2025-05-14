from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import whisper
import subprocess
from threading import Thread
from queue import Queue
# import queue
import os
import time
from datetime import datetime

app = Flask(__name__)
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

    whisper_bin = os.path.expanduser("~/Projects/whisper.cpp/build/bin/whisper-stream")
    model_path = os.path.expanduser("~/Projects/whisper.cpp/models/ggml-medium.bin")

    stream_process = subprocess.Popen(
        [whisper_bin, "-m", model_path, "-t", "4", "--step", "500", "--length", "5000", "--language", "auto"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

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
    def generate():
        try:
            while True:
                # Simulate live transcription
                # You'd replace this with your Whisper.cpp call
                time.sleep(5)
                clean_text = "This is a test transcription."  # Replace with actual output

                # Log raw or noisy data to terminal
                print("[DEBUG] Whisper Output: Full whisper.cpp logs or JSON...")

                # Send only clean text to frontend
                yield f"data: {clean_text.strip()}\n\n"
        except GeneratorExit:
            print("[INFO] Client disconnected")
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route('/live')
def live_transcription_page():
    return render_template('stream.html')

if __name__ == '__main__':
    app.run(debug=True)
