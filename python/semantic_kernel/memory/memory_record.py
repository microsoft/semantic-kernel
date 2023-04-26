# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from numpy import ndarray


class MemoryRecord:
    _key: str
    _timestamp: str
    _is_reference: bool
    _external_source_name: Optional[str]
    _id: str
    _description: Optional[str]
    _text: Optional[str]
    _embedding: ndarray

    def __init__(
        self,
        is_reference: bool,
        external_source_name: Optional[str],
        id: str,
        description: Optional[str],
        text: Optional[str],
        embedding: ndarray,
        key: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        self._key = key
        self._timestamp = timestamp
        self._is_reference = is_reference
        self._external_source_name = external_source_name
        self._id = id
        self._description = description
        self._text = text
        self._embedding = embedding

    @property
    def embedding(self) -> ndarray:
        return self.embedding

    @staticmethod
    def reference_record(
        external_id: str,
        source_name: str,
        description: Optional[str],
        embedding: ndarray,
    ) -> "MemoryRecord":
        return MemoryRecord(
            is_reference=True,
            external_source_name=source_name,
            id=external_id,
            description=description,
            text=None,
            embedding=embedding,
        )

    @staticmethod
    def local_record(
        id: str, text: str, description: Optional[str], embedding: ndarray
    ) -> "MemoryRecord":
        return MemoryRecord(
            is_reference=False,
            external_source_name=None,
            id=id,
            description=description,
            text=text,
            embedding=embedding,
        )
