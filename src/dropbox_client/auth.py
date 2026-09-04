"""Authentication helpers for Dropbox OAuth2 + refresh tokens."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox.oauth import OAuth2FlowNoRedirectResult


def load_credentials(env_file: Optional[str | Path] = None) -> dict[str, str]:
    """Load Dropbox credentials from environment / .env file."""
    if env_file:
        load_dotenv(env_file)
    else:
        # Try common locations
        for candidate in [".env", Path.cwd() / ".env", Path(__file__).resolve().parents[2] / ".env"]:
            if Path(candidate).exists():
                load_dotenv(candidate)
                break
        else:
            load_dotenv()  # still load from process env

    app_key = os.getenv("DROPBOX_APP_KEY", "").strip()
    app_secret = os.getenv("DROPBOX_APP_SECRET", "").strip()
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN", "").strip()

    if not app_key or not app_secret:
        raise ValueError(
            "DROPBOX_APP_KEY and DROPBOX_APP_SECRET must be set in the environment or .env file.\n"
            "See .env.example and the README for instructions."
        )

    return {
        "app_key": app_key,
        "app_secret": app_secret,
        "refresh_token": refresh_token,
    }


def get_authorization_url(
    app_key: str,
    app_secret: str,
    scopes: Optional[list[str]] = None,
) -> tuple[str, DropboxOAuth2FlowNoRedirect]:
    """
    Start the OAuth2 flow and return (authorization_url, flow_object).

    Default scopes cover common file operations. Adjust as needed.
    """
    if scopes is None:
        scopes = [
            "account_info.read",
            "files.metadata.read",
            "files.metadata.write",
            "files.content.read",
            "files.content.write",
            "sharing.read",
            "sharing.write",
        ]

    flow = DropboxOAuth2FlowNoRedirect(
        app_key,
        consumer_secret=app_secret,
        token_access_type="offline",  # critical: get a refresh token
        scope=scopes,
    )
    authorize_url = flow.start()
    return authorize_url, flow


def finish_authorization(
    flow: DropboxOAuth2FlowNoRedirect,
    auth_code: str,
) -> OAuth2FlowNoRedirectResult:
    """Exchange the authorization code for tokens."""
    return flow.finish(auth_code.strip())


def save_refresh_token(refresh_token: str, env_file: str | Path = ".env") -> None:
    """Write (or update) the refresh token in the .env file."""
    env_path = Path(env_file)
    lines: list[str] = []

    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    key = "DROPBOX_REFRESH_TOKEN="
    found = False
    new_lines = []
    for line in lines:
        if line.startswith(key) or line.startswith("#" + key):
            new_lines.append(f"{key}{refresh_token}")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}{refresh_token}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"Refresh token saved to {env_path.resolve()}")


def get_dropbox_client(
    env_file: Optional[str | Path] = None,
    timeout: Optional[float] = None,
) -> dropbox.Dropbox:
    """
    Return an authenticated dropbox.Dropbox instance.

    Uses the refresh token so the SDK handles access-token refresh automatically.
    """
    creds = load_credentials(env_file)

    if not creds["refresh_token"]:
        raise ValueError(
            "No DROPBOX_REFRESH_TOKEN found. Run `python scripts/authorize.py` first "
            "to complete the one-time OAuth flow."
        )

    kwargs = {
        "app_key": creds["app_key"],
        "app_secret": creds["app_secret"],
        "oauth2_refresh_token": creds["refresh_token"],
    }
    if timeout is not None:
        kwargs["timeout"] = timeout

    return dropbox.Dropbox(**kwargs)
