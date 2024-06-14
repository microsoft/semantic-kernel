# Copyright (c) Microsoft. All rights reserved.


from dataclasses import dataclass, field
from re import M
from typing import Annotated, Any
from uuid import UUID, uuid4
from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_vector_record_store import (
    AzureAISearchVectorRecordStore,
)
from semantic_kernel.memory.data_model.data_model_decorator import datamodel
from semantic_kernel.memory.data_model.vector_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)


@datamodel
@dataclass
class MyDataModel:
    vector: Annotated[list[float], VectorStoreRecordVectorField]
    other: str | None
    key: Annotated[UUID, VectorStoreRecordKeyField()] = field(default_factory=uuid4)
    content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")] = (
        "content1"
    )

    def serialize(self) -> dict[str, Any]:
        return {
            "vector": self.vector,
            "other": self.other,
            "key": self.key,
            "content": self.content,
        }

    @classmethod
    def deserialize(cls, obj: dict[str, Any]) -> "MyDataModel":
        return cls(
            vector=obj["vector"],
            other=obj["other"],
            key=obj["key"],
            content=obj["content"],
        )


record_store = AzureAISearchVectorRecordStore(item_type=MyDataModel, collection_name="edvan-index")

record1 = MyDataModel(vector=[1.0, 2.0, 3.0], other="other1")
record2 = MyDataModel(vector=[4.0, 5.0, 6.0], other="other2")

record_store.upsert(record1)
record_store.upsert(record2)
