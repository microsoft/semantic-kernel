# Copyright (c) Microsoft. All rights reserved.


import os
from dataclasses import dataclass, field
from typing import Annotated, Any
from uuid import UUID, uuid4

from numpy import array, ndarray

from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding import OpenAITextEmbedding
from semantic_kernel.connectors.vectors.azure_ai_search.azure_ai_search_vector_record_store import (
    AzureAISearchVectorRecordStore,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.vectors.data_models.data_model_decorator import datamodel
from semantic_kernel.vectors.data_models.vector_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)


@datamodel
@dataclass
class MyDataModel:
    vector: Annotated[
        ndarray | None,
        VectorStoreRecordVectorField(embedding_settings={"embedding": {"dimensions": 1536}}),
    ] = None
    other: str | None = None
    id: Annotated[UUID, VectorStoreRecordKeyField()] = field(default_factory=uuid4)
    content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")] = (
        "content1"
    )

    def serialize(self) -> dict[str, Any]:
        return {
            "vector": self.vector.tolist(),
            "id": str(self.id),
            "content": self.content,
        }

    @classmethod
    def deserialize(cls, obj: dict[str, Any]):
        return cls(
            vector=array(obj["vector"]),
            id=UUID(obj["id"]),
            content=obj["content"],
        )


async def main():
    kernel = Kernel()
    kernel.add_service(OpenAITextEmbedding(service_id="embedding", ai_model_id="text-embedding-3-small"))
    async with AzureAISearchVectorRecordStore[MyDataModel](
        item_type=MyDataModel,
        collection_name=os.environ["ALT_SEARCH_INDEX_NAME"],
        search_endpoint=os.environ["ALT_SEARCH_ENDPOINT"],
        api_key=os.environ["ALT_SEARCH_API_KEY"],
    ) as record_store:
        record1 = MyDataModel(content="My text")
        record2 = MyDataModel(content="My other text")

        await record_store.upsert(record1, kernel=kernel)
        await record_store.upsert(record2, kernel=kernel)

        result = await record_store.get(record1.id)
        print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
