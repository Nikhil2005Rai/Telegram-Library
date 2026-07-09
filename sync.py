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
import random

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.patched import MessageService
from telethon.errors import FloodWaitError


BATCH_SIZE = 50
MIN_DELAY = 3
MAX_DELAY = 5


# ============================================================
# Sync Logic
# ============================================================

async def sync_pair(client, source_id, dest_id, progress):
    try:
        source = await client.get_entity(source_id)
        dest = await client.get_entity(dest_id)
    except Exception as e:
        print(
            f"Skipping pair {source_id} -> {dest_id}: {e}"
        )
        return

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

    forwardable = []

    for msg in messages:

        if isinstance(msg, MessageService):

            progress[source_key] = msg.id

            continue

        forwardable.append(msg)

    total = len(forwardable)

    if total == 0:
        save_progress(progress)
        print("Only service messages found.")
        return

    print(f"Found {total} new messages")

    for start in range(
        0,
        total,
        BATCH_SIZE
    ):

        batch = forwardable[
            start:start + BATCH_SIZE
        ]

        while True:

            try:

                await client.forward_messages(
                    dest,
                    batch
                )

                progress[source_key] = (
                    batch[-1].id
                )

                save_progress(progress)

                current = min(
                    start + len(batch),
                    total
                )

                print(
                    f"[{current}/{total}] "
                    f"Forwarded batch of "
                    f"{len(batch)} messages"
                )

                await asyncio.sleep(
                    random.uniform(
                        MIN_DELAY,
                        MAX_DELAY
                    )
                )

                break

            except FloodWaitError as e:

                wait_time = e.seconds + 10

                print(
                    "\nFloodWait detected"
                )
                print(
                    f"Sleeping for "
                    f"{wait_time} seconds..."
                )

                save_progress(progress)

                await asyncio.sleep(
                    wait_time
                )

            except Exception as e:

                print(
                    "\nBatch failed."
                )
                print(f"Reason: {e}")

                print(
                    "Retrying in 15 seconds..."
                )

                await asyncio.sleep(15)

    save_progress(progress)

    print("\nPair Complete!")
    print(
        f"Latest Synced ID: "
        f"{progress[source_key]}"
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

        session = StringSession(
            SESSION_STRING
        )

        print(
            "Using SESSION_STRING"
        )

    else:

        session = str(
            SESSION_FILE
        )

        print(
            "Using local session file"
        )

    client = TelegramClient(
        session,
        API_ID,
        API_HASH
    )

    await client.start()

    progress = load_progress()

    try:

        for pair in config["pairs"]:

            if not pair.get(
                "enabled",
                True
            ):
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