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
from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_collection import AzureAISearchCollection
from semantic_kernel.connectors.memory.qdrant.qdrant_collection import QdrantCollection
from semantic_kernel.connectors.memory.redis.redis_collection import RedisHashsetCollection, RedisJsonCollection
from semantic_kernel.connectors.memory.volatile.volatile_collection import VolatileCollection
from semantic_kernel.data.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.vector_store_record_utils import VectorStoreRecordUtils


@vectorstoremodel
@dataclass
class MyDataModelArray:
    vector: Annotated[
        np.ndarray | None,
        VectorStoreRecordVectorField(
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
            index_kind="hnsw",
            dimensions=1536,
            distance_function="cosine",
            property_type="float",
            serialize_function=np.ndarray.tolist,
            deserialize_function=np.array,
        ),
    ] = None
    other: str | None = None
    id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
    content: Annotated[
        str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
    ] = "content1"


@vectorstoremodel
@dataclass
class MyDataModelList:
    vector: Annotated[
        list[float] | None,
        VectorStoreRecordVectorField(
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
            index_kind="hnsw",
            dimensions=1536,
            distance_function="cosine",
            property_type="float",
        ),
    ] = None
    other: str | None = None
    id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
    content: Annotated[
        str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
    ] = "content1"


# configuration
# specify which store (redis_json, redis_hash, qdrant, Azure AI Search or volatile) to use
# and which model (vectors as list or as numpy arrays)
store = "volatile"
collection_name = "test"
MyDataModel = MyDataModelArray

stores: dict[str, VectorStoreRecordCollection] = {
    "ai_search": AzureAISearchCollection[MyDataModel](
        data_model_type=MyDataModel,
    ),
    "redis_json": RedisJsonCollection[MyDataModel](
        data_model_type=MyDataModel,
        collection_name=collection_name,
        prefix_collection_name_to_key_names=True,
    ),
    "redis_hashset": RedisHashsetCollection[MyDataModel](
        data_model_type=MyDataModel,
        collection_name=collection_name,
        prefix_collection_name_to_key_names=True,
    ),
    "qdrant": QdrantCollection[MyDataModel](
        data_model_type=MyDataModel, collection_name=collection_name, prefer_grpc=True, named_vectors=False
    ),
    "volatile": VolatileCollection[MyDataModel](
        data_model_type=MyDataModel,
        collection_name=collection_name,
    ),
}


async def main():
    kernel = Kernel()
    service_id = "embedding"
    ai_model_id = "text-embedding-3-small"
    kernel.add_service(OpenAITextEmbedding(service_id=service_id, ai_model_id=ai_model_id))
    async with stores[store] as record_store:
        await record_store.create_collection_if_not_exists()

        record1 = MyDataModel(content="My text", id="e6103c03-487f-4d7d-9c23-4723651c17f4")
        record2 = MyDataModel(content="My other text", id="09caec77-f7e1-466a-bcec-f1d51c5b15be")

        records = await VectorStoreRecordUtils(kernel).add_vector_to_records(
            [record1, record2], data_model_type=MyDataModel
        )
        keys = await record_store.upsert_batch(records)
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
