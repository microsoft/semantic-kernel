# Copyright (c) Microsoft. All rights reserved.

import argparse
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

import numpy as np

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIEmbeddingPromptExecutionSettings, OpenAITextEmbedding
from semantic_kernel.connectors.ai.open_ai.services.azure_text_embedding import AzureTextEmbedding
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchCollection
from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_collection import (
    AzureCosmosDBNoSQLCollection,
)
from semantic_kernel.connectors.memory.postgres.postgres_collection import PostgresCollection
from semantic_kernel.connectors.memory.qdrant import QdrantCollection
from semantic_kernel.connectors.memory.redis import RedisHashsetCollection, RedisJsonCollection
from semantic_kernel.connectors.memory.volatile import VolatileCollection
from semantic_kernel.connectors.memory.weaviate.weaviate_collection import WeaviateCollection
from semantic_kernel.data import (
    VectorStoreRecordCollection,
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordUtils,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)
from semantic_kernel.data.const import DistanceFunction, IndexKind


def get_data_model_array(index_kind: IndexKind, distance_function: DistanceFunction) -> type:
    @vectorstoremodel
    @dataclass
    class DataModelArray:
        vector: Annotated[
            np.ndarray | None,
            VectorStoreRecordVectorField(
                embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
                index_kind=index_kind,
                dimensions=1536,
                distance_function=distance_function,
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

    return DataModelArray


def get_data_model_list(index_kind: IndexKind, distance_function: DistanceFunction) -> type:
    @vectorstoremodel
    @dataclass
    class DataModelList:
        vector: Annotated[
            list[float] | None,
            VectorStoreRecordVectorField(
                embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
                index_kind=index_kind,
                dimensions=1536,
                distance_function=distance_function,
                property_type="float",
            ),
        ] = None
        other: str | None = None
        id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
        content: Annotated[
            str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
        ] = "content1"

    return DataModelList


collection_name = "test"
# Depending on the vector database, the index kind and distance function may need to be adjusted,
# since not all combinations are supported by all databases.
DataModel = get_data_model_array(IndexKind.HNSW, DistanceFunction.COSINE)

# A list of VectorStoreRecordCollection that can be used.
# Available collections are:
# - ai_search: Azure AI Search
# - postgres: PostgreSQL
# - redis_json: Redis JSON
# - redis_hashset: Redis Hashset
# - qdrant: Qdrant
# - volatile: In-memory store
# - weaviate: Weaviate
#   Please either configure the weaviate settings via environment variables or provide them through the constructor.
#   Note that embed mode is not supported on Windows: https://github.com/weaviate/weaviate/issues/3315
# - azure_cosmos_nosql: Azure Cosmos NoSQL
#   https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/how-to-create-account?tabs=azure-portal
#   Please see the link above to learn how to set up an Azure Cosmos NoSQL account.
#   https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-develop-emulator?tabs=windows%2Cpython&pivots=api-nosql
#   Please see the link above to learn how to set up the Azure Cosmos NoSQL emulator on your machine.
#   For this sample to work with Azure Cosmos NoSQL, please adjust the index_kind of the data model to QUANTIZED_FLAT.
# This is represented as a mapping from the collection name to a
# function which returns the collection.
# Using a function allows for lazy initialization of the collection,
# so that settings for unused collections do not cause validation errors.
collections: dict[str, Callable[[], VectorStoreRecordCollection]] = {
    "ai_search": lambda: AzureAISearchCollection[DataModel](
        data_model_type=DataModel,
    ),
    "postgres": lambda: PostgresCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
    "redis_json": lambda: RedisJsonCollection[DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
        prefix_collection_name_to_key_names=True,
    ),
    "redis_hashset": lambda: RedisHashsetCollection[DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
        prefix_collection_name_to_key_names=True,
    ),
    "qdrant": lambda: QdrantCollection[DataModel](
        data_model_type=DataModel, collection_name=collection_name, prefer_grpc=True, named_vectors=False
    ),
    "volatile": lambda: VolatileCollection[DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
    "weaviate": lambda: WeaviateCollection[DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
    "azure_cosmos_nosql": lambda: AzureCosmosDBNoSQLCollection(
        data_model_type=DataModel,
        database_name="sample_database",
        collection_name=collection_name,
        create_database=True,
    ),
}


async def main(collection: str, use_azure_openai: bool, embedding_model: str):
    kernel = Kernel()
    service_id = "embedding"
    if use_azure_openai:
        kernel.add_service(AzureTextEmbedding(service_id=service_id, deployment_name=embedding_model))
    else:
        kernel.add_service(OpenAITextEmbedding(service_id=service_id, ai_model_id=embedding_model))
    async with collections[collection]() as record_collection:
        await record_collection.create_collection_if_not_exists()

        record1 = DataModel(content="My text", id="e6103c03-487f-4d7d-9c23-4723651c17f4")
        record2 = DataModel(content="My other text", id="09caec77-f7e1-466a-bcec-f1d51c5b15be")

        records = await VectorStoreRecordUtils(kernel).add_vector_to_records(
            [record1, record2], data_model_type=DataModel
        )
        keys = await record_collection.upsert_batch(records)
        print(f"upserted {keys=}")

        results = await record_collection.get_batch([record1.id, record2.id])
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

    argparse.ArgumentParser()

    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", default="volatile", choices=collections.keys(), help="What collection to use.")
    # Option of whether to use OpenAI or Azure OpenAI.
    parser.add_argument("--use-azure-openai", action="store_true", help="Use Azure OpenAI instead of OpenAI.")
    # Model
    parser.add_argument(
        "--model", default="text-embedding-3-small", help="The model or deployment to use for embeddings."
    )
    args = parser.parse_args()

    asyncio.run(main(collection=args.collection, use_azure_openai=args.use_azure_openai, embedding_model=args.model))
