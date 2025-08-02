import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEYS = os.getenv("GEMINI_API_KEYS", "").split(",")
AUTH_KEY = os.getenv("AUTH_KEY")
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", 10))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
PORT = int(os.getenv("PORT", 8000))
UPSTREAM_URL = os.getenv("UPSTREAM_URL", "https://generativelanguage.googleapis.com")
REPORTING_PATH = os.getenv("REPORTING_PATH", "/status")
