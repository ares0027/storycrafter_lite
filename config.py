import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent
PROJECTS_DIR = BASE_DIR / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

# Database
DB_PATH = BASE_DIR / "storycrafter.db"

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lmstudio")  # lmstudio, ollama, gemini
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
LLM_PORT = int(os.getenv("LLM_PORT", "1234"))
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen-3.6-35b")

# Extraction Configuration
WORDS_TO_EXTRACT = int(os.getenv("WORDS_TO_EXTRACT", "1000"))
EXTRACTOR_SYSTEM_PROMPT = os.getenv("EXTRACTOR_SYSTEM_PROMPT", "You are an expert editor and librarian. Your task is twofold:\n1. Fix any OCR errors in the provided text. Return the corrected text.\n2. Extract book metadata from the text (Title, Author, Details, Genre, Style, Target Audience, Publish Date, Original Language, Provided Language, Is Translation (boolean), Translator).\n\nOutput strictly in JSON format as follows:\n{\n    \"corrected_text\": \"...\",\n    \"metadata\": {\n        \"title\": \"...\",\n        \"author\": \"...\",\n        \"details\": \"...\",\n        \"genre\": \"...\",\n        \"style\": \"...\",\n        \"target_audience\": \"...\",\n        \"publish_date\": \"...\",\n        \"original_language\": \"...\",\n        \"provided_language\": \"...\",\n        \"is_translation\": true/false,\n        \"translator\": \"...\"\n    }\n}\n")

OCR_CHUNK_WORDS = int(os.getenv("OCR_CHUNK_WORDS", "2000"))
OCR_OVERLAP_WORDS = int(os.getenv("OCR_OVERLAP_WORDS", "50"))

# Web Server
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# To easily update configuration on the fly during runtime
def update_config(key: str, value: any):
    from dotenv import set_key
    globals()[key] = value
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        env_file.touch()
    set_key(str(env_file), key, str(value))
