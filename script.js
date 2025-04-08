let mediaRecorder;
let audioChunks = [];

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  audioChunks = [];

  mediaRecorder.ondataavailable = event => {
    if (event.data.size > 0) {
      audioChunks.push(event.data);
    }
  };

  mediaRecorder.onstop = () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append("audio_data", audioBlob, "recorded_audio.wav");

    fetch("/upload_speak", {
      method: "POST",
      body: formData
    }).then(() => {
      document.getElementById("status").innerText = "Uploaded!";
      window.location.reload();  // Refresh the page to show the new result
    });
  };

  mediaRecorder.start();
  document.getElementById("status").innerText = "Recording... 🎤";
}

function stopRecording() {
  mediaRecorder.stop();
  document.getElementById("status").innerText = "Recording stopped. Uploading...";
}
