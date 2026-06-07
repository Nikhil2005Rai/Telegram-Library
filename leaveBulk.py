import asyncio

from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.functions.channels import LeaveChannelRequest

from utils import (
    SESSION_FILE,
    API_ID,
    API_HASH,
    SESSION_STRING,
)

FOLDER_NAME = "Onlyfans"


async def main():
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

    session = SESSION_STRING if SESSION_STRING else str(SESSION_FILE)

    client = TelegramClient(session, API_ID, API_HASH)

    await client.start()

    try:
        result = await client(GetDialogFiltersRequest())

        target_folder = None

        for folder in result.filters:
            title = getattr(folder, "title", None)

            if hasattr(title, "text"):
                title = title.text

            if title == FOLDER_NAME:
                target_folder = folder
                break

        if target_folder is None:
            print(f'Folder "{FOLDER_NAME}" not found')
            return

        peers = getattr(target_folder, "include_peers", [])

        print(f"Found {len(peers)} channels")

        left = 0
        failed = 0

        for peer in peers:
            try:
                entity = await client.get_entity(peer)

                name = getattr(entity, "title", str(entity))

                print(f"Leaving: {name}")

                await client(LeaveChannelRequest(entity))

                left += 1

                await asyncio.sleep(1)

            except Exception as e:
                failed += 1
                print(f"Failed: {e}")

        print("\nDone")
        print(f"Left: {left}")
        print(f"Failed: {failed}")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())