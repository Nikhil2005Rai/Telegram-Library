# Telegram Library Sync

A small Python utility for mirroring Telegram channel messages from one or more source channels into destination channels.

The project uses [Telethon](https://docs.telethon.dev/) to connect to Telegram, forwards only messages that have not been synced yet, and stores local progress so a later run can continue where the previous run stopped.

## Features

- Mirror messages from Telegram source channels to archive or backup channels.
- Manage multiple source-to-destination pairs.
- Enable or disable pairs without deleting them.
- Resume from the last synced message ID after an interruption.
- Preserve chronological order by forwarding older new messages before newer ones.
- Forward normal Telegram messages, including media and documents supported by Telethon forwarding.
- Skip Telegram service messages while still advancing progress.
- Use either a local Telethon session file or a `SESSION_STRING`.

## Project Structure

```text
telegram-library/
|-- sync.py               # Main sync runner
|-- add_pair.py           # Add a source/destination pair
|-- list_pairs.py         # Show configured pairs
|-- remove_pair.py        # Remove a configured pair
|-- toggle_pair.py        # Enable or disable a pair
|-- teleGetChannelId.py   # Print visible Telegram dialog IDs
|-- stringSession.py      # Generate a Telethon string session
|-- utils.py              # Shared config, progress, and session helpers
|-- config.json           # Channel pair configuration
|-- progress.json         # Last synced message ID per source channel
|-- requirements.txt      # Python dependencies
`-- sessions/             # Local Telethon session files
```

## Requirements

- Python 3.10 or newer
- A Telegram account
- Telegram API credentials from <https://my.telegram.org/apps>

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Create `.env`

The application reads Telegram credentials from environment variables. Create a `.env` file in the project root:

```env
API_ID=12345678
API_HASH=your_api_hash_here
```

You can also use a Telethon string session instead of a local session file:

```env
API_ID=12345678
API_HASH=your_api_hash_here
SESSION_STRING=your_string_session_here
```

If `SESSION_STRING` is not set, the app creates and reuses a local session at:

```text
sessions/session.session
```

### 2. Configure channel pairs

Channel pairs are stored in `config.json`:

```json
{
  "pairs": [
    {
      "source": -1001111111111,
      "destination": -1002222222222,
      "enabled": true
    }
  ]
}
```

Each pair contains:

- `source`: Telegram channel, group, or chat ID to read from.
- `destination`: Telegram channel, group, or chat ID to forward into.
- `enabled`: whether the sync runner should process the pair.

Use the helper scripts below instead of editing `config.json` by hand when possible.

## First Login

Run the sync script:

```bash
python sync.py
```

On the first local-session run, Telethon may ask for your phone number, login code, and two-step verification password if your account requires one. After login, future runs reuse the saved session.

## Finding Channel IDs

Run:

```bash
python teleGetChannelId.py
```

The script prints the names and IDs of dialogs visible to the authenticated account. Telegram channel IDs commonly look like this:

```text
-1003500551621
```

Make sure the authenticated account has permission to read from the source and post or forward into the destination.

## Usage

Add a pair:

```bash
python add_pair.py
```

List configured pairs:

```bash
python list_pairs.py
```

Enable or disable a pair:

```bash
python toggle_pair.py
```

Remove a pair:

```bash
python remove_pair.py
```

Run synchronization:

```bash
python sync.py
```

During a sync run, the app:

1. Loads `config.json`.
2. Loads `progress.json`.
3. Connects to Telegram using either `SESSION_STRING` or `sessions/session.session`.
4. Processes each enabled pair.
5. Reads messages newer than the last saved message ID.
6. Reverses the fetched batch so messages forward oldest to newest.
7. Saves progress every 10 processed messages and again at the end of each pair.
8. Disconnects from Telegram.

## Progress Tracking

Progress is stored in `progress.json` using the source channel ID as the key:

```json
{
  "-1001111111111": 1875
}
```

This means source channel `-1001111111111` has been processed through message ID `1875`. The next sync only requests messages with higher IDs.

To intentionally resync a source from the beginning, stop the app and remove that source entry from `progress.json`. Be careful: doing this can duplicate forwarded messages in the destination.

## String Sessions

The project includes `stringSession.py` for generating a Telethon string session. A string session is useful when running the sync on a server or CI environment where you do not want to store a `.session` file.

Run:

```bash
python stringSession.py
```

Then place the printed value in `.env` as `SESSION_STRING`.

Treat string sessions like passwords. Anyone with the value can access the Telegram account session.

## Security Notes

Keep these files and values private:

- `.env`
- `SESSION_STRING`
- `sessions/`
- `*.session`
- `*.session-journal`

The included `.gitignore` already excludes these local secrets and session files.

## Troubleshooting

`TypeError` or `ValueError` while loading credentials:

- Check that `.env` exists.
- Confirm `API_ID` is present and is a number.
- Confirm `API_HASH` is present.

No dialogs or channel IDs appear:

- Log in with the Telegram account that belongs to the target channels.
- Confirm the account can see the channels in Telegram.

Sync finds no new messages:

- Check `progress.json`; the stored message ID may already be current.
- Confirm the pair is enabled with `python list_pairs.py`.
- Confirm the source ID is correct.

Forwarding fails for a message:

- Confirm the account has permission to post in the destination.
- Some Telegram messages or protected content may not be forwardable.
- Telegram flood limits can temporarily slow or block forwarding.

## Notes and Limitations

- The tool forwards messages; it does not clone channel settings, members, reactions, comments, or metadata.
- Progress is tracked per source channel ID, not per source/destination pair. If the same source is synced to multiple destinations, they share one progress entry.
- `progress.json` is local state. Back it up if you rely on exact resume behavior.
- Always follow Telegram's Terms of Service and respect channel permissions, copyright, and privacy expectations.
