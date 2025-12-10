import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# --- API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please set it before running the application.")

# --- File Paths ---
SAMPLE_PDFS_DIR = os.path.join(os.path.dirname(__file__), "data", "sample_pdfs")
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
TEMP_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "temp_audio")
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads")
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "app.db")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "data", "docs")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ai_voice_tutor")

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# --- Audio Settings ---
TTS_LANGUAGE = 'en'  # Language for text-to-speech
STT_TIMEOUT = 10  # Timeout for speech recognition in seconds
TTS_SPEED = 1.0  # Speech speed multiplier (1.0 is normal)

# --- PDF Settings ---
CHUNK_SIZE = 800  # Number of characters per text chunk for Gemini context
TESSERACT_CMD = os.getenv("TESSERACT_CMD")
POPPLER_PATH = os.getenv("POPPLER_PATH")
