import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, send_file
<<<<<<< HEAD
import os
import io
from google.cloud import speech, texttospeech, language_v1
=======
import google.generativeai as genai
>>>>>>> 2b7e12b (project 3 changes)

app = Flask(__name__)

# Get API key from environment variable
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=API_KEY)

# Configure upload folder
UPLOAD_FOLDER = 'uploads/speak'
ALLOWED_EXTENSIONS = {'wav', 'mp3'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file is an allowed audio format."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files(folder, extension, exclude_patterns=None):
<<<<<<< HEAD
    if exclude_patterns is None:
        exclude_patterns = []

    # Get all files with the specified extension while excluding the specified patterns
=======
    """Retrieve files from a folder, sorted by modification time."""
    if exclude_patterns is None:
        exclude_patterns = []
    
>>>>>>> 2b7e12b (project 3 changes)
    files = [filename for filename in os.listdir(folder) 
             if (filename.endswith(extension) or filename.endswith('.txt')) 
             and not any(pattern in filename for pattern in exclude_patterns)]
    
<<<<<<< HEAD
    # Prioritize .wav files to be at the beginning of the list
    wav_files = [f for f in files if f.endswith('.wav')]
    other_files = [f for f in files if not f.endswith('.wav')]
    
    # Combine the lists and sort the combined list in reverse order
    files = wav_files + other_files
    files.sort(reverse=True)
=======
    files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
>>>>>>> 2b7e12b (project 3 changes)
    return files

@app.route('/')
def index():
    """Render index page with list of uploaded audio files."""
    speak_files = get_files(app.config['UPLOAD_FOLDER'], '.wav')
    return render_template('index.html', speak_files=speak_files)

@app.route('/upload_speak', methods=['POST'])
def upload_speak():
    """Handle audio file upload and process it using Gemini AI."""
    if 'audio_data' not in request.files:
        flash('No audio data')
        return redirect(request.url)

    file = request.files['audio_data']
    if file.filename == '' or not allowed_file(file.filename):
        flash('Invalid file selection')
        return redirect(request.url)
<<<<<<< HEAD
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
=======
    
    # Generate filename with timestamp
    filename_base = datetime.now().strftime("%Y%m%d-%I%M%S%p")
    audio_filename = f"{filename_base}.wav"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
    file.save(file_path)
    
    # Process audio with Gemini API
    analysis_result = process_audio_with_gemini(file_path)
    
    # Save analysis result (transcript + sentiment analysis)
    result_filename = f"{filename_base}.txt"
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
    with open(result_path, 'w') as f:
        f.write(analysis_result)
    
    return redirect('/')

@app.route('/uploads/speak/<path:filename>')
>>>>>>> 2b7e12b (project 3 changes)
def speak_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def process_audio_with_gemini(file_path):
    """Send audio file to Gemini API for transcription and sentiment analysis."""
    with open(file_path, "rb") as audio_file:
        audio_data = audio_file.read()
    
    mime_type = "audio/wav" if file_path.endswith('.wav') else "audio/mpeg"
    
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content([
        "Transcribe this audio and analyze its sentiment, providing a score between -1 and 1:",
        {"mime_type": mime_type, "data": audio_data}
    ])
    return response.text if response else "No analysis available"

<<<<<<< HEAD
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

=======
>>>>>>> 2b7e12b (project 3 changes)
@app.route('/script.js', methods=['GET'])
def scripts_js():
    """Serve script.js file."""
    return send_file('./script.js')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
