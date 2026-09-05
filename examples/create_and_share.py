#!/usr/bin/env python3
"""Create a folder, upload a file, and generate a shared link."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from dropbox_client import DropboxClient


def main() -> None:
    client = DropboxClient()

    folder = "/demo-from-client"
    file_path = f"{folder}/readme.txt"

    print(f"Ensuring folder {folder} ...")
    client.ensure_folder(folder)

    print(f"Uploading {file_path} ...")
    client.upload(file_path, b"Created by the Dropbox Python client.\n")

    print("Creating shared link ...")
    url = client.create_shared_link(file_path)
    print(f"Shared link: {url}")

    print("Temporary direct link:")
    print(client.get_temporary_link(file_path))


if __name__ == "__main__":
    main()
