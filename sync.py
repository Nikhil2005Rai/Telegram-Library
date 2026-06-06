from utils import (
    load_config,
    load_progress,
    save_progress,
    SESSION_FILE,
    API_ID,
    API_HASH,
    SESSION_STRING
)

import asyncio
from telethon import TelegramClient
from telethon.tl.patched import MessageService
from telethon.sessions import StringSession


# ============================================================
# Sync Logic
# ============================================================

async def sync_pair(client, source_id, dest_id, progress):
    source = await client.get_entity(source_id)
    dest = await client.get_entity(dest_id)

    source_key = str(source_id)

    last_id = progress.get(source_key, 0)

    print("\n" + "=" * 70)
    print(f"Source      : {source_id}")
    print(f"Destination : {dest_id}")
    print(f"Last Synced : {last_id}")
    print("=" * 70)

    messages = []

    async for msg in client.iter_messages(
        source,
        min_id=last_id
    ):
        messages.append(msg)

    if not messages:
        print("No new messages found.")
        return

    messages.reverse()

    total = len(messages)

    print(f"Found {total} new messages")

    for index, msg in enumerate(messages, start=1):

        try:
            # Skip Telegram service messages
            if isinstance(msg, MessageService):
                progress[source_key] = msg.id

                if index % 10 == 0:
                    save_progress(progress)

                continue

            await client.forward_messages(
                dest,
                msg
            )

            progress[source_key] = msg.id

            # Save every 10 messages
            if index % 10 == 0:
                save_progress(progress)

            print(
                f"[{index}/{total}] Forwarded Message ID: {msg.id}"
            )

            # Helps avoid Telegram flood limits
            await asyncio.sleep(0.2)

        except Exception as e:
            print(
                f"[{index}/{total}] Failed Message ID: {msg.id}"
            )
            print(f"Reason: {e}")

    # Final save
    save_progress(progress)

    print("\nPair Complete!")
    print(
        f"Latest Synced ID: {progress[source_key]}"
    )


# ============================================================
# Main
# ============================================================

async def main():
    config = load_config()

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

    await client.start()

    progress = load_progress()

    try:
        for pair in config["pairs"]:

            if not pair.get("enabled", True):
                continue

            await sync_pair(
                client,
                pair["source"],
                pair["destination"],
                progress
            )

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())