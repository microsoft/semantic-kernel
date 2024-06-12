# Copyright (c) Microsoft. All rights reserved.
from dataclasses import dataclass, field
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.memory.data_model.data_model_decorator import datamodel
from semantic_kernel.memory.data_model.memory_record_fields import (
    MemoryRecordDataField,
    MemoryRecordKeyField,
    MemoryRecordVectorField,
)


@datamodel
@dataclass
class DataModelDataclass:
    vector: Annotated[list[float], MemoryRecordVectorField]
    other: str | None
    key: Annotated[UUID, MemoryRecordKeyField()] = field(default_factory=uuid4)
    content: Annotated[str, MemoryRecordDataField(has_embedding=True, embedding_property_name="vector")] = "content1"


@datamodel
class DataModelPydantic(KernelBaseModel):
    vector: Annotated[list[float], MemoryRecordVectorField]
    other: str | None
    key: Annotated[UUID, MemoryRecordKeyField()] = Field(default_factory=uuid4)
    content: Annotated[str, MemoryRecordDataField(has_embedding=True, embedding_property_name="vector")] = "content1"


@datamodel
class DataModelPydanticComplex(KernelBaseModel):
    vector: Annotated[list[float], MemoryRecordVectorField]
    other: str | None
    key: Annotated[UUID, Field(default_factory=uuid4), MemoryRecordKeyField()]
    content: Annotated[str, MemoryRecordDataField(has_embedding=True, embedding_property_name="vector")] = "content1"


@datamodel
class DataModelPython:
    def __init__(
        self,
        vector: Annotated[list[float], MemoryRecordVectorField],
        other: str | None,
        key: Annotated[UUID, MemoryRecordKeyField] | None = None,
        content: Annotated[
            str, MemoryRecordDataField(has_embedding=True, embedding_property_name="vector")
        ] = "content1",
    ):
        self.vector = vector
        self.other = other
        self.key = key or uuid4()
        self.content = content


if __name__ == "__main__":
    data_item1 = DataModelDataclass(content="Hello, world!", vector=[1.0, 2.0, 3.0], other=None)
    data_item2 = DataModelPydantic(content="Hello, world!", vector=[1.0, 2.0, 3.0], other=None)
    data_item3 = DataModelPydanticComplex(
        content="Hello, world!",
        vector=[1.0, 2.0, 3.0],
        other=None,
    )
    data_item4 = DataModelPython(content="Hello, world!", vector=[1.0, 2.0, 3.0], other=None)
    print(
        f"item1 key: {data_item1.key}, item2 key: {data_item2.key}, "
        f"item3 key: {data_item3.key}, item4 key: {data_item4.key}"
    )
    print(
        f"item1 content: {data_item1.content}, item2 content: {data_item2.content}, "
        f"item3 content: {data_item3.content}, item4 content: {data_item4.content}"
    )
    print("item1 details:")
    item = "item1"
    for name, value in data_item1.__sk_data_model_fields__.items():
        print(f"    {item}: {name} -> {value}")

    print("item2 details:")
    item = "item2"
    for name, value in data_item2.__sk_data_model_fields__.items():
        print(f"    {item}: {name} -> {value}")

    print("item3 details:")
    item = "item3"
    for name, value in data_item3.__sk_data_model_fields__.items():
        print(f"    {item}: {name} -> {value}")

    print("item4 details:")
    item = "item4"
    for name, value in data_item4.__sk_data_model_fields__.items():
        print(f"    {item}: {name} -> {value}")
    if (
        data_item1.__sk_data_model_fields__
        == data_item2.__sk_data_model_fields__
        == data_item3.__sk_data_model_fields__
        == data_item4.__sk_data_model_fields__
    ):
        print("All data models are the same")
    else:
        print("Data models are not the same")
