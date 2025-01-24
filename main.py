from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, send_file
import os
import io
from google.cloud import speech, texttospeech
#from pydub.utils import mediainfo

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

def get_files(folder, extension):
    files = []
    for filename in os.listdir(folder):
        if filename.endswith(extension) or filename.endswith('.txt'):
            files.append(filename)
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
        print("FILE NAME IS: ", filename)
        file_path = os.path.join(app.config['SPEAK_FOLDER'], filename)
        print("FILE PATH IS: ", file_path)
        file.save(file_path)
        
        
        # Call speech-to-text API
        #filename = "example.wav"  # Replace with the actual filename you are processing
        file_path = os.path.join(app.config['SPEAK_FOLDER'], filename)
        transcript = speech_to_text(file_path)
        transcript_filename = filename.rsplit('.', 1)[0] + '.txt'
        transcript_path = os.path.join(app.config['SPEAK_FOLDER'], transcript_filename)
        with open(transcript_path, 'w') as f:
            f.write(transcript)
        
    
    return redirect('/')  # success

@app.route('/upload_typing', methods=['POST'])
def upload_typing():
    text = request.form['text']
    print(text)
    
    # Call text-to-speech API
    tts_output_filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
    tts_output_path = os.path.join(app.config['TYPING_FOLDER'], tts_output_filename)
    text_to_speech(text, tts_output_path)
    
    return redirect('/')  # success

@app.route('/uploads/speak/<filename>')
def speak_file(filename):
    return send_from_directory(app.config['SPEAK_FOLDER'], filename)

@app.route('/uploads/typing/<filename>')
def typing_file(filename):
    return send_from_directory(app.config['TYPING_FOLDER'], filename)

def speech_to_text(file_path):
    #print("MEDIA INFO")
    #print(mediainfo(file_path))

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

    if response.results:
        print("SPEECH TO TEXT REPONSE :")
    else:
        print("NO SPEECH TO TEXT REPONSE")
    
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript
    
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

@app.route('/script.js',methods=['GET'])
def scripts_js():
    return send_file('./script.js')

if __name__ == '__main__':
    app.run(debug=True)