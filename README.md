# Dropbox Python Client

Clean, modern Python client for the Dropbox API using the official SDK, with proper OAuth2 + refresh token support.

Designed so you can drop in real `APP_KEY` / `APP_SECRET` (and optionally a long-lived refresh token) and start working immediately.

## Features

- Official `dropbox` SDK (v12+)
- One-time OAuth2 authorization flow that obtains a **refresh token**
- Automatic token refresh (no manual access-token juggling)
- Simple high-level `DropboxClient` wrapper
- Ready-to-run examples (list files, upload, download, search, share links)
- `.env` based configuration

## Requirements

- Python **3.11+**
- A Dropbox App (create one at https://www.dropbox.com/developers/apps)

## Quick Start

### 1. Create a Dropbox App

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Create app → **Scoped access** (recommended) or Full Dropbox
3. Choose **App folder** or **Full Dropbox** depending on what you need
4. Under Permissions, enable at least:
   - `files.metadata.read`
   - `files.content.read`
   - `files.content.write`
   - (add more as needed)
5. Copy the **App key** and **App secret**

### 2. Install

```bash
git clone https://github.com/howyouaresignedin-max/dropbox-python-client.git
cd dropbox-python-client
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` and put your real values:

```env
DROPBOX_APP_KEY=your_app_key_here
DROPBOX_APP_SECRET=your_app_secret_here
# DROPBOX_REFRESH_TOKEN=   # leave empty the first time
```

### 4. Authorize once (get the refresh token)

```bash
python scripts/authorize.py
```

This will:

1. Print an authorization URL
2. Ask you to paste the code from Dropbox
3. Save the long-lived **refresh token** into your `.env`

After this you never need to re-authorize again (unless you revoke the token).

### 5. Use it

```python
from dropbox_client import DropboxClient

client = DropboxClient()          # reads from .env automatically

# List root
for entry in client.list_folder(""):
    print(entry.name, entry.path_display)

# Upload
client.upload("/hello.txt", b"Hello from the custom client!")

# Download
data = client.download("/hello.txt")
print(data.decode())
```

See the `examples/` folder for more.

## Project Layout

```
.
├── src/dropbox_client/
│   ├── __init__.py
│   ├── auth.py          # OAuth helpers + token loading
│   └── client.py        # High-level DropboxClient
├── scripts/
│   └── authorize.py     # One-time OAuth flow
├── examples/
│   ├── list_files.py
│   ├── upload_download.py
│   └── share_link.py
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Notes on Tokens

- We request `token_access_type="offline"` so Dropbox issues a **refresh token**.
- The official SDK automatically refreshes the short-lived access token when you pass `oauth2_refresh_token` + `app_key` + `app_secret`.
- Never commit your real `.env` or refresh token.

## License

MIT
