import os
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Load environment variables from .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set in .env")

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)

# Base directory
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
CORS(app)  # allow frontend (Lovable) to call this API

# Simple health check route
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


def save_uploaded_file(file_storage) -> str:
    """
    Save the uploaded audio file to disk and return the file path.
    """
    # Generate a safe, unique filename
    ext = Path(file_storage.filename).suffix or ".mp3"
    filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / filename
    file_storage.save(file_path)
    return str(file_path)


def transcribe_audio_with_openai(file_path: str) -> str:
    """
    Use OpenAI Whisper-style model to transcribe audio.
    """
    try:
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",  # adjust if OpenAI uses a different exact name
                file=audio_file,
                response_format="text"
            )
        # transcription is plain text
        return transcription
    except Exception as e:
        print("Error during STT:", e)
        raise


@app.route("/stt", methods=["POST"])
def stt():
    """
    Speech-to-Text endpoint.
    v1: accept file upload, save it, and return a dummy transcript.
    Later: call real STT service here.
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided. Use form field name 'audio'."}), 400

    audio_file = request.files["audio"]

    if audio_file.filename == "":
        return jsonify({"error": "Empty file name."}), 400

    # Optional: basic file type check
    allowed_ext = {".mp3", ".wav", ".m4a", ".m4b"}
    ext = Path(audio_file.filename).suffix.lower()
    if ext not in allowed_ext:
        return jsonify({"error": f"Unsupported file type {ext}. Allowed: {', '.join(allowed_ext)}"}), 400

    # Save file
    file_path = save_uploaded_file(audio_file)

    # Call STT
    try:
        transcript = transcribe_audio_with_openai(file_path)
    except Exception:
        return jsonify({"error": "Failed to transcribe audio with STT service."}), 500

    return jsonify({
        "status": "success",
        "file_name": Path(file_path).name,
        "transcript": transcript
    }), 200

def summarize_text_with_openai(text: str, summary_type: str = "short") -> str:
    """
    Use OpenAI LLM to summarize text.
    summary_type: "short", "medium", "detailed"
    """
    if summary_type not in {"short", "medium", "detailed"}:
        summary_type = "short"

    style_instruction = {
        "short": "Provide a concise executive summary in 3–5 sentences.",
        "medium": "Provide a detailed summary in 6–10 sentences highlighting main ideas and key points.",
        "detailed": "Provide a comprehensive summary with clear structure and bullet points where useful."
    }[summary_type]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # use a cheap, capable model
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert summarizer of long audiobook transcripts."
                },
                {
                    "role": "user",
                    "content": f"{style_instruction}\n\nText to summarize:\n{text}"
                }
            ],
            temperature=0.3
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print("Error during summarization:", e)
        raise


@app.route("/summarize", methods=["POST"])
def summarize():
    """
    Summarization endpoint.
    v1: accept text, and return a dummy summary.
    Later: call real LLM service here.
    """
    data = request.get_json()

    if not data or "text" not in data:
        return jsonify({"error": "No text provided for summarization."}), 400

    text_to_summarize = data["text"]
    summary_type = data.get("summary_type", "short") # Default to 'short' if not provided

    if not isinstance(text_to_summarize, str) or not text_to_summarize.strip():
        return jsonify({"error": "Invalid or empty text provided for summarization."}), 400

    # Call summarization
    try:
        summary = summarize_text_with_openai(text_to_summarize, summary_type)
    except Exception:
        return jsonify({"error": "Failed to summarize text with LLM service."}), 500

    return jsonify({
        "status": "success",
        "summary": summary,
        "summary_type": summary_type
    }), 200

def generate_audio_with_openai(text: str) -> str:
    """
    Use OpenAI TTS to generate audio from text.
    Saves an MP3 file and returns its path.
    """
    audio_filename = f"summary_audio_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}.mp3"
    audio_filepath = UPLOAD_DIR / audio_filename

    try:
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",  # adjust to correct TTS model name per docs
            voice="alloy",
            input=text
        )

        # response.read() gives binary audio data
        audio_bytes = response.read()
        with open(audio_filepath, "wb") as f:
            f.write(audio_bytes)

        print(f"TTS audio file created at: {audio_filepath}")
        return str(audio_filepath)
    except Exception as e:
        print("Error during TTS:", e)
        raise


@app.route("/tts", methods=["POST"])
def tts():
    """
    Text-to-Speech endpoint.
    v1: accept text, and return a dummy audio file.
    Later: call real TTS service here.
    """
    data = request.get_json()

    if not data or "text" not in data:
        return jsonify({"error": "No text provided for audio generation."}), 400

    text_to_convert = data["text"]

    if not isinstance(text_to_convert, str) or not text_to_convert.strip():
        return jsonify({"error": "Invalid or empty text provided for audio generation."}), 400

    # Call audio generation
    try:
        audio_filepath = generate_audio_with_openai(text_to_convert)
    except Exception:
        return jsonify({"error": "Failed to generate audio with TTS service."}), 500

    # In a real scenario, you stream the audio or return a URL to it.
    return jsonify({
        "status": "success",
        "message": "Audio generated.",
        "audio_file_name": Path(audio_filepath).name,
        "audio_file_path": str(audio_filepath) # This path is local to the server
    }), 200

@app.route("/uploads/<filename>", methods=["GET"])
def serve_audio(filename):
    """Serve uploaded/generated audio files"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404
    return send_file(file_path, mimetype="audio/mpeg")


def create_pdf_from_text(text: str) -> str:
    """
    Create a simple PDF file from the given text and return its file path.
    """
    pdf_filename = f"summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}.pdf"
    pdf_path = UPLOAD_DIR / pdf_filename

    # Basic PDF generation with word wrapping
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    # Simple margins
    margin_left = 50
    margin_top = height - 50
    line_height = 14

    # Split text into lines that fit the page width
    # Very simple wrap: split on newline first, then wrap long lines
    import textwrap
    max_chars_per_line = 90  # approximate characters per line

    y = margin_top
    for paragraph in text.split("\n"):
        lines = textwrap.wrap(paragraph, max_chars_per_line) or [""]
        for line in lines:
            if y < 50:  # new page if we're near the bottom
                c.showPage()
                y = margin_top
            c.drawString(margin_left, y, line)
            y -= line_height

    c.save()
    return str(pdf_path)

@app.route("/export_summary_pdf", methods=["POST"])
def export_summary_pdf():
    """
    Accepts summary text and returns a generated PDF file for download.
    Does NOT modify existing /stt, /summarize, /tts functionality.
    """
    data = request.get_json()

    if not data or "summary_text" not in data:
        return jsonify({"error": "No summary_text provided."}), 400

    summary_text = data["summary_text"]
    if not isinstance(summary_text, str) or not summary_text.strip():
        return jsonify({"error": "Invalid or empty summary_text."}), 400

    try:
        pdf_path = create_pdf_from_text(summary_text)
    except Exception as e:
        print("Error creating PDF:", e)
        return jsonify({"error": "Failed to generate PDF."}), 500

    # Return the file as a download
    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=Path(pdf_path).name,
    )

if __name__ == "__main__":
    # Development server
    app.run(host="127.0.0.1", port=5000, debug=True)    