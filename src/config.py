import os
from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Native pure-Python .env reader (zero external dependency required)
def load_env_file(env_path: Path):
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("\"'")
                    if key not in os.environ:
                        os.environ[key] = val

load_env_file(BASE_DIR / ".env")

# Google Gemini API Configuration
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY", ""
)

# Gmail SMTP Configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "enggdilipkirar@gmail.com")
RAW_APP_PASSWORD = os.getenv("APP_PASSWORD", "")

# Remove spaces from Gmail App Password for SMTP authentication
APP_PASSWORD = RAW_APP_PASSWORD.replace(" ", "").strip()

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("DEFAULT_PORT", "7861"))

# Data File Paths
DATA_DIR = BASE_DIR / "data"
JSON_FILE = DATA_DIR / "seminars_data.json"
CSV_FILE = DATA_DIR / "seminars_data.csv"
