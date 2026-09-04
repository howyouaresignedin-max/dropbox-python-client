#!/usr/bin/env python3
"""Create a public shared link for a file."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from dropbox_client import DropboxClient


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python examples/share_link.py /path/to/file-in-dropbox")
        sys.exit(1)

    path = sys.argv[1]
    client = DropboxClient()

    print(f"Creating shared link for {path} ...")
    url = client.create_shared_link(path)
    print(f"Shared link: {url}")


if __name__ == "__main__":
    main()
