"""
Programmatic API facade for telegram-library.

This module is intentionally additive: the existing CLI scripts keep working as
they do today, while future UI/backend code can import this single file instead
of shelling out to prompts.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Awaitable, Callable, Literal

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
PROGRESS_FILE = BASE_DIR / "progress.json"
SESSION_FILE = BASE_DIR / "sessions" / "session"

LogLevel = Literal["info", "success", "warning", "error"]
LogCallback = Callable[[LogLevel, str], None | Awaitable[None]]


class TelegramLibraryError(Exception):
    """Base exception for API facade errors."""


class ConfigError(TelegramLibraryError):
    """Raised when config or environment values are invalid."""


class PairExistsError(TelegramLibraryError):
    """Raised when adding a duplicate source/destination pair."""


class PairNotFoundError(TelegramLibraryError):
    """Raised when an operation targets a missing pair."""


@dataclass(frozen=True)
class ChannelPair:
    source: int
    destination: int
    enabled: bool = True


@dataclass(frozen=True)
class PairState:
    source: int
    destination: int
    enabled: bool
    last_synced_id: int


@dataclass(frozen=True)
class DialogInfo:
    id: int
    name: str
    type: str


@dataclass(frozen=True)
class SessionStatus:
    api_configured: bool
    api_id_configured: bool
    api_hash_configured: bool
    session_mode: str
    session_file: str
    session_file_exists: bool


@dataclass(frozen=True)
class SyncResult:
    source: int
    destination: int
    forwarded: int
    skipped: int
    failed: int
    latest_synced_id: int


@dataclass(frozen=True)
class BulkLeaveResult:
    folder_name: str
    found: int
    left: int
    failed: int


def get_state() -> dict:
    """Return the current local state needed by a UI."""
    return {
        "pairs": [asdict(pair) for pair in list_pair_states()],
        "progress": get_progress(),
        "session": asdict(get_session_status()),
    }


def list_pairs() -> list[ChannelPair]:
    config = _load_config()
    return [_pair_from_dict(pair) for pair in config["pairs"]]


def list_pair_states() -> list[PairState]:
    """Return pairs enriched with their progress.json entry."""
    progress = get_progress()

    return [
        PairState(
            source=pair.source,
            destination=pair.destination,
            enabled=pair.enabled,
            last_synced_id=progress.get(str(pair.source), 0),
        )
        for pair in list_pairs()
    ]


def add_pair(source: int, destination: int, enabled: bool = True) -> ChannelPair:
    config = _load_config()

    if _find_pair_index(config["pairs"], source, destination) is not None:
        raise PairExistsError("Pair already exists.")

    pair = ChannelPair(
        source=int(source),
        destination=int(destination),
        enabled=bool(enabled),
    )
    config["pairs"].append(asdict(pair))
    _save_config(config)

    return pair


def remove_pair(
    source: int,
    destination: int,
    cleanup_progress: bool = False,
) -> ChannelPair:
    config = _load_config()
    index = _find_pair_index(config["pairs"], source, destination)

    if index is None:
        raise PairNotFoundError("Pair not found.")

    removed = _pair_from_dict(config["pairs"].pop(index))
    _save_config(config)

    if cleanup_progress and not _source_exists(config["pairs"], removed.source):
        reset_progress(removed.source)

    return removed


def set_pair_enabled(source: int, destination: int, enabled: bool) -> ChannelPair:
    config = _load_config()
    index = _find_pair_index(config["pairs"], source, destination)

    if index is None:
        raise PairNotFoundError("Pair not found.")

    config["pairs"][index]["enabled"] = bool(enabled)
    _save_config(config)

    return _pair_from_dict(config["pairs"][index])


def toggle_pair(source: int, destination: int) -> ChannelPair:
    config = _load_config()
    index = _find_pair_index(config["pairs"], source, destination)

    if index is None:
        raise PairNotFoundError("Pair not found.")

    current = bool(config["pairs"][index].get("enabled", True))
    config["pairs"][index]["enabled"] = not current
    _save_config(config)

    return _pair_from_dict(config["pairs"][index])


def get_progress() -> dict[str, int]:
    if not PROGRESS_FILE.exists():
        return {}

    data = _read_json(PROGRESS_FILE, {})
    return {str(key): int(value) for key, value in data.items()}


def set_progress(source: int, message_id: int) -> dict[str, int]:
    progress = get_progress()
    progress[str(source)] = int(message_id)
    _save_progress(progress)

    return progress


def update_progress(updates: dict[int | str, int]) -> dict[str, int]:
    """Merge multiple source/message-id updates into progress.json."""
    progress = get_progress()

    for source, message_id in updates.items():
        progress[str(source)] = int(message_id)

    _save_progress(progress)

    return progress


def reset_progress(source: int | None = None) -> dict[str, int]:
    progress = get_progress()

    if source is None:
        progress = {}
    else:
        progress.pop(str(source), None)

    _save_progress(progress)

    return progress


def prune_progress() -> dict[str, int]:
    """Remove progress entries whose source no longer exists in config.json."""
    configured_sources = {str(pair.source) for pair in list_pairs()}
    progress = {
        source: message_id
        for source, message_id in get_progress().items()
        if source in configured_sources
    }
    _save_progress(progress)

    return progress


def get_session_status() -> SessionStatus:
    load_dotenv(BASE_DIR / ".env")
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    session_string = os.getenv("SESSION_STRING")

    return SessionStatus(
        api_configured=bool(api_id and api_hash),
        api_id_configured=bool(api_id),
        api_hash_configured=bool(api_hash),
        session_mode="string-session" if session_string else "local-file",
        session_file=str(SESSION_FILE),
        session_file_exists=SESSION_FILE.with_suffix(".session").exists()
        or SESSION_FILE.exists(),
    )


async def list_dialogs() -> list[DialogInfo]:
    """Return dialogs visible to the authenticated Telegram account."""
    client = _create_client()

    async with client:
        dialogs: list[DialogInfo] = []

        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            dialog_type = "chat"

            if getattr(entity, "broadcast", False):
                dialog_type = "channel"
            elif getattr(entity, "megagroup", False) or getattr(entity, "gigagroup", False):
                dialog_type = "group"

            dialogs.append(
                DialogInfo(
                    id=int(dialog.id),
                    name=str(dialog.name),
                    type=dialog_type,
                )
            )

        return dialogs


async def sync_enabled_pairs(log: LogCallback | None = None) -> list[SyncResult]:
    """Sync all enabled pairs from config.json."""
    pairs = [pair for pair in list_pairs() if pair.enabled]
    return await sync_pairs(pairs, log=log)


async def sync_pair(
    source: int,
    destination: int,
    log: LogCallback | None = None,
) -> SyncResult:
    """Sync one source/destination pair."""
    results = await sync_pairs(
        [ChannelPair(source=source, destination=destination, enabled=True)],
        log=log,
    )
    return results[0]


async def sync_pairs(
    pairs: list[ChannelPair],
    log: LogCallback | None = None,
) -> list[SyncResult]:
    """Sync the provided pairs using the same progress file as the CLI."""
    client = _create_client()
    progress = get_progress()
    results: list[SyncResult] = []

    async with client:
        for pair in pairs:
            if not pair.enabled:
                continue

            result = await _sync_one_pair(client, pair, progress, log)
            results.append(result)

    return results


async def bulk_leave_folder(
    folder_name: str,
    log: LogCallback | None = None,
) -> BulkLeaveResult:
    """Leave every channel included in a Telegram dialog folder."""
    from telethon.tl.functions.channels import LeaveChannelRequest
    from telethon.tl.functions.messages import GetDialogFiltersRequest

    client = _create_client()

    async with client:
        result = await client(GetDialogFiltersRequest())
        target_folder = None

        for folder in result.filters:
            title = getattr(folder, "title", None)

            if hasattr(title, "text"):
                title = title.text

            if title == folder_name:
                target_folder = folder
                break

        if target_folder is None:
            await _emit(log, "warning", f'Folder "{folder_name}" not found.')
            return BulkLeaveResult(folder_name=folder_name, found=0, left=0, failed=0)

        peers = getattr(target_folder, "include_peers", [])
        found = len(peers)
        left = 0
        failed = 0

        await _emit(log, "info", f'Found {found} channel(s) in "{folder_name}".')

        for peer in peers:
            try:
                entity = await client.get_entity(peer)
                name = getattr(entity, "title", str(entity))

                await _emit(log, "info", f"Leaving: {name}")
                await client(LeaveChannelRequest(entity))

                left += 1
                await asyncio.sleep(1)
            except Exception as exc:  # noqa: BLE001 - reported to API caller.
                failed += 1
                await _emit(log, "error", f"Failed to leave channel: {exc}")

        return BulkLeaveResult(
            folder_name=folder_name,
            found=found,
            left=left,
            failed=failed,
        )


async def _sync_one_pair(
    client,
    pair: ChannelPair,
    progress: dict[str, int],
    log: LogCallback | None,
) -> SyncResult:
    from telethon.tl.patched import MessageService

    source = await client.get_entity(pair.source)
    destination = await client.get_entity(pair.destination)

    source_key = str(pair.source)
    last_id = progress.get(source_key, 0)

    await _emit(
        log,
        "info",
        f"Syncing {pair.source} -> {pair.destination} from message ID {last_id}.",
    )

    messages = []

    async for message in client.iter_messages(source, min_id=last_id):
        messages.append(message)

    messages.reverse()

    if not messages:
        await _emit(log, "info", f"No new messages for {pair.source}.")
        return SyncResult(
            source=pair.source,
            destination=pair.destination,
            forwarded=0,
            skipped=0,
            failed=0,
            latest_synced_id=last_id,
        )

    forwarded = 0
    skipped = 0
    failed = 0
    total = len(messages)

    await _emit(log, "info", f"Found {total} new message(s).")

    for index, message in enumerate(messages, start=1):
        try:
            if isinstance(message, MessageService):
                skipped += 1
                progress[source_key] = message.id
            else:
                await client.forward_messages(destination, message)
                forwarded += 1
                progress[source_key] = message.id
                await _emit(
                    log,
                    "success",
                    f"[{index}/{total}] Forwarded message ID {message.id}.",
                )
                await asyncio.sleep(0.2)

            if index % 10 == 0:
                _save_progress(progress)
        except Exception as exc:  # noqa: BLE001 - continue like the CLI.
            failed += 1
            await _emit(log, "error", f"[{index}/{total}] Message {message.id}: {exc}")

    _save_progress(progress)
    latest_synced_id = progress.get(source_key, last_id)

    await _emit(
        log,
        "success",
        f"Pair complete. Latest synced ID: {latest_synced_id}.",
    )

    return SyncResult(
        source=pair.source,
        destination=pair.destination,
        forwarded=forwarded,
        skipped=skipped,
        failed=failed,
        latest_synced_id=latest_synced_id,
    )


def _create_client():
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    credentials = _load_credentials()
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

    if credentials["session_string"]:
        session = StringSession(credentials["session_string"])
    else:
        session = str(SESSION_FILE)

    return TelegramClient(session, credentials["api_id"], credentials["api_hash"])


def _load_credentials() -> dict:
    load_dotenv(BASE_DIR / ".env")

    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    session_string = os.getenv("SESSION_STRING")

    if not api_id:
        raise ConfigError("API_ID is missing.")

    if not api_hash:
        raise ConfigError("API_HASH is missing.")

    try:
        parsed_api_id = int(api_id)
    except ValueError as exc:
        raise ConfigError("API_ID must be a number.") from exc

    return {
        "api_id": parsed_api_id,
        "api_hash": api_hash,
        "session_string": session_string,
    }


async def _emit(
    log: LogCallback | None,
    level: LogLevel,
    message: str,
) -> None:
    if log is None:
        return

    result = log(level, message)

    if hasattr(result, "__await__"):
        await result


def _load_config() -> dict:
    config = _read_json(CONFIG_FILE, {"pairs": []})
    config.setdefault("pairs", [])

    if not isinstance(config["pairs"], list):
        raise ConfigError("config.json must contain a pairs list.")

    return config


def _save_config(config: dict) -> None:
    _write_json(CONFIG_FILE, config)


def _save_progress(progress: dict[str, int]) -> None:
    _write_json(PROGRESS_FILE, progress)


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default.copy()

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def _find_pair_index(
    pairs: list[dict],
    source: int,
    destination: int,
) -> int | None:
    for index, pair in enumerate(pairs):
        if int(pair["source"]) == int(source) and int(pair["destination"]) == int(destination):
            return index

    return None


def _source_exists(pairs: list[dict], source: int) -> bool:
    return any(int(pair["source"]) == int(source) for pair in pairs)


def _pair_from_dict(pair: dict) -> ChannelPair:
    return ChannelPair(
        source=int(pair["source"]),
        destination=int(pair["destination"]),
        enabled=bool(pair.get("enabled", True)),
    )
