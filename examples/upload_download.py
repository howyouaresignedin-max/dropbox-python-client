#!/usr/bin/env python3
"""Simple upload + download round-trip example."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from dropbox_client import DropboxClient


def main() -> None:
    client = DropboxClient()

    remote_path = "/demo/hello-from-python-client.txt"
    content = b"Hello from the custom Dropbox Python client!\nThis file was uploaded via the official SDK + refresh token.\n"

    print(f"Uploading to {remote_path} ...")
    meta = client.upload(remote_path, content)
    print(f"Uploaded. Server modified: {meta.server_modified}")

    print("Downloading back ...")
    data = client.download(remote_path)
    print("Content:")
    print(data.decode("utf-8"))

    print("\nDone.")


if __name__ == "__main__":
    main()
