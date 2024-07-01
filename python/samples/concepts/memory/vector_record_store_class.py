# Copyright (c) Microsoft. All rights reserved.


import os
from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

from numpy import array

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding import OpenAITextEmbedding
from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_vector_record_store import (
    AzureAISearchVectorRecordStore,
)
from semantic_kernel.connectors.memory.qdrant.qdrant_vector_record_store import QdrantVectorRecordStore
from semantic_kernel.connectors.memory.redis.redis_vector_record_store import RedisVectorRecordStore
from semantic_kernel.data.models.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.models.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)


@vectorstoremodel
@dataclass
class MyDataModel:
    vector: Annotated[
        list[float] | None,
        VectorStoreRecordVectorField(
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
            # cast_function=array,
        ),
    ] = None
    other: str | None = None
    id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
    content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")] = (
        "content1"
    )


kernel = Kernel()


stores = {
    "ai_search": AzureAISearchVectorRecordStore[MyDataModel](
        data_model_type=MyDataModel,
        kernel=kernel,
        collection_name=os.environ["ALT_SEARCH_INDEX_NAME"],
        search_endpoint=os.environ["ALT_SEARCH_ENDPOINT"],
        api_key=os.environ["ALT_SEARCH_API_KEY"],
    ),
    "redis": RedisVectorRecordStore[MyDataModel](
        data_model_type=MyDataModel,
        kernel=kernel,
        collection_name="test",
        prefix_collection_name_to_key_names=True,
    ),
    "qdrant": QdrantVectorRecordStore[MyDataModel](data_model_type=MyDataModel, kernel=kernel, collection_name="test"),
}

store = "qdrant"
manual_embed = False


async def main():
    service_id = "embedding"
    ai_model_id = "text-embedding-3-small"
    kernel.add_service(OpenAITextEmbedding(service_id=service_id, ai_model_id=ai_model_id))
    async with stores[store] as record_store:
        record1 = MyDataModel(content="My text", id="e6103c03-487f-4d7d-9c23-4723651c17f4")
        record2 = MyDataModel(content="My other text", id="09caec77-f7e1-466a-bcec-f1d51c5b15be")

        if manual_embed:
            await kernel.add_embedding_to_object(
                inputs=[record1, record2],
                field_to_embed="content",
                field_to_store="vector",
                execution_settings={
                    service_id: OpenAIEmbeddingPromptExecutionSettings(
                        service_id=service_id, ai_model_id=ai_model_id, dimensions=1536
                    )
                },
                cast_function=array,
            )
            keys = await record_store.upsert_batch([record1, record2])
        else:
            keys = await record_store.upsert_batch([record1, record2], generate_embeddings=True)
        print(f"upserted {keys=}")

        result = await record_store.get(record1.id)
        print(f"found {result.id=}")
        print(f"{result.content=}")
        print(f"{result.vector[:5]=}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
