

from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = 38710207
api_hash = "0d1f84b65e2ad492d40059f6b017ec78"

BASE_DIR = Path(__file__).resolve().parent

SESSION_FILE = (
    BASE_DIR
    / "sessions"
    / "session"
)

with TelegramClient(
    str(SESSION_FILE),
    api_id,
    api_hash
) as client:
    print(StringSession.save(client.session))