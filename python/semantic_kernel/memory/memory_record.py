# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from datetime import datetime

from numpy import ndarray


class MemoryRecord:
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

        Arguments:
            is_reference {bool} -- Whether the record is a reference record.
            external_source_name {str | None} -- The name of the external source.
            id {str} -- A unique for the record.
            description {str | None} -- The description of the record.
            text {str | None} -- The text of the record.
            additional_metadata {str | None} -- Custom metadata for the record.
            embedding {ndarray} -- The embedding of the record.

        Returns:
            None -- None.
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

        Arguments:
            external_id {str} -- The external id of the record.
            source_name {str} -- The name of the external source.
            description {str | None} -- The description of the record.
            additional_metadata {str | None} -- Custom metadata for the record.
            embedding {ndarray} -- The embedding of the record.

        Returns:
            MemoryRecord -- The reference record.
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

        Arguments:
            id {str} -- A unique for the record.
            text {str} -- The text of the record.
            description {str | None} -- The description of the record.
            additional_metadata {str | None} -- Custom metadata for the record.
            embedding {ndarray} -- The embedding of the record.
            timestamp {datetime | None} -- The timestamp of the record.

        Returns:
            MemoryRecord -- The local record.
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
        return self._id

    @property
    def embedding(self) -> ndarray:
        return self._embedding

    @property
    def text(self):
        return self._text

    @property
    def additional_metadata(self):
        return self._additional_metadata

    @property
    def description(self):
        return self._description

    @property
    def timestamp(self):
        return self._timestamp
