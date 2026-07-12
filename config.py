# ============================================================
# config.py — MediAssist App Configuration
# All tuneable settings live here. Change values as needed.
# ============================================================

import os

# ---- Ollama / AI Model ----
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "mediassist-finetuned")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

# ---- Dataset ----
DATASET_FILE = os.getenv("DATASET_FILE", "data/Final_Medicine_Dataset.json")

# ---- Flask ----
DEBUG = os.getenv("FLASK_DEBUG", "1").lower() in {"1", "true", "yes", "on"}
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
SECRET_KEY = os.getenv("SECRET_KEY", "mediassist-secret-key-change-in-production")
MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_SIZE_MB", "16")) * 1024 * 1024
UPLOAD_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}

# ---- Google OAuth Credentials ----
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Explicit base URL used to build OAuth redirect_uri.
# Example: http://127.0.0.1:5000 or https://yourdomain.com
GOOGLE_REDIRECT_BASE_URL = os.getenv("GOOGLE_REDIRECT_BASE_URL", "")


