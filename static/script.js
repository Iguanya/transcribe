let mediaRecorder;
let audioChunks = [];
let isRecording = false;

async function startAutoRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
        const blob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append("audio_data", blob);

        logToScreen("⏳ Sending audio to server for transcription...");

        const res = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        logToScreen("📝 Transcription: " + data.transcription);
        logToScreen("✅ Waiting for next chunk...");
        audioChunks = [];

        // Restart recording
        mediaRecorder.start();
        setTimeout(() => mediaRecorder.stop(), 30000);  // 30 seconds
    };

    mediaRecorder.start();
    setTimeout(() => mediaRecorder.stop(), 30000);  // Initial 30s
    isRecording = true;
    logToScreen("🎙️ Started recording. Transcribing every 30s...");
}

function logToScreen(text) {
    const log = document.getElementById("transcription");
    log.textContent += "\n" + text;
    log.scrollTop = log.scrollHeight;  // auto scroll
}

document.getElementById("recordBtn").addEventListener("click", () => {
    if (!isRecording) {
        startAutoRecording();
        document.getElementById("recordBtn").disabled = true;
        document.getElementById("status").textContent = "Recording in progress...";
    }
});

document.getElementById("uploadForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = document.getElementById("status");
    const form = e.target;
    const formData = new FormData(form);

    status.textContent = "Uploading and transcribing...";
    
    const res = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    document.getElementById("transcription").textContent = data.transcription;
    status.textContent = "Done";
});
