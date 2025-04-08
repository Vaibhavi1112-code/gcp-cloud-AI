import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, send_from_directory, flash
import google.generativeai as genai
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
from google.cloud import texttospeech

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# API Keys
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=API_KEY)

# Upload folders
UPLOAD_AUDIO = 'uploads/speak'
UPLOAD_PDF = 'uploads/pdf'
os.makedirs(UPLOAD_AUDIO, exist_ok=True)
os.makedirs(UPLOAD_PDF, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_AUDIO
app.config['PDF_FOLDER'] = UPLOAD_PDF

ALLOWED_AUDIO_EXT = {'wav', 'mp3'}
ALLOWED_PDF_EXT = {'pdf'}

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

def get_files(folder, extension, exclude_patterns=None):
    if exclude_patterns is None:
        exclude_patterns = []
    files = [filename for filename in os.listdir(folder)
             if filename.endswith(extension)
             and not any(pattern in filename for pattern in exclude_patterns)]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
    return files

@app.route('/')
def index():
    speak_files = get_files(app.config['UPLOAD_FOLDER'], '.wav')
    text_files = get_files(app.config['UPLOAD_FOLDER'], '.txt')
    pdf_files = get_files(app.config['PDF_FOLDER'], '.pdf')
    return render_template('index.html',
                           speak_files=speak_files,
                           text_files=text_files,
                           pdf_files=pdf_files)

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    print("📥 Received POST to /upload_pdf")

    if 'pdf_file' not in request.files:
        print("❌ No file part in request")
        flash('No PDF file uploaded.')
        return redirect('/')

    file = request.files['pdf_file']
    print("📎 Uploaded filename:", file.filename)

    if file.filename == '':
        print("❌ Filename is empty")
        flash('No selected file.')
        return redirect('/')

    if not allowed_file(file.filename, ALLOWED_PDF_EXT):
        print("❌ File extension not allowed")
        flash('Invalid PDF file.')
        return redirect('/')

    filename = secure_filename(file.filename)
    pdf_path = os.path.join(app.config['PDF_FOLDER'], filename)
    print("✅ Saving PDF to:", pdf_path)

    file.save(pdf_path)

    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
    except Exception as e:
        print("❌ Error extracting PDF text:", e)
        flash("Error processing PDF.")
        return redirect('/')

    book_txt_path = os.path.join(app.config['PDF_FOLDER'], "book.txt")
    with open(book_txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    print("✅ Text extracted and saved to:", book_txt_path)

    flash('✅ PDF uploaded and book content extracted.')
    return redirect('/')

@app.route('/upload_speak', methods=['POST'])
def upload_speak():
    if 'audio_data' not in request.files:
        flash('No audio data')
        return redirect(request.url)

    file = request.files['audio_data']
    if file.filename == '' or not allowed_file(file.filename, ALLOWED_AUDIO_EXT):
        flash('Invalid file selection')
        return redirect(request.url)

    filename_base = datetime.now().strftime("%Y%m%d-%I%M%S%p")
    audio_filename = f"{filename_base}.wav"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
    file.save(file_path)

    response_text = process_audio_with_gemini(file_path)

    result_filename = f"{filename_base}.txt"
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write(response_text)

    tts_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename_base}_reply.mp3")
    synthesize_and_save_audio(response_text, tts_path)

    return '', 200

@app.route('/uploads/speak/<path:filename>')
def speak_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/uploads/pdf/<path:filename>')
def pdf_file(filename):
    return send_from_directory(app.config['PDF_FOLDER'], filename)

def process_audio_with_gemini(file_path):
    with open(file_path, "rb") as audio_file:
        audio_data = audio_file.read()

    mime_type = "audio/wav" if file_path.endswith('.wav') else "audio/mpeg"

    try:
        with open(os.path.join(app.config['PDF_FOLDER'], "book.txt"), "r", encoding="utf-8") as f:
            book_text = f.read()
    except FileNotFoundError:
        return "Please upload a book first."

    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    prompt = [
        "Here's the book content. The user will ask a question based on it:",
        {"text": book_text[:8000]},
        "Now transcribe the audio question and answer it clearly:",
        {"mime_type": mime_type, "data": audio_data}
    ]

    response = model.generate_content(prompt)
    return response.text if response else "No response from model."

def synthesize_and_save_audio(text, output_path):
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
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    with open(output_path, "wb") as out:
        out.write(response.audio_content)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
