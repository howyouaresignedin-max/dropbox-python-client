# Dropbox Python Client

Clean, modern Python client for the Dropbox API using the official SDK, with proper OAuth2 + refresh token support.

Designed so you can drop in real `APP_KEY` / `APP_SECRET` (and optionally a long-lived refresh token) and start working immediately.

**Current status:** v0.2 — expanded client ready for MCP wrapper and future official connector work.

## Features

- Official `dropbox` SDK (v12+)
- One-time OAuth2 authorization flow that obtains a **refresh token**
- Automatic token refresh
- High-level `DropboxClient` with:
  - list / search
  - upload / download
  - create / move / copy / delete files & folders
  - temporary links
  - shared links (create + revoke)
  - helpers (`exists`, `ensure_folder`)
- Ready-to-run examples
- `.env` based configuration

## Requirements

- Python **3.11+**
- A Dropbox App (https://www.dropbox.com/developers/apps)

## Quick Start

### 1. Create a Dropbox App

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Create app → **Scoped access**
3. Choose **App folder** or **Full Dropbox**
4. Enable at least these scopes:
   - `account_info.read`
   - `files.metadata.read` / `files.metadata.write`
   - `files.content.read` / `files.content.write`
   - `sharing.read` / `sharing.write` (if you want shared links)
5. Copy the **App key** and **App secret**

### 2. Install

```bash
git clone https://github.com/howyouaresignedin-max/dropbox-python-client.git
cd dropbox-python-client
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
```

Edit `.env`:

```env
DROPBOX_APP_KEY=your_app_key_here
DROPBOX_APP_SECRET=your_app_secret_here
# DROPBOX_REFRESH_TOKEN=   # filled automatically by authorize.py
```

### 4. Authorize once

```bash
python scripts/authorize.py
```

### 5. Use it

```python
from dropbox_client import DropboxClient

client = DropboxClient()

print(client.account_display_name())

# List
for entry in client.list_folder(""):
    print(entry.name)

# Upload
client.upload("/hello.txt", b"Hello!")

# Temporary direct link
url = client.get_temporary_link("/hello.txt")
print(url)
```

## Project Layout

```
.
├── src/dropbox_client/
│   ├── __init__.py
│   ├── auth.py
│   └── client.py
├── scripts/
│   └── authorize.py
├── examples/
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Roadmap (toward official connector)

- [x] Solid OAuth2 + refresh token client
- [x] Expanded high-level API
- [ ] MCP server wrapper (`dropbox-mcp`)
- [ ] Tool schema that matches platform connector style
- [ ] Beta testing + feedback
- [ ] Possible future official connector submission

## License

MIT
