#!/usr/bin/env python3
"""List files and folders in the root of your Dropbox (or app folder)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from dropbox_client import DropboxClient


def main() -> None:
    client = DropboxClient()

    print(f"Connected as: {client.account_display_name()}\n")
    print("Contents of root:\n")

    for entry in client.list_folder(""):
        kind = "DIR " if entry.__class__.__name__ == "FolderMetadata" else "FILE"
        size = getattr(entry, "size", None)
        size_str = f"{size:>10} bytes" if size is not None else ""
        print(f"  {kind}  {entry.path_display:<50} {size_str}")


if __name__ == "__main__":
    main()
