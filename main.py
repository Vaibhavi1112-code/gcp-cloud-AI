from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, send_file
import os
import io
from google.cloud import speech, texttospeech, language_v1

app = Flask(__name__)

# Configure upload folders
BASE_UPLOAD_FOLDER = 'uploads'
SPEAK_FOLDER = os.path.join(BASE_UPLOAD_FOLDER, 'speak')
TYPING_FOLDER = os.path.join(BASE_UPLOAD_FOLDER, 'typing')
ALLOWED_EXTENSIONS = {'wav', 'mp3'}
app.config['SPEAK_FOLDER'] = SPEAK_FOLDER
app.config['TYPING_FOLDER'] = TYPING_FOLDER

os.makedirs(SPEAK_FOLDER, exist_ok=True)
os.makedirs(TYPING_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files(folder, extension, exclude_patterns=None):
    if exclude_patterns is None:
        exclude_patterns = []

    # Get all files with the specified extension while excluding the specified patterns
    files = [filename for filename in os.listdir(folder) 
             if (filename.endswith(extension) or filename.endswith('.txt')) 
             and not any(pattern in filename for pattern in exclude_patterns)]
    
    # Prioritize .wav files to be at the beginning of the list
    wav_files = [f for f in files if f.endswith('.wav')]
    other_files = [f for f in files if not f.endswith('.wav')]
    
    # Combine the lists and sort the combined list in reverse order
    files = wav_files + other_files
    files.sort(reverse=True)
    return files

@app.route('/')
def index():
    speak_files = get_files(app.config['SPEAK_FOLDER'], '.wav')
    typing_files = get_files(app.config['TYPING_FOLDER'], '.wav')
    return render_template('index.html', speak_files=speak_files, typing_files=typing_files)

@app.route('/upload_speak', methods=['POST'])
def upload_speak():
    if 'audio_data' not in request.files:
        flash('No audio data')
        return redirect(request.url)
    file = request.files['audio_data']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['SPEAK_FOLDER'], filename)
        file.save(file_path)

        # Call speech-to-text API
        transcript = speech_to_text(file_path)
        transcript_filename = filename.rsplit('.', 1)[0] + '.txt'
        transcript_path = os.path.join(app.config['SPEAK_FOLDER'], transcript_filename)
        with open(transcript_path, 'w') as f:
            f.write(transcript)

        # Perform sentiment analysis
        sentiment, score = analyze_sentiment(transcript)
        sentiment_filename = filename.rsplit('.', 1)[0] + '_sentiment.txt'
        sentiment_path = os.path.join(app.config['SPEAK_FOLDER'], sentiment_filename)

        # Save sentiment result
        with open(sentiment_path, 'w') as f:
            f.write(f"Original Text: {transcript}\nSentiment: {sentiment} (Score: {score})")

    return redirect('/')  # success

@app.route('/upload_typing', methods=['POST'])
def upload_typing():
    text = request.form['text']
    
    # Generate filenames
    timestamp = datetime.now().strftime("%Y%m%d-%I%M%S%p")
    tts_output_filename = f"{timestamp}.wav"  # Filename for the TTS output
    text_filename = f"{timestamp}.txt"
    sentiment_filename = f"{timestamp}_sentiment.txt"

    # Paths for saving files
    tts_output_path = os.path.join(app.config['TYPING_FOLDER'], tts_output_filename)
    text_path = os.path.join(app.config['TYPING_FOLDER'], text_filename)
    sentiment_path = os.path.join(app.config['TYPING_FOLDER'], sentiment_filename)

    # Save text to file
    with open(text_path, "w") as text_file:
        text_file.write(text)

    # Perform sentiment analysis
    sentiment, score = analyze_sentiment(text)

    # Save sentiment result
    with open(sentiment_path, "w") as sentiment_file:
        sentiment_file.write(f"Original Text: {text}\nSentiment: {sentiment} (Score: {score})")

    # Call text-to-speech API to generate audio file
    text_to_speech(text, tts_output_path)

    return redirect('/')  # success

@app.route('/uploads/speak/<filename>')
def speak_file(filename):
    return send_from_directory(app.config['SPEAK_FOLDER'], filename)

@app.route('/uploads/typing/<filename>')
def typing_file(filename):
    return send_from_directory(app.config['TYPING_FOLDER'], filename)

def speech_to_text(file_path):
    client = speech.SpeechClient()
    with io.open(file_path, "rb") as audio_file:
        content = audio_file.read()
    
    if not content:
        print("No content in the audio file.")
    
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        language_code="en-US",
        sample_rate_hertz=48000
    )
    
    response = client.recognize(config=config, audio=audio)
    transcript = "".join(result.alternatives[0].transcript for result in response.results)
    
    return transcript

def text_to_speech(text, output_path):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    with open(output_path, "wb") as out:
        out.write(response.audio_content)

def analyze_sentiment(text):
    """Analyze sentiment of the given text using Google Cloud Natural Language API."""
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)

    response = client.analyze_sentiment(request={"document": document})
    sentiment_score = response.document_sentiment.score

    # Determine sentiment category
    sentiment = "Positive" if sentiment_score > 0.2 else "Negative" if sentiment_score < -0.2 else "Neutral"
    
    return sentiment, sentiment_score

@app.route('/script.js', methods=['GET'])
def scripts_js():
    return send_file('./script.js')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
