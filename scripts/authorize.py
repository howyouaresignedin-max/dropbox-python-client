#!/usr/bin/env python3
"""
One-time OAuth2 authorization script.

Run this once after putting your APP_KEY and APP_SECRET into .env.
It will obtain a long-lived refresh token and save it back into .env.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the package importable when running from the repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from dropbox_client.auth import (
    get_authorization_url,
    finish_authorization,
    load_credentials,
    save_refresh_token,
)


def main() -> None:
    print("=== Dropbox OAuth2 Authorization ===\n")

    try:
        creds = load_credentials()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nMake sure you have created .env from .env.example and filled in")
        print("DROPBOX_APP_KEY and DROPBOX_APP_SECRET.")
        sys.exit(1)

    if creds["refresh_token"]:
        print("A refresh token is already present in .env.")
        answer = input("Do you want to re-authorize and overwrite it? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted.")
            return

    authorize_url, flow = get_authorization_url(creds["app_key"], creds["app_secret"])

    print("1. Open this URL in your browser:\n")
    print(authorize_url)
    print()
    print("2. Click 'Allow' (you may need to log in first).")
    print("3. Copy the authorization code that Dropbox shows you.\n")

    auth_code = input("Paste the authorization code here: ").strip()
    if not auth_code:
        print("No code entered. Exiting.")
        sys.exit(1)

    try:
        result = finish_authorization(flow, auth_code)
    except Exception as e:
        print(f"\nAuthorization failed: {e}")
        sys.exit(1)

    if not result.refresh_token:
        print("\nWarning: No refresh token was returned.")
        print("Make sure you requested token_access_type='offline' (this script does).")
        sys.exit(1)

    save_refresh_token(result.refresh_token)

    print("\nSuccess!")
    print(f"Access token expires at: {result.expires_at}")
    print(f"Granted scopes: {result.scope}")
    print("\nYou can now use the client without further authorization.")


if __name__ == "__main__":
    main()
