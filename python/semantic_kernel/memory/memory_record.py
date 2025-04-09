# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime

from numpy import ndarray

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class MemoryRecord:
    """The in-built memory record."""

    _key: str
    _timestamp: datetime | None
    _is_reference: bool
    _external_source_name: str | None
    _id: str
    _description: str | None
    _text: str | None
    _additional_metadata: str | None
    _embedding: ndarray

    def __init__(
        self,
        is_reference: bool,
        external_source_name: str | None,
        id: str,
        description: str | None,
        text: str | None,
        additional_metadata: str | None,
        embedding: ndarray | None,
        key: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Initialize a new instance of MemoryRecord.

        Args:
            is_reference (bool): Whether the record is a reference record.
            external_source_name (Optional[str]): The name of the external source.
            id (str): A unique for the record.
            description (Optional[str]): The description of the record.
            text (Optional[str]): The text of the record.
            additional_metadata (Optional[str]): Custom metadata for the record.
            embedding (ndarray): The embedding of the record.
            key (Optional[str]): The key of the record.
            timestamp (Optional[datetime]): The timestamp of the record.
        """
        self._key = key
        self._timestamp = timestamp
        self._is_reference = is_reference
        self._external_source_name = external_source_name
        self._id = id
        self._description = description
        self._text = text
        self._additional_metadata = additional_metadata
        self._embedding = embedding

    @staticmethod
    def reference_record(
        external_id: str,
        source_name: str,
        description: str | None,
        additional_metadata: str | None,
        embedding: ndarray,
    ) -> "MemoryRecord":
        """Create a reference record.

        Args:
            external_id (str): The external id of the record.
            source_name (str): The name of the external source.
            description (Optional[str]): The description of the record.
            additional_metadata (Optional[str]): Custom metadata for the record.
            embedding (ndarray): The embedding of the record.

        Returns:
            MemoryRecord: The reference record.
        """
        return MemoryRecord(
            is_reference=True,
            external_source_name=source_name,
            id=external_id,
            description=description,
            text=None,
            additional_metadata=additional_metadata,
            embedding=embedding,
        )

    @staticmethod
    def local_record(
        id: str,
        text: str,
        description: str | None,
        additional_metadata: str | None,
        embedding: ndarray,
        timestamp: datetime | None = None,
    ) -> "MemoryRecord":
        """Create a local record.

        Args:
            id (str): A unique for the record.
            text (str): The text of the record.
            description (Optional[str]): The description of the record.
            additional_metadata (Optional[str]): Custom metadata for the record.
            embedding (ndarray): The embedding of the record.
            timestamp (Optional[datetime]): The timestamp of the record.

        Returns:
            MemoryRecord: The local record.
        """
        return MemoryRecord(
            is_reference=False,
            external_source_name=None,
            id=id,
            description=description,
            text=text,
            additional_metadata=additional_metadata,
            timestamp=timestamp,
            embedding=embedding,
        )

    @property
    def id(self):
        """Get the unique identifier for the memory record."""
        return self._id

    @property
    def embedding(self) -> ndarray:
        """Get the embedding of the memory record."""
        return self._embedding

    @property
    def text(self):
        """Get the text of the memory record."""
        return self._text

    @property
    def additional_metadata(self):
        """Get the additional metadata of the memory record."""
        return self._additional_metadata

    @property
    def description(self):
        """Get the description of the memory record."""
        return self._description

    @property
    def timestamp(self):
        """Get the timestamp of the memory record."""
        return self._timestamp
