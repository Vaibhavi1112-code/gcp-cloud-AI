const recordButtonSpeak = document.getElementById('recordSpeak');
const stopButtonSpeak = document.getElementById('stopSpeak');
const audioElementSpeak = document.getElementById('audioSpeak');
const audioDataInputSpeak = document.getElementById('audioDataSpeak');
const timerDisplaySpeak = document.getElementById('timerSpeak');

let mediaRecorder;
let audioChunks = [];
let startTime;
let timerInterval;

function formatTime(time) {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

recordButtonSpeak.addEventListener('click', () => {
    console.log("Record button clicked");
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            console.log("Recording started");

            startTime = Date.now();
            timerInterval = setInterval(() => {
                const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
                timerDisplaySpeak.textContent = formatTime(elapsedTime);
            }, 1000);

            mediaRecorder.ondataavailable = e => {
                audioChunks.push(e.data);
            };

            mediaRecorder.onstop = () => {
                console.log("Recording stopped");
                clearInterval(timerInterval);
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const audioUrl = URL.createObjectURL(audioBlob);
                audioElementSpeak.src = audioUrl;

                const formData = new FormData();
                formData.append('audio_data', audioBlob, 'recorded_audio.wav');

                // Upload the recorded audio
                fetch('/upload_speak', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    console.log("Audio uploaded successfully");
                    location.reload(); // Force refresh

                    return response.text();
                })
                .then(data => {
                    console.log('Audio uploaded successfully:', data);
                })
                .catch(error => {
                    console.error('Error uploading audio:', error);
                });
            };
        })
        .catch(error => {
            console.error('Error accessing microphone:', error);
        });

    recordButtonSpeak.disabled = true;
    stopButtonSpeak.disabled = false;
});

stopButtonSpeak.addEventListener('click', () => {
    console.log("Stop button clicked");
    if (mediaRecorder) {
        mediaRecorder.stop();
    }

    recordButtonSpeak.disabled = false;
    stopButtonSpeak.disabled = true;
});

// Initially disable the stop button
stopButtonSpeak.disabled = true;