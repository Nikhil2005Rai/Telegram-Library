# Telegram Library Sync

A Telegram channel synchronization tool built with Python and Telethon.

The application automatically mirrors messages from one or more source channels to destination channels while preserving chronological order and tracking synchronization progress.

---

# Features

* Sync messages from Telegram channels to backup/archive channels
* Support multiple source → destination channel pairs
* Resume from the last synced message after interruption
* Progress tracking using local storage
* Enable or disable channel pairs without deleting them
* Add, list, remove, and manage channel pairs through CLI tools
* Automatic chronological forwarding (oldest → newest)
* Support for text messages, media, documents, and forwarded content
* Session persistence using Telethon session files

---

# Project Structure

```text
telegram-library/
│
├── sync.py
├── add_pair.py
├── list_pairs.py
├── remove_pair.py
├── toggle_pair.py
├── utils.py
│
├── config.json
├── progress.json
├── requirements.txt
│
└── sessions/
    └── session.session
```

---

# How It Works

## Configuration

All source and destination channel mappings are stored in:

```text
config.json
```

Example:

```json
{
  "api_id": 12345678,
  "api_hash": "your_api_hash",
  "pairs": [
    {
      "source": -1001111111111,
      "destination": -1002222222222,
      "enabled": true
    }
  ]
}
```

Each pair defines:

* Source channel ID
* Destination channel ID
* Whether synchronization is enabled

---

## Progress Tracking

Synchronization progress is stored in:

```text
progress.json
```

Example:

```json
{
  "-1001111111111": 1875
}
```

This means the source channel has been synchronized up to message ID 1875.

When the application runs again, only messages newer than that ID are processed.

---

## Synchronization Process

The sync engine performs the following steps:

1. Load configuration from `config.json`
2. Load synchronization progress from `progress.json`
3. Connect to Telegram using Telethon
4. Iterate through all enabled channel pairs
5. Retrieve messages newer than the last synchronized ID
6. Reverse message order to maintain chronology
7. Forward messages to the destination channel
8. Update progress information
9. Save progress periodically
10. Disconnect from Telegram

---

# Installation

## Clone the Project

```bash
git clone <repository-url>
cd telegram-library
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Create Telegram API Credentials

Visit:

https://my.telegram.org/apps

Create an application and obtain:

* API ID
* API Hash

---

## Configure Credentials

Edit:

```text
config.json
```

Example:

```json
{
  "api_id": 12345678,
  "api_hash": "your_api_hash",
  "pairs": []
}
```

---

# First Login

Run:

```bash
python sync.py
```

Telethon will ask for:

```text
Phone Number
Verification Code
```

After successful authentication, a session file will be created:

```text
sessions/session.session
```

Future executions will use the saved session automatically.

---

# Finding Channel IDs

Use a utility script or Telethon to obtain channel IDs.

Example format:

```text
Source Channel      -> -1003500551621
Destination Channel -> -1003368170139
```

These IDs are used when creating synchronization pairs.

---

# Usage

## Add a Pair

```bash
python add_pair.py
```

Example:

```text
Source Channel ID:
-1003500551621

Destination Channel ID:
-1003368170139
```

---

## List All Pairs

```bash
python list_pairs.py
```

Displays:

* Source channel
* Destination channel
* Enabled/disabled status

---

## Remove a Pair

```bash
python remove_pair.py
```

Select the pair number to delete.

---

## Enable or Disable a Pair

```bash
python toggle_pair.py
```

Select the pair number to toggle.

Disabled pairs are skipped during synchronization.

---

## Run Synchronization

```bash
python sync.py
```

The application will:

* Read enabled pairs
* Synchronize new messages only
* Update progress
* Exit when complete

---

# Example Workflow

## Step 1

Add a synchronization pair:

```bash
python add_pair.py
```

---

## Step 2

Verify the pair:

```bash
python list_pairs.py
```

---

## Step 3

Run synchronization:

```bash
python sync.py
```

---

## Step 4

Run synchronization again later:

```bash
python sync.py
```

Only newly posted messages will be processed.

---

# Progress Recovery

The application is designed to recover from interruptions.

Example:

```text
Message 1 synced
Message 2 synced
Message 3 synced
Application closed
```

Upon restart:

```bash
python sync.py
```

Synchronization resumes from the last saved position.

---

# Session Files

The following files contain sensitive information:

```text
sessions/session.session
config.json
```

Do not publish these files.

Recommended `.gitignore`:

```gitignore
sessions/
*.session
*.session-journal
progress.json
__pycache__/
```

---

# Requirements

* Python 3.10+
* Telethon

---

# Future Improvements

* Web dashboard using Next.js
* Automatic scheduling
* Channel validation
* Statistics dashboard
* Search and filtering
* Notification system
* Docker deployment
* GitHub Actions automation

---

# Disclaimer

Use this software responsibly and ensure you comply with Telegram's Terms of Service and any applicable channel permissions or content restrictions.
