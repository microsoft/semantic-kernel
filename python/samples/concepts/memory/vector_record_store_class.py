# Copyright (c) Microsoft. All rights reserved.


from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

import numpy as np

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding import OpenAITextEmbedding
from semantic_kernel.connectors.memory.redis.redis_collection import RedisHashsetCollection, RedisJsonCollection
from semantic_kernel.data.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)


@vectorstoremodel
@dataclass
class MyDataModel:
    vector: Annotated[
        np.ndarray | None,
        VectorStoreRecordVectorField(
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
            index_kind="hnsw",
            dimensions=1536,
            distance_function="cosine",
            property_type="ndarray",
            cast_function=lambda x: np.frombuffer(x),
        ),
    ] = None
    other: str | None = None
    id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
    content: Annotated[
        str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
    ] = "content1"


kernel = Kernel()


stores = {
    "redis": RedisJsonCollection[MyDataModel](
        data_model_type=MyDataModel,
        collection_name="test",
        prefix_collection_name_to_key_names=True,
    ),
    "redis_hashset": RedisHashsetCollection[MyDataModel](
        data_model_type=MyDataModel,
        collection_name="test_hashset",
        prefix_collection_name_to_key_names=True,
    ),
    # "ai_search": AzureAISearchCollection[MyDataModel](
    #     data_model_type=MyDataModel,
    # ),
    # "qdrant": QdrantCollection[MyDataModel](data_model_type=MyDataModel, collection_name="test", prefer_grpc=True),
}

store = "redis_hashset"
manual_embed = True


async def main():
    service_id = "embedding"
    ai_model_id = "text-embedding-3-small"
    kernel.add_service(OpenAITextEmbedding(service_id=service_id, ai_model_id=ai_model_id))
    async with stores[store] as record_store:
        await record_store.create_collection_if_not_exists()

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
                cast_function=lambda x: np.array(x),
            )
            keys = await record_store.upsert_batch([record1, record2])
        else:
            keys = await record_store.upsert_batch([record1, record2], generate_embeddings=True)
        print(f"upserted {keys=}")

        results = await record_store.get_batch([record1.id, record2.id])
        if results:
            for result in results:
                print(f"found {result.id=}")
                print(f"{result.content=}")
                if result.vector is not None:
                    print(f"{result.vector[:5]=}")
        else:
            print("not found")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
