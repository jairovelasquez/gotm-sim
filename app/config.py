import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "gotm.db"
BEDROCK_MODEL = "anthropic.claude-3-haiku-20240307-v1:0"
