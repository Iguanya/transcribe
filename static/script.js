let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let eventSource = null;

// === Mic Auto Recording ===
async function startAutoRecording() {
  const statusEl = document.getElementById("status");
  const log = document.getElementById("transcription");

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = event => {
      audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      const formData = new FormData();
      formData.append("audio_data", blob);

      logToScreen("⏳ Sending audio to server for transcription...", log);

      try {
        const res = await fetch("/upload", {
          method: "POST",
          body: formData
        });

        const data = await res.json();
        logToScreen("📝 Transcription: " + (data.transcription || data.error), log);
        logToScreen("✅ Waiting for next chunk...", log);
      } catch (err) {
        logToScreen("❌ Error sending audio.", log);
      }

      audioChunks = [];
      mediaRecorder.start();
      setTimeout(() => mediaRecorder.stop(), 30000); // Record next chunk
    };

    mediaRecorder.start();
    setTimeout(() => mediaRecorder.stop(), 30000);
    isRecording = true;
    if (statusEl) statusEl.textContent = "Recording in progress...";
    logToScreen("🎙️ Started recording. Transcribing every 30s...", log);
  } catch (err) {
    logToScreen("❌ Could not access microphone.", log);
    console.error(err);
  }
}

function logToScreen(text, element) {
  if (element) {
    element.textContent += "\n" + text;
    element.scrollTop = element.scrollHeight;
  }
}

// === File Upload Transcription ===
const uploadForm = document.getElementById("uploadForm");
if (uploadForm) {
  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = document.getElementById("status");
    const transcription = document.getElementById("fileTranscription") || document.getElementById("transcription");
    const formData = new FormData(uploadForm);

    if (status) status.textContent = "Uploading and transcribing...";
    transcription.textContent = "";

    try {
      const res = await fetch("/upload", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      transcription.textContent = data.transcription || `❌ ${data.error}`;
    } catch (err) {
      transcription.textContent = "❌ Failed to upload audio.";
    }

    if (status) status.textContent = "Done";
  });
}

// === Live Transcription Stream ===
const startStreamBtn = document.getElementById("startStream");
const stopBtn = document.getElementById("stopBtn");
const liveOutput = document.getElementById("transcription");

if (startStreamBtn && liveOutput) {
  startStreamBtn.addEventListener("click", () => {
    if (eventSource) eventSource.close();

    eventSource = new EventSource("/stream");
    liveOutput.textContent = "🔴 Live transcription started...\n";

    eventSource.onmessage = (event) => {
      liveOutput.textContent += event.data + "\n";
      liveOutput.scrollTop = liveOutput.scrollHeight;
    };

    eventSource.onerror = (err) => {
      liveOutput.textContent += "\n❌ Lost connection to server.";
      eventSource.close();
    };

    if (stopBtn) stopBtn.disabled = false;
    startStreamBtn.disabled = true;
  });

  if (stopBtn) {
    stopBtn.addEventListener("click", () => {
      if (eventSource) {
        eventSource.close();
        eventSource = null;
        liveOutput.textContent += "\n⏹️ Transcription stopped.";
      }

      startStreamBtn.disabled = false;
      stopBtn.disabled = true;
    });
  }
}

// === Mic Record Button ===
const recordBtn = document.getElementById("recordBtn");
if (recordBtn) {
  recordBtn.addEventListener("click", () => {
    if (!isRecording) {
      startAutoRecording();
      recordBtn.disabled = true;
    }
  });
}

// === Sidebar Toggle ===
document.addEventListener("DOMContentLoaded", function () {
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.querySelector(".sidebar");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", function () {
      sidebar.classList.toggle("collapsed");
      localStorage.setItem(
        "sidebarCollapsed",
        sidebar.classList.contains("collapsed")
      );
    });
    if (localStorage.getItem("sidebarCollapsed") === "true") {
      sidebar.classList.add("collapsed");
    }
  }
});

// === Dropdown Toggle ===
document.addEventListener("DOMContentLoaded", () => {
  const getStartedBtn = document.getElementById("getStartedBtn");
  const optionsMenu = document.getElementById("transcribeOptions");

  if (getStartedBtn && optionsMenu) {
    getStartedBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      optionsMenu.classList.toggle("dropdown-hidden");
    });

    document.addEventListener("click", (event) => {
      if (!optionsMenu.contains(event.target) && event.target !== getStartedBtn) {
        optionsMenu.classList.add("dropdown-hidden");
      }
    });
  }
});
