"""High-level Dropbox client wrapper."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import BinaryIO, Iterator, Optional, Union

import dropbox
from dropbox.files import (
    FileMetadata,
    FolderMetadata,
    DeletedMetadata,
    WriteMode,
    RelocationPath,
)
from dropbox.exceptions import ApiError

from .auth import get_dropbox_client

logger = logging.getLogger(__name__)


class DropboxClient:
    """Convenient, production-oriented wrapper around the official Dropbox SDK."""

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
            data = content.read()

        logger.info("Uploading to %s (%d bytes)", dropbox_path, len(data))
        return self.dbx.files_upload(data, dropbox_path, mode=mode, mute=mute)

    def download(self, dropbox_path: str) -> bytes:
        """Download a file and return its content as bytes."""
        _metadata, response = self.dbx.files_download(dropbox_path)
        return response.content

    def download_to_file(self, dropbox_path: str, local_path: str | Path) -> FileMetadata:
        """Download a Dropbox file to a local path."""
        metadata, response = self.dbx.files_download(dropbox_path)
        Path(local_path).write_bytes(response.content)
        logger.info("Downloaded %s → %s", dropbox_path, local_path)
        return metadata

    # ------------------------------------------------------------------
    # Folder & File management
    # ------------------------------------------------------------------
    def create_folder(self, path: str) -> FolderMetadata:
        """Create a folder (and any missing parents)."""
        logger.info("Creating folder %s", path)
        return self.dbx.files_create_folder_v2(path).metadata

    def move(self, from_path: str, to_path: str) -> Union[FileMetadata, FolderMetadata]:
        """Move or rename a file/folder."""
        logger.info("Moving %s → %s", from_path, to_path)
        return self.dbx.files_move_v2(from_path, to_path).metadata

    def copy(self, from_path: str, to_path: str) -> Union[FileMetadata, FolderMetadata]:
        """Copy a file or folder."""
        logger.info("Copying %s → %s", from_path, to_path)
        return self.dbx.files_copy_v2(from_path, to_path).metadata

    def delete(self, path: str) -> Union[FileMetadata, FolderMetadata, DeletedMetadata]:
        """Delete a file or folder."""
        logger.info("Deleting %s", path)
        return self.dbx.files_delete_v2(path).metadata

    # ------------------------------------------------------------------
    # Temporary / Direct links
    # ------------------------------------------------------------------
    def get_temporary_link(self, path: str) -> str:
        """
        Get a temporary direct download link (usually valid ~4 hours).
        Useful for streaming or short-lived sharing without creating a permanent shared link.
        """
        result = self.dbx.files_get_temporary_link(path)
        return result.link

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
    def create_shared_link(self, path: str) -> str:
        """Create a public shared link and return the URL."""
        settings = dropbox.sharing.SharedLinkSettings(
            requested_visibility=dropbox.sharing.RequestedVisibility.public,
        )
        try:
            link = self.dbx.sharing_create_shared_link_with_settings(path, settings=settings)
            return link.url
        except ApiError as e:
            # If a shared link already exists, just return the existing one
            if (
                e.error.is_shared_link_already_exists()
                and e.error.get_shared_link_already_exists().metadata
            ):
                return e.error.get_shared_link_already_exists().metadata.url
            raise

    def list_shared_links(self, path: Optional[str] = None):
        return self.dbx.sharing_list_shared_links(path=path).links

    def revoke_shared_link(self, url: str) -> None:
        """Revoke a shared link."""
        self.dbx.sharing_revoke_shared_link(url)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def exists(self, path: str) -> bool:
        try:
            self.get_metadata(path)
            return True
        except ApiError as e:
            if (
                isinstance(e.error, dropbox.files.GetMetadataError)
                and e.error.is_path()
                and e.error.get_path().is_not_found()
            ):
                return False
            raise

    def ensure_folder(self, path: str) -> FolderMetadata:
        """Create the folder if it does not already exist."""
        if self.exists(path):
            meta = self.get_metadata(path)
            if isinstance(meta, FolderMetadata):
                return meta
            raise ValueError(f"Path exists but is not a folder: {path}")
        return self.create_folder(path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self.dbx, "__exit__"):
            return self.dbx.__exit__(exc_type, exc_val, exc_tb)
        return False
