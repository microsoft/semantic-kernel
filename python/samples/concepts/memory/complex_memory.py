# Copyright (c) Microsoft. All rights reserved.

import argparse
import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

from samples.concepts.memory.utils import print_record
from samples.concepts.resources.utils import Colors, print_with_color
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding, OpenAITextEmbedding
from semantic_kernel.connectors.memory import (
    AzureAISearchCollection,
    ChromaCollection,
    CosmosMongoCollection,
    CosmosNoSqlCollection,
    FaissCollection,
    InMemoryCollection,
    PineconeCollection,
    PostgresCollection,
    QdrantCollection,
    RedisHashsetCollection,
    RedisJsonCollection,
    SqlServerCollection,
    WeaviateCollection,
)
from semantic_kernel.data.vector import (
    SearchType,
    VectorSearchProtocol,
    VectorStoreCollection,
    VectorStoreField,
    vectorstoremodel,
)

# This is a rather complex sample, showing how to use the vector store
# with a number of different collections.
# It also shows how to use the vector store with a number of different data models.
# It also uses all the types of search available in the vector store.
# For a simpler example, see "simple_memory.py"


# Depending on the vector database, the index kind and distance function may need to be adjusted
# since not all combinations are supported by all databases.
# The values below might need to be changed for your collection to work.
@vectorstoremodel(collection_name="test")
@dataclass
class DataModel:
    title: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)]
    content: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)]
    embedding: Annotated[
        list[float] | str | None,
        VectorStoreField("vector", dimensions=1536, type="float"),
    ] = None
    id: Annotated[
        str,
        VectorStoreField(
            "key",
        ),
    ] = field(default_factory=lambda: str(uuid4()))
    tag: Annotated[str | None, VectorStoreField("data", type="str", is_indexed=True)] = None

    def __post_init__(self, **kwargs):
        if self.embedding is None:
            self.embedding = f"{self.title} {self.content}"
        if self.tag is None:
            self.tag = "general"


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
collections: dict[str, Callable[[], VectorStoreCollection]] = {
    "ai_search": lambda: AzureAISearchCollection[str, DataModel](record_type=DataModel),
    "postgres": lambda: PostgresCollection[str, DataModel](record_type=DataModel),
    "redis_json": lambda: RedisJsonCollection[str, DataModel](
        record_type=DataModel,
        prefix_collection_name_to_key_names=True,
    ),
    "redis_hash": lambda: RedisHashsetCollection[str, DataModel](
        record_type=DataModel,
        prefix_collection_name_to_key_names=True,
    ),
    "qdrant": lambda: QdrantCollection[str, DataModel](
        record_type=DataModel,
        prefer_grpc=True,
        named_vectors=False,
    ),
    "in_memory": lambda: InMemoryCollection[str, DataModel](record_type=DataModel),
    "weaviate": lambda: WeaviateCollection[str, DataModel](record_type=DataModel),
    "azure_cosmos_nosql": lambda: CosmosNoSqlCollection[str, DataModel](
        record_type=DataModel,
        create_database=True,
    ),
    "azure_cosmos_mongodb": lambda: CosmosMongoCollection[str, DataModel](record_type=DataModel),
    "faiss": lambda: FaissCollection[str, DataModel](record_type=DataModel),
    "chroma": lambda: ChromaCollection[str, DataModel](record_type=DataModel),
    "pinecone": lambda: PineconeCollection[str, DataModel](record_type=DataModel),
    "sql_server": lambda: SqlServerCollection[str, DataModel](record_type=DataModel),
}


async def cleanup(record_collection):
    print("-" * 30)
    delete = input("Do you want to delete the collection? (y/n): ")
    if delete.lower() != "y":
        print("Skipping deletion.")
        return
    print_with_color("Deleting collection!", Colors.CBLUE)
    await record_collection.ensure_collection_deleted()
    print_with_color("Done!", Colors.CGREY)


async def main(collection: str, use_azure_openai: bool):
    print("-" * 30)
    kernel = Kernel()
    embedder = (
        AzureTextEmbedding(service_id="embedding") if use_azure_openai else OpenAITextEmbedding(service_id="embedding")
    )
    kernel.add_service(embedder)
    async with collections[collection]() as record_collection:
        assert isinstance(record_collection, VectorSearchProtocol)  # nosec
        record_collection.embedding_generator = embedder
        print_with_color(f"Creating {collection} collection!", Colors.CGREY)
        # cleanup any existing collection
        await record_collection.ensure_collection_deleted()
        # create a new collection
        await record_collection.create_collection()

        record1 = DataModel(
            content="Semantic Kernel is awesome",
            id="e6103c03-487f-4d7d-9c23-4723651c17f4",
            title="Overview",
        )
        record2 = DataModel(
            content="Semantic Kernel is available in dotnet, python and Java.",
            id="09caec77-f7e1-466a-bcec-f1d51c5b15be",
            title="Semantic Kernel Languages",
        )
        record3 = DataModel(
            content="```python\nfrom semantic_kernel import Kernel\nkernel = Kernel()\n```",
            id="d5c9913a-e015-4944-b960-5d4a84bca002",
            title="Code sample",
            tag="code",
        )

        print_with_color("Adding records!", Colors.CBLUE)
        records = [record1, record2, record3]
        keys = await record_collection.upsert(records)
        print(f"    Upserted {keys=}")
        print_with_color("Getting records!", Colors.CBLUE)
        results = await record_collection.get(top=10, order_by="content")
        if results:
            [print_record(record=result) for result in results]
        else:
            print("Nothing found...")
        options = {
            "vector_property_name": "embedding",
            "additional_property_name": "content",
            "filter": lambda x: x.tag == "general",
        }

        print("-" * 30)
        print_with_color("Now we can start searching.", Colors.CBLUE)
        print_with_color("  For each type of search, enter a search term, for instance `python`.", Colors.CBLUE)
        print_with_color("  Enter exit to exit, and skip or nothing to skip this search.", Colors.CBLUE)
        print("-" * 30)
        print_with_color(
            "This collection supports the following search types: "
            f"{', '.join(search.value for search in record_collection.supported_search_types)}",
            Colors.CBLUE,
        )
        if SearchType.KEYWORD_HYBRID in record_collection.supported_search_types:
            search_text = input("Enter search text for hybrid text search: ")
            if search_text.lower() == "exit":
                await cleanup(record_collection)
                return
            if search_text and search_text.lower() != "skip":
                print("-" * 30)
                print_with_color(
                    "Using hybrid text search: ",
                    Colors.CBLUE,
                )
                search_results = await record_collection.hybrid_search(values=search_text, **options)
                if search_results.total_count == 0:
                    print("\nNothing found...\n")
                else:
                    [print_record(result) async for result in search_results.results]
                print("-" * 30)

        if SearchType.VECTOR in record_collection.supported_search_types:
            search_text = input("Enter search text for vector search: ")
            if search_text.lower() == "exit":
                await cleanup(record_collection)
                return
            if search_text and search_text.lower() != "skip":
                print("-" * 30)
                print_with_color(
                    "Using vector search: ",
                    Colors.CBLUE,
                )
                search_results = await record_collection.search(search_text, **options)
                if search_results.total_count == 0:
                    print("\nNothing found...\n")
                else:
                    [print_record(result) async for result in search_results.results]
                print("-" * 30)
            await cleanup(record_collection)


if __name__ == "__main__":
    argparse.ArgumentParser()

    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", default="in_memory", choices=collections.keys(), help="What collection to use.")
    # Option of whether to use OpenAI or Azure OpenAI.
    parser.add_argument("--use-azure-openai", action="store_true", help="Use Azure OpenAI instead of OpenAI.")
    args = parser.parse_args()
    args.collection = "ai_search"
    asyncio.run(main(collection=args.collection, use_azure_openai=args.use_azure_openai))
