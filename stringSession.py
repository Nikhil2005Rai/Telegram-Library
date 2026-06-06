from telethon import TelegramClient
from telethon.sessions import StringSession

api_id=38710207
api_hash="0d1f84b65e2ad492d40059f6b017ec78"

with TelegramClient("sessions/session", api_id, api_hash) as client:
    print(StringSession.save(client.session))