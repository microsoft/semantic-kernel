# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime

from semantic_kernel.memory.memory_record import MemoryRecord


class DataEntry:
    _key: str
    _value: MemoryRecord
    _timestamp: datetime

    def __init__(self, key: str, value: MemoryRecord, timestamp: datetime) -> None:
        self._key = key
        self._value = value
        self._timestamp = timestamp

    @property
    def key(self) -> str:
        return self._key

    @property
    def value(self) -> MemoryRecord:
        return self._value

    @value.setter
    def value(self, value: MemoryRecord) -> None:
        self._value = value

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp: datetime) -> None:
        self._timestamp = timestamp
