# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from dataclasses import dataclass


@dataclass
class Field(ABC):
    name: str | None = None


@dataclass
class MemoryRecordKeyField(Field):
    """Memory record key field."""

    name: str = "key"


@dataclass
class MemoryRecordDataField(Field):
    """Memory record data field."""

    has_embedding: bool = False
    embedding_property_name: str | None = None


@dataclass
class MemoryRecordVectorField(Field):
    """Memory record vector field."""
