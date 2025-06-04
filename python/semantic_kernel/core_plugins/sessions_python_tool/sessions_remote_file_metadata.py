# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.kernel_pydantic import KernelBaseModel


class SessionsRemoteFileMetadata(KernelBaseModel):
    """Metadata for a file in the session."""

    """The filename relative to `/mnt/data/`."""
    filename: str

    """The size of the file in bytes."""
    size_in_bytes: int

    @property
    def full_path(self) -> str:
        """Get the full path of the file."""
        if not self.filename.startswith("/mnt/data/"):
            return f"/mnt/data/{self.filename}"
        return self.filename

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SessionsRemoteFileMetadata":
        """Create a SessionsRemoteFileMetadata object from a dictionary of file data values.

        Args:
            data (dict[str, Any]): The file data values.

        Returns:
            SessionsRemoteFileMetadata: The metadata for the file.
        """
        return SessionsRemoteFileMetadata(filename=data["filename"], size_in_bytes=data["size"])
