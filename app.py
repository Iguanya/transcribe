from flask import Flask, render_template, request, jsonify
import os
import whisper
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = whisper.load_model("small")

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

if __name__ == '__main__':
    app.run(debug=True)
