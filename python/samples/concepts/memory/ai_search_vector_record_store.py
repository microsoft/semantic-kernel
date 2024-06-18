# Copyright (c) Microsoft. All rights reserved.


import os
from dataclasses import dataclass, field
from typing import Annotated
from uuid import UUID, uuid4

from numpy import ndarray

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding import OpenAITextEmbedding
from semantic_kernel.connectors.data.azure_ai_search.azure_ai_search_vector_record_store import (
    AzureAISearchVectorRecordStore,
)
from semantic_kernel.data.data_models.data_model_decorator import datamodel
from semantic_kernel.data.data_models.vector_record_fields import (
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
