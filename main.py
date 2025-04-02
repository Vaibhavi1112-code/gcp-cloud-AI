import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, send_file
import google.generativeai as genai

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
    """Retrieve files from a folder, sorted by modification time."""
    if exclude_patterns is None:
        exclude_patterns = []
    
    files = [filename for filename in os.listdir(folder) 
             if (filename.endswith(extension) or filename.endswith('.txt')) 
             and not any(pattern in filename for pattern in exclude_patterns)]
    
    files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
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

@app.route('/script.js', methods=['GET'])
def scripts_js():
    """Serve script.js file."""
    return send_file('./script.js')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
