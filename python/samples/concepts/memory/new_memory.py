# Copyright (c) Microsoft. All rights reserved.

import argparse
import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

import numpy as np

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    AzureTextEmbedding,
    OpenAIEmbeddingPromptExecutionSettings,
    OpenAITextEmbedding,
)
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchCollection
from semantic_kernel.connectors.memory.azure_cosmos_db import AzureCosmosDBNoSQLCollection
from semantic_kernel.connectors.memory.in_memory import InMemoryVectorCollection
from semantic_kernel.connectors.memory.postgres import PostgresCollection
from semantic_kernel.connectors.memory.qdrant import QdrantCollection
from semantic_kernel.connectors.memory.redis import RedisHashsetCollection, RedisJsonCollection
from semantic_kernel.connectors.memory.weaviate import WeaviateCollection
from semantic_kernel.data import (
    DistanceFunction,
    IndexKind,
    VectorizableTextSearchMixin,
    VectorizedSearchMixin,
    VectorSearchFilter,
    VectorSearchOptions,
    VectorSearchResult,
    VectorStoreRecordCollection,
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordUtils,
    VectorStoreRecordVectorField,
    VectorTextSearchMixin,
    vectorstoremodel,
)


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
        id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
        content: Annotated[
            str,
            VectorStoreRecordDataField(
                has_embedding=True,
                embedding_property_name="vector",
                property_type="str",
                is_full_text_searchable=True,
            ),
        ] = "content1"
        title: Annotated[str, VectorStoreRecordDataField(property_type="str", is_full_text_searchable=True)] = "title"
        tag: Annotated[str, VectorStoreRecordDataField(property_type="str", is_filterable=True)] = "tag"

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
        id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
        content: Annotated[
            str,
            VectorStoreRecordDataField(
                has_embedding=True,
                embedding_property_name="vector",
                property_type="str",
                is_full_text_searchable=True,
            ),
        ] = "content1"
        title: Annotated[str, VectorStoreRecordDataField(property_type="str", is_full_text_searchable=True)] = "title"
        tag: Annotated[str, VectorStoreRecordDataField(property_type="str", is_filterable=True)] = "tag"

    return DataModelList


collection_name = "test"
# Depending on the vector database, the index kind and distance function may need to be adjusted,
# since not all combinations are supported by all databases.
DataModel = get_data_model_array(IndexKind.HNSW, DistanceFunction.COSINE_SIMILARITY)

# A list of VectorStoreRecordCollection that can be used.
# Available collections are:
# - ai_search: Azure AI Search
# - postgres: PostgreSQL
# - redis_json: Redis JSON
# - redis_hashset: Redis Hashset
# - qdrant: Qdrant
# - in_memory: In-memory store
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
    "redis_hash": lambda: RedisHashsetCollection[DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
        prefix_collection_name_to_key_names=True,
    ),
    "qdrant": lambda: QdrantCollection[DataModel](
        data_model_type=DataModel, collection_name=collection_name, prefer_grpc=True, named_vectors=False
    ),
    "in_memory": lambda: InMemoryVectorCollection[DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
    "weaviate": lambda: WeaviateCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
    "azure_cosmos_nosql": lambda: AzureCosmosDBNoSQLCollection(
        data_model_type=DataModel,
        collection_name=collection_name,
        create_database=True,
    ),
}


def print_record(result: VectorSearchResult | None = None, record: DataModel | None = None):
    if result:
        record = result.record
    print(f"  Found id: {record.id}")
    print(f"    Content: {record.content}")
    if record.vector is not None:
        print(f"    Vector (first five): {record.vector[:5]}")


async def main(collection: str, use_azure_openai: bool, embedding_model: str):
    print("-" * 30)
    kernel = Kernel()
    service_id = "embedding"
    if use_azure_openai:
        embedder = AzureTextEmbedding(service_id=service_id, deployment_name=embedding_model)
    else:
        embedder = OpenAITextEmbedding(service_id=service_id, ai_model_id=embedding_model)
    kernel.add_service(embedder)
    async with collections[collection]() as record_collection:
        print(f"Creating {collection} collection!")
        await record_collection.delete_collection()
        await record_collection.create_collection_if_not_exists()

        record1 = DataModel(
            content="Semantic Kernel is awesome",
            id="e6103c03-487f-4d7d-9c23-4723651c17f4",
            title="Overview",
            tag="general",
        )
        record2 = DataModel(
            content="Semantic Kernel is available in dotnet, python and Java.",
            id="09caec77-f7e1-466a-bcec-f1d51c5b15be",
            title="Semantic Kernel Languages",
            tag="general",
        )

        print("Adding records!")
        records = await VectorStoreRecordUtils(kernel).add_vector_to_records(
            [record1, record2], data_model_type=DataModel
        )

        keys = await record_collection.upsert_batch(records)
        print(f"    Upserted {keys=}")
        print("Getting records!")
        results = await record_collection.get_batch([record1.id, record2.id])
        if results:
            [print_record(record=result) for result in results]
        else:
            print("Nothing found...")
        options = VectorSearchOptions(
            vector_field_name="vector",
            include_vectors=True,
            filter=VectorSearchFilter.equal_to("tag", "general"),
        )
        if isinstance(record_collection, VectorTextSearchMixin):
            print("-" * 30)
            print("Using text search")
            try:
                search_results = await record_collection.text_search("python", options)
                if search_results.total_count == 0:
                    print("\nNothing found...\n")
                else:
                    [print_record(result) async for result in search_results.results]
            except Exception:
                print("Text search could not execute.")
        if isinstance(record_collection, VectorizedSearchMixin):
            print("-" * 30)
            print(
                "Using vectorized search, depending on the distance function, "
                "the better score might be higher or lower."
            )
            try:
                search_results = await record_collection.vectorized_search(
                    vector=(await embedder.generate_raw_embeddings(["python"]))[0],
                    options=VectorSearchOptions(vector_field_name="vector", include_vectors=True),
                )
                if search_results.total_count == 0:
                    print("\nNothing found...\n")
                else:
                    [print_record(result) async for result in search_results.results]
            except Exception:
                print("Vectorized search could not execute.")
        if isinstance(record_collection, VectorizableTextSearchMixin):
            print("-" * 30)
            print("Using vectorizable text search")
            try:
                search_results = await record_collection.vectorizable_text_search("python", options)
                if search_results.total_count == 0:
                    print("\nNothing found...\n")
                else:
                    [print_record(result) async for result in search_results.results]
            except Exception:
                print("Vectorizable text search could not execute.")
        print("-" * 30)
        print("Deleting collection!")
        await record_collection.delete_collection()
        print("Done!")


if __name__ == "__main__":
    argparse.ArgumentParser()

    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", default="in_memory", choices=collections.keys(), help="What collection to use.")
    # Option of whether to use OpenAI or Azure OpenAI.
    parser.add_argument("--use-azure-openai", action="store_true", help="Use Azure OpenAI instead of OpenAI.")
    # Model
    parser.add_argument(
        "--model", default="text-embedding-3-small", help="The model or deployment to use for embeddings."
    )
    args = parser.parse_args()

    asyncio.run(main(collection=args.collection, use_azure_openai=args.use_azure_openai, embedding_model=args.model))
