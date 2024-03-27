# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from numpy import ndarray

from semantic_kernel.memory.memory_record import MemoryRecord


class MemoryQueryResult:
    is_reference: bool
    external_source_name: str | None
    id: str
    description: str | None
    text: str | None
    additional_metadata: str | None
    relevance: float
    embedding: ndarray | None

    def __init__(
        self,
        is_reference: bool,
        external_source_name: str | None,
        id: str,
        description: str | None,
        text: str | None,
        additional_metadata: str | None,
        embedding: ndarray | None,
        relevance: float,
    ) -> None:
        """Initialize a new instance of MemoryQueryResult.

        Arguments:
            is_reference {bool} -- Whether the record is a reference record.
            external_source_name {str | None} -- The name of the external source.
            id {str} -- A unique for the record.
            description {str | None} -- The description of the record.
            text {str | None} -- The text of the record.
            embedding {ndarray} -- The embedding of the record.
            relevance {float} -- The relevance of the record to a known query.

        Returns:
            None -- None.
        """
        self.is_reference = is_reference
        self.external_source_name = external_source_name
        self.id = id
        self.description = description
        self.text = text
        self.additional_metadata = additional_metadata
        self.relevance = relevance
        self.embedding = embedding

    @staticmethod
    def from_memory_record(
        record: MemoryRecord,
        relevance: float,
    ) -> "MemoryQueryResult":
        """Create a new instance of MemoryQueryResult from a MemoryRecord.

        Arguments:
            record {MemoryRecord} -- The MemoryRecord to create the MemoryQueryResult from.
            relevance {float} -- The relevance of the record to a known query.

        Returns:
            MemoryQueryResult -- The created MemoryQueryResult.
        """
        return MemoryQueryResult(
            is_reference=record._is_reference,
            external_source_name=record._external_source_name,
            id=record._id,
            description=record._description,
            text=record._text,
            additional_metadata=record._additional_metadata,
            embedding=record._embedding,
            relevance=relevance,
        )
