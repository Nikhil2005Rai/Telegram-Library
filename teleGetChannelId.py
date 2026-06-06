from utils import (
    API_ID,
    API_HASH,
    SESSION_STRING,
    SESSION_FILE
)
from telethon import TelegramClient
from telethon.sessions import StringSession


SESSION_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

if SESSION_STRING:
    session = StringSession(SESSION_STRING)
    print("Using SESSION_STRING")
else:
    session = str(SESSION_FILE)
    print("Using local session file")

client = TelegramClient(
        session,
        API_ID,
        API_HASH
    )

async def main():
    async for dialog in client.iter_dialogs():
        print(
            f"Name: {dialog.name}\n"
            f"ID: {dialog.id}\n"
            f"--------------------"
        )


with client:
    client.loop.run_until_complete(main())