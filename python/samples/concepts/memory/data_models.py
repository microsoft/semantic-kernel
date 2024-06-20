# Copyright (c) Microsoft. All rights reserved.
from dataclasses import dataclass, field
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import Field

from semantic_kernel.data.models.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.models.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel


@vectorstoremodel
@dataclass
class DataModelDataclass:
    vector: Annotated[list[float], VectorStoreRecordVectorField]
    other: str | None
    key: Annotated[UUID, VectorStoreRecordKeyField()] = field(default_factory=uuid4)
    content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")] = (
        "content1"
    )


@vectorstoremodel
class DataModelPydantic(KernelBaseModel):
    vector: Annotated[list[float], VectorStoreRecordVectorField]
    other: str | None
    key: Annotated[UUID, VectorStoreRecordKeyField()] = Field(default_factory=uuid4)
    content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")] = (
        "content1"
    )


@vectorstoremodel
class DataModelPydanticComplex(KernelBaseModel):
    vector: Annotated[list[float], VectorStoreRecordVectorField]
    other: str | None
    key: Annotated[UUID, Field(default_factory=uuid4), VectorStoreRecordKeyField()]
    content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")] = (
        "content1"
    )


@vectorstoremodel
class DataModelPython:
    def __init__(
        self,
        vector: Annotated[list[float], VectorStoreRecordVectorField],
        other: str | None,
        key: Annotated[UUID, VectorStoreRecordKeyField] | None = None,
        content: Annotated[
            str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")
        ] = "content1",
    ):
        self.vector = vector
        self.other = other
        self.key = key or uuid4()
        self.content = content

    def serialize(self) -> dict[str, Any]:
        return {
            "vector": self.vector,
            "other": self.other,
            "key": self.key,
            "content": self.content,
        }

    @classmethod
    def deserialize(cls, obj: dict[str, Any]) -> "DataModelDataclass":
        return cls(
            vector=obj["vector"],
            other=obj["other"],
            key=obj["key"],
            content=obj["content"],
        )


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
    print(f"{data_item1.__kernel_data_model_fields__=}")
    print(f"{data_item2.__kernel_data_model_fields__=}")
    print(f"{data_item3.__kernel_data_model_fields__=}")
    print(f"{data_item4.__kernel_data_model_fields__=}")
    if (
        data_item1.__kernel_data_model_fields__
        == data_item2.__kernel_data_model_fields__
        == data_item3.__kernel_data_model_fields__
        == data_item4.__kernel_data_model_fields__
    ):
        print("All data models are the same")
    else:
        print("Data models are not the same")
