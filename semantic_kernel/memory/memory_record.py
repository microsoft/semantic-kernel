# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from numpy import ndarray


class MemoryRecord:
    is_reference: bool
    external_source_name: Optional[str]
    id: str
    description: Optional[str]
    text: Optional[str]
    _embedding: ndarray

    def __init__(
        self,
        is_reference: bool,
        external_source_name: Optional[str],
        id: str,
        description: Optional[str],
        text: Optional[str],
        embedding: ndarray,
    ) -> None:
        self.is_reference = is_reference
        self.external_source_name = external_source_name
        self.id = id
        self.description = description
        self.text = text
        self._embedding = embedding

    @property
    def embedding(self) -> ndarray:
        return self._embedding

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
