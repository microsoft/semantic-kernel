# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.storage.data_entry import DataEntry
from semantic_kernel.memory.storage.data_store_base import DataStoreBase

if TYPE_CHECKING:
    import chromadb
    import chromadb.config
    from chromadb.api.models.Collection import Collection
    from chromadb.api.types import QueryResult


def camel_to_snake(camel_str):
    snake_str = camel_str[0].lower()
    for char in camel_str[1:]:
        if char.isupper():
            snake_str += "_" + char.lower()
        else:
            snake_str += char
    return snake_str


class ChromaDataStore(DataStoreBase):
    """
    ChromaDataStore provides an interface to store and retrieve data using ChromaDB.
    This implementation does not use ChromaDB's built-in embedding function, as embeddings are directly provided from SemanticTextMemory.
    Collection names with uppercase characters are not supported by ChromaDB, they will be automatically converted.

    Args:
        persist_directory (Optional[str], optional): Path to the directory where data will be persisted.
            Defaults to None, which means the default settings for ChromaDB will be used.
        client_settings (Optional["chromadb.config.Settings"], optional): A Settings instance to configure
            the ChromaDB client. Defaults to None, which means the default settings for ChromaDB will be used.

    Example:
        # Create a ChromaDataStore with a local specified directory for data persistence
        chroma_local_data_store = ChromaDataStore(persist_directory='/path/to/persist/directory')

        # Create a ChromaDataStore with a custom Settings instance
        chroma_remote_data_store = ChromaDataStore(
            client_settings=Settings(
                chroma_api_impl="rest",
                chroma_server_host="xxx.xxx.xxx.xxx",
                chroma_server_http_port="8000"
            )
        )
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        client_settings: Optional["chromadb.config.Settings"] = None,
    ) -> None:
        try:
            import chromadb
            import chromadb.config

        except ImportError:
            raise ValueError(
                "Could not import chromadb python package. "
                "Please install it with `pip install chromadb`."
            )

        if client_settings:
            self._client_settings = client_settings
        else:
            self._client_settings = chromadb.config.Settings()
            if persist_directory is not None:
                self._client_settings = chromadb.config.Settings(
                    chroma_db_impl="duckdb+parquet", persist_directory=persist_directory
                )
        self._client = chromadb.Client(self._client_settings)
        self._persist_directory = persist_directory
        # ChromaDataStore will get embeddings from SemanticTextMemory. Never use this.
        self._default_embdding_function = "DoNotUseChromaEmbeddingFunction"
        self._default_query_includes = ["embeddings", "metadatas", "documents"]

    async def get_collection_async(self, collection: str) -> Optional["Collection"]:
        try:
            # Current version of ChromeDB reject camel case collection names.
            collection_snake_case = camel_to_snake(collection)
            return self._client.get_collection(
                name=collection_snake_case,
                embedding_function=self._default_embdding_function,
            )
        except ValueError:
            return None

    async def get_collections_async(self) -> List[str]:
        return [collection.name for collection in self._client.list_collections()]

    async def get_all_async(self, collection: str) -> List[DataEntry]:
        collection = self.get_collection_async(collection)
        if collection is None:
            return []

        values = collection.get(include=self._default_query_includes)
        records = self.query_results_to_memory_records(values)

        entries = [
            DataEntry(
                key=values["ids"][i][0],
                value=record,
                timestamp=datetime.fromtimestamp(
                    values["metadatas"][i][0]["timestamp"]
                ),
            )
            for i, record in enumerate(records)
        ]

        return entries

    async def get_async(self, collection: str, key: str) -> Optional[DataEntry]:
        collection = self._client.get_collection(name=collection)
        if collection is None:
            return None

        value = collection.get(ids=key, include=self._default_query_includes)
        record = self.query_results_to_memory_records(value)[0]
        timestamp = datetime.fromtimestamp(value["metadatas"][0]["timestamp"])

        return DataEntry(key=key, value=record, timestamp=timestamp)

    async def put_async(self, collection: str, value: DataEntry) -> DataEntry:
        record: MemoryRecord = value.value
        collection: Collection = self._client.get_or_create_collection(
            name=camel_to_snake(collection),
            embedding_function=self._default_embdding_function,
        )
        collection.add(
            metadatas={
                "timestamp": value.timestamp.timestamp(),
                "is_reference": record.is_reference,
                "external_source_name": record.external_source_name or "",
                "description": record.description or "",
            },
            # by providing embeddings, we can skip the chroma's embedding function call
            embeddings=record.embedding.tolist(),
            documents=record.text,
            ids=value.key,
        )

        return value

    async def remove_async(self, collection: str, key: str) -> None:
        collection = self._client.get_collection(name=collection)
        if collection is None:
            return None
        collection.delete(ids=[key])

    async def get_value_async(self, collection: str, key: str) -> MemoryRecord:
        entry = await self.get_async(collection, key)

        if entry is None:
            # TODO: equivalent here?
            raise Exception(f"Key '{key}' not found in collection '{collection}'")

        return entry.value

    async def put_value_async(
        self, collection: str, key: str, value: MemoryRecord
    ) -> None:
        await self.put_async(collection, DataEntry(key, value, datetime.now()))

    def query_results_to_memory_records(
        self, results: "QueryResult"
    ) -> List[MemoryRecord]:
        memory_records = [
            (
                MemoryRecord(
                    id=id,
                    text=document,
                    embedding=embedding,
                    is_reference=metadata["is_reference"],
                    external_source_name=metadata["external_source_name"],
                    description=metadata["description"],
                )
            )
            for id, document, embedding, metadata in zip(
                results["ids"][0],
                results["documents"][0],
                results["embeddings"][0],
                results["metadatas"][0],
            )
        ]
        return memory_records
