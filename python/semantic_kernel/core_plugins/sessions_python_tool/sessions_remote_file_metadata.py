# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseModel


class SessionsRemoteFileMetadata(KernelBaseModel):
    """Metadata for a file in the session."""

    filename: str
    """The filename relative to `/mnt/data`."""

    size_in_bytes: int
    """The size of the file in bytes."""

    @property
    def full_path(self) -> str:
        """Get the full path of the file."""
        return f"/mnt/data/{self.filename}"

    @staticmethod
    def from_dict(data: dict) -> "SessionsRemoteFileMetadata":
        """Create a RemoteFileMetadata object from a dictionary."""
        return SessionsRemoteFileMetadata(filename=data["filename"], size_in_bytes=data["bytes"])
