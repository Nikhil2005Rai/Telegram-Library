import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE = BASE_DIR / "config.json"
PROGRESS_FILE = BASE_DIR / "progress.json"
SESSION_FILE = BASE_DIR / "sessions" / "session"

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# ============================================================
# Config Helpers
# ============================================================

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# ============================================================
# Progress Helpers
# ============================================================

def load_progress():
    if not PROGRESS_FILE.exists():
        return {}

    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)