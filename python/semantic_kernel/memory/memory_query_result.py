# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from semantic_kernel.memory.memory_record import MemoryRecord


class MemoryQueryResult:
    is_reference: bool
    external_source_name: Optional[str]
    id: str
    description: Optional[str]
    text: Optional[str]
    relevance: float

    def __init__(
        self,
        is_reference: bool,
        external_source_name: Optional[str],
        id: str,
        description: Optional[str],
        text: Optional[str],
        relevance: float,
    ) -> None:
        self.is_reference = is_reference
        self.external_source_name = external_source_name
        self.id = id
        self.description = description
        self.text = text
        self.relevance = relevance

    @staticmethod
    def from_memory_record(
        record: MemoryRecord, relevance: float
    ) -> "MemoryQueryResult":
        return MemoryQueryResult(
            is_reference=record.is_reference,
            external_source_name=record.external_source_name,
            id=record.id,
            description=record.description,
            text=record.text,
            relevance=relevance,
        )
