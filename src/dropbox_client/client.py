"""High-level Dropbox client wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, Iterator, Optional, Union

import dropbox
from dropbox.files import FileMetadata, FolderMetadata, DeletedMetadata, WriteMode

from .auth import get_dropbox_client, load_credentials


class DropboxClient:
    """Convenient wrapper around the official Dropbox SDK."""

    def __init__(
        self,
        env_file: Optional[str | Path] = None,
        dbx: Optional[dropbox.Dropbox] = None,
    ):
        if dbx is not None:
            self.dbx = dbx
        else:
            self.dbx = get_dropbox_client(env_file)

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------
    def get_current_account(self):
        return self.dbx.users_get_current_account()

    def account_display_name(self) -> str:
        return self.get_current_account().name.display_name

    # ------------------------------------------------------------------
    # Listing / Metadata
    # ------------------------------------------------------------------
    def list_folder(
        self,
        path: str = "",
        recursive: bool = False,
        include_deleted: bool = False,
    ) -> list[Union[FileMetadata, FolderMetadata, DeletedMetadata]]:
        """List a folder. path="" means the root of the app/full Dropbox."""
        result = self.dbx.files_list_folder(
            path,
            recursive=recursive,
            include_deleted=include_deleted,
        )
        entries = list(result.entries)

        while result.has_more:
            result = self.dbx.files_list_folder_continue(result.cursor)
            entries.extend(result.entries)

        return entries

    def list_folder_iter(
        self,
        path: str = "",
        recursive: bool = False,
    ) -> Iterator[Union[FileMetadata, FolderMetadata]]:
        """Generator version of list_folder."""
        result = self.dbx.files_list_folder(path, recursive=recursive)
        yield from result.entries

        while result.has_more:
            result = self.dbx.files_list_folder_continue(result.cursor)
            yield from result.entries

    def get_metadata(self, path: str):
        return self.dbx.files_get_metadata(path)

    # ------------------------------------------------------------------
    # Upload / Download
    # ------------------------------------------------------------------
    def upload(
        self,
        dropbox_path: str,
        content: Union[bytes, BinaryIO, str, Path],
        mode: WriteMode = WriteMode("overwrite"),
        mute: bool = False,
    ) -> FileMetadata:
        """
        Upload bytes, a file-like object, a local path, or a string.

        dropbox_path should start with / (e.g. "/folder/file.txt").
        """
        if isinstance(content, (str, Path)) and Path(content).exists():
            data = Path(content).read_bytes()
        elif isinstance(content, str):
            data = content.encode("utf-8")
        elif isinstance(content, bytes):
            data = content
        else:
            # assume file-like
            data = content.read()

        return self.dbx.files_upload(data, dropbox_path, mode=mode, mute=mute)

    def download(self, dropbox_path: str) -> bytes:
        """Download a file and return its content as bytes."""
        _metadata, response = self.dbx.files_download(dropbox_path)
        return response.content

    def download_to_file(self, dropbox_path: str, local_path: str | Path) -> FileMetadata:
        """Download a Dropbox file to a local path."""
        metadata, response = self.dbx.files_download(dropbox_path)
        Path(local_path).write_bytes(response.content)
        return metadata

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search(self, query: str, path: str = "", max_results: int = 100):
        """Simple search (files and folders)."""
        result = self.dbx.files_search_v2(
            query,
            options=dropbox.files.SearchOptions(
                path=path or None,
                max_results=max_results,
            ),
        )
        return result.matches

    # ------------------------------------------------------------------
    # Sharing
    # ------------------------------------------------------------------
    def create_shared_link(self, path: str, short_url: bool = False) -> str:
        """Create a shared link and return the URL."""
        settings = dropbox.sharing.SharedLinkSettings(
            requested_visibility=dropbox.sharing.RequestedVisibility.public,
        )
        link = self.dbx.sharing_create_shared_link_with_settings(path, settings=settings)
        return link.url

    def list_shared_links(self, path: Optional[str] = None):
        return self.dbx.sharing_list_shared_links(path=path).links

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def exists(self, path: str) -> bool:
        try:
            self.get_metadata(path)
            return True
        except dropbox.exceptions.ApiError as e:
            if isinstance(e.error, dropbox.files.GetMetadataError) and e.error.is_path() and e.error.get_path().is_not_found():
                return False
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # dropbox.Dropbox is context-manager friendly itself
        if hasattr(self.dbx, "__exit__"):
            return self.dbx.__exit__(exc_type, exc_val, exc_tb)
        return False
