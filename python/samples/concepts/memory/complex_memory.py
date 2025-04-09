# Copyright (c) Microsoft. All rights reserved.

import argparse
import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated, Literal
from uuid import uuid4

import numpy as np

from samples.concepts.memory.utils import print_record
from samples.concepts.resources.utils import Colors, print_with_color
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    AzureTextEmbedding,
    OpenAIEmbeddingPromptExecutionSettings,
    OpenAITextEmbedding,
)
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchCollection
from semantic_kernel.connectors.memory.azure_cosmos_db import (
    AzureCosmosDBforMongoDBCollection,
    AzureCosmosDBNoSQLCollection,
)
from semantic_kernel.connectors.memory.chroma import ChromaCollection
from semantic_kernel.connectors.memory.faiss import FaissCollection
from semantic_kernel.connectors.memory.in_memory import InMemoryVectorCollection
from semantic_kernel.connectors.memory.pinecone import PineconeCollection
from semantic_kernel.connectors.memory.postgres import PostgresCollection
from semantic_kernel.connectors.memory.qdrant import QdrantCollection
from semantic_kernel.connectors.memory.redis import RedisHashsetCollection, RedisJsonCollection
from semantic_kernel.connectors.memory.sql_server import SqlServerCollection
from semantic_kernel.connectors.memory.weaviate import WeaviateCollection
from semantic_kernel.data import (
    VectorizableTextSearchMixin,
    VectorizedSearchMixin,
    VectorSearchFilter,
    VectorSearchOptions,
    VectorStoreRecordCollection,
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
    VectorTextSearchMixin,
    vectorstoremodel,
)
from semantic_kernel.data.const import DISTANCE_FUNCTION_DIRECTION_HELPER, DistanceFunction, IndexKind
from semantic_kernel.data.vector_search import add_vector_to_records

# This is a rather complex sample, showing how to use the vector store
# with a number of different collections.
# It also shows how to use the vector store with a number of different data models.
# It also uses all the types of search available in the vector store.
# For a simpler example, see "simple_memory.py"


def get_data_model(type: Literal["array", "list"], index_kind: IndexKind, distance_function: DistanceFunction) -> type:
    if type == "array":

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
            title: Annotated[str, VectorStoreRecordDataField(property_type="str", is_full_text_searchable=True)] = (
                "title"
            )
            tag: Annotated[str, VectorStoreRecordDataField(property_type="str", is_filterable=True)] = "tag"

        return DataModelArray

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
# Depending on the vector database, the index kind and distance function may need to be adjusted
# since not all combinations are supported by all databases.
# The values below might need to be changed for your collection to work.
distance_function = DistanceFunction.COSINE_DISTANCE
index_kind = IndexKind.FLAT
DataModel = get_data_model("array", index_kind, distance_function)

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
# - azure_cosmos_mongodb: Azure Cosmos MongoDB
#   https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/introduction
# - chroma: Chroma
#   The chroma collection is currently only available for in-memory versions
#   Client-Server mode and Chroma Cloud are not yet supported.
#   More info on Chroma here: https://docs.trychroma.com/docs/overview/introduction
# - faiss: Faiss - in-memory with optimized indexes.
# - pinecone: Pinecone
# - sql_server: SQL Server, can connect to any SQL Server compatible database, like Azure SQL.
# This is represented as a mapping from the collection name to a
# function which returns the collection.
# Using a function allows for lazy initialization of the collection,
# so that settings for unused collections do not cause validation errors.
collections: dict[str, Callable[[], VectorStoreRecordCollection]] = {
    "ai_search": lambda: AzureAISearchCollection[str, DataModel](
        data_model_type=DataModel,
    ),
    "postgres": lambda: PostgresCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
    "redis_json": lambda: RedisJsonCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
        prefix_collection_name_to_key_names=True,
    ),
    "redis_hash": lambda: RedisHashsetCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
        prefix_collection_name_to_key_names=True,
    ),
    "qdrant": lambda: QdrantCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
        prefer_grpc=True,
        named_vectors=False,
    ),
    "in_memory": lambda: InMemoryVectorCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
    "weaviate": lambda: WeaviateCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
    "azure_cosmos_nosql": lambda: AzureCosmosDBNoSQLCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
        create_database=True,
    ),
    "azure_cosmos_mongodb": lambda: AzureCosmosDBforMongoDBCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
    "faiss": lambda: FaissCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
    "chroma": lambda: ChromaCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
    "pinecone": lambda: PineconeCollection[str, DataModel](
        collection_name=collection_name,
        data_model_type=DataModel,
    ),
    "sql_server": lambda: SqlServerCollection[str, DataModel](
        data_model_type=DataModel,
        collection_name=collection_name,
    ),
}


async def cleanup(record_collection):
    print("-" * 30)
    delete = input("Do you want to delete the collection? (y/n): ")
    if delete.lower() != "y":
        print("Skipping deletion.")
        return
    print_with_color("Deleting collection!", Colors.CBLUE)
    await record_collection.delete_collection()
    print_with_color("Done!", Colors.CGREY)


async def main(collection: str, use_azure_openai: bool):
    print("-" * 30)
    kernel = Kernel()
    embedder = (
        AzureTextEmbedding(service_id="embedding") if use_azure_openai else OpenAITextEmbedding(service_id="embedding")
    )
    kernel.add_service(embedder)
    async with collections[collection]() as record_collection:
        print_with_color(f"Creating {collection} collection!", Colors.CGREY)
        # cleanup any existing collection
        await record_collection.delete_collection()
        # create a new collection
        await record_collection.create_collection()

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
        record3 = DataModel(
            content="```python\nfrom semantic_kernel import Kernel\nkernel = Kernel()\n```",
            id="d5c9913a-e015-4944-b960-5d4a84bca002",
            title="Code sample",
            tag="code",
        )

        print_with_color("Adding records!", Colors.CBLUE)
        records = await add_vector_to_records(kernel, [record1, record2, record3], data_model_type=DataModel)
        records = [record1, record2, record3]
        keys = await record_collection.upsert_batch(records)
        print(f"    Upserted {keys=}")
        print_with_color("Getting records!", Colors.CBLUE)
        results = await record_collection.get([record1.id, record2.id, record3.id])
        if results:
            [print_record(record=result) for result in results]
        else:
            print("Nothing found...")
        options = VectorSearchOptions(
            vector_field_name="vector",
            include_vectors=True,
            filter=VectorSearchFilter.equal_to("tag", "general"),
        )
        print("-" * 30)
        print_with_color("Now we can start searching.", Colors.CBLUE)
        print_with_color("  For each type of search, enter a search term, for instance `python`.", Colors.CBLUE)
        print_with_color("  Enter exit to exit, and skip or nothing to skip this search.", Colors.CBLUE)
        if isinstance(record_collection, VectorTextSearchMixin):
            search_text = input("Enter search text for text search: ")
            if search_text.lower() == "exit":
                await cleanup(record_collection)
                return
            if not search_text or search_text.lower() != "skip":
                print_with_color(f"Searching for '{search_text}', with filter 'tag == general'", Colors.CBLUE)
                print("-" * 30)
                print_with_color("Using text search", Colors.CBLUE)
                search_results = await record_collection.text_search(search_text, options)
                if search_results.total_count == 0:
                    print("\nNothing found...\n")
                else:
                    [print_record(result) async for result in search_results.results]
        if isinstance(record_collection, VectorizedSearchMixin):
            search_text = input("Enter search text for vector search: ")
            if search_text.lower() == "exit":
                await cleanup(record_collection)
                return
            if not search_text or search_text.lower() != "skip":
                vector = (await embedder.generate_raw_embeddings([search_text]))[0]
                print_with_color(f"Vector of search text (first five): {vector[:5]}", Colors.CBLUE)
                print("-" * 30)
                print_with_color(
                    f"Using vectorized search, for {distance_function.value}, "
                    f"the {'higher' if DISTANCE_FUNCTION_DIRECTION_HELPER[distance_function](1, 0) else 'lower'} the score the better"  # noqa: E501
                    f"",
                    Colors.CBLUE,
                )
                search_results = await record_collection.vectorized_search(
                    vector=vector,
                    options=options,
                )
                if search_results.total_count == 0:
                    print("\nNothing found...\n")
                else:
                    [print_record(result) async for result in search_results.results]
        if isinstance(record_collection, VectorizableTextSearchMixin):
            search_text = input("Enter search text for vectorizable text search: ")
            if search_text.lower() == "exit":
                await cleanup(record_collection)
                return
            if not search_text or search_text.lower() != "skip":
                print("-" * 30)
                print_with_color(
                    f"Using vectorizable text search, for {distance_function.value}, "
                    f"the {'higher' if DISTANCE_FUNCTION_DIRECTION_HELPER[distance_function](1, 0) else 'lower'} the score the better",  # noqa: E501
                    Colors.CBLUE,
                )
                try:
                    search_results = await record_collection.vectorizable_text_search(search_text, options)
                    if search_results.total_count == 0:
                        print("\nNothing found...\n")
                    else:
                        [print_record(result) async for result in search_results.results]
                except Exception as e:
                    print(f"Error: {e}")
        await cleanup(record_collection)


if __name__ == "__main__":
    argparse.ArgumentParser()

    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", default="in_memory", choices=collections.keys(), help="What collection to use.")
    # Option of whether to use OpenAI or Azure OpenAI.
    parser.add_argument("--use-azure-openai", action="store_true", help="Use Azure OpenAI instead of OpenAI.")
    args = parser.parse_args()
    asyncio.run(main(collection=args.collection, use_azure_openai=args.use_azure_openai))
