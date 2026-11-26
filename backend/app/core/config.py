"""Application settings, read from the .env file."""

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://reconx:reconx@localhost:5432/reconx")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
