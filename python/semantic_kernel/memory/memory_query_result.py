# Copyright (c) Microsoft. All rights reserved.

from typing import Optional
from numpy import ndarray

from semantic_kernel.memory.memory_record import MemoryRecord


class MemoryQueryResult:
    is_reference: bool
    external_source_name: Optional[str]
    id: str
    description: Optional[str]
    text: Optional[str]
    relevance: float
    embedding: Optional[ndarray]

    def __init__(
        self,
        is_reference: bool,
        external_source_name: Optional[str],
        id: str,
        description: Optional[str],
        text: Optional[str],
        relevance: float,
        embedding: Optional[ndarray]
    ) -> None:
        self.is_reference = is_reference
        self.external_source_name = external_source_name
        self.id = id
        self.description = description
        self.text = text
        self.relevance = relevance
        self.embedding = embedding

    @staticmethod
    def from_memory_record(
        record: MemoryRecord,
        relevance: float,
    ) -> "MemoryQueryResult":
        return MemoryQueryResult(
            is_reference=record._is_reference,
            external_source_name=record._external_source_name,
            id=record._id,
            description=record._description,
            text=record._text,
            embedding=record._embedding,
            relevance=relevance,
        )
