import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
base_dir = Path(__file__).resolve().parent
load_dotenv(base_dir / ".env")

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "volunteeriq_secret")
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(base_dir / "volunteeriq.db"))
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")