# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, List, Optional, Tuple

from numpy import array, ndarray

from semantic_kernel.connectors.memory.chroma.utils import (
    camel_to_snake,
    chroma_compute_similarity_scores,
    query_results_to_records,
)
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger

if TYPE_CHECKING:
    import chromadb
    import chromadb.config
    from chromadb.api.models.Collection import Collection


class ChromaMemoryStore(MemoryStoreBase):
    _client: "chromadb.Client"
    _logger: Logger

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        client_settings: Optional["chromadb.config.Settings"] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        ChromaMemoryStore provides an interface to store and retrieve data using ChromaDB.
        Collection names with uppercase characters are not supported by ChromaDB, they will be automatically converted.

        Args:
            persist_directory (Optional[str], optional): Path to the directory where data will be persisted.
                Defaults to None, which means the default settings for ChromaDB will be used.
            client_settings (Optional["chromadb.config.Settings"], optional): A Settings instance to configure
                the ChromaDB client. Defaults to None, which means the default settings for ChromaDB will be used.
            similarity_fetch_limit (int, optional): The maximum number of results to calculate cosine-similarity.
        Example:
            # Create a ChromaMemoryStore with a local specified directory for data persistence
            chroma_local_data_store = ChromaMemoryStore(persist_directory='/path/to/persist/directory')
            # Create a ChromaMemoryStore with a custom Settings instance
            chroma_remote_data_store = ChromaMemoryStore(
                client_settings=Settings(
                    chroma_api_impl="rest",
                    chroma_server_host="xxx.xxx.xxx.xxx",
                    chroma_server_http_port="8000"
                )
            )
        """
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
                    is_persistent=True, persist_directory=persist_directory
                )
        self._client = chromadb.Client(self._client_settings)
        self._persist_directory = persist_directory
        self._default_query_includes = ["embeddings", "metadatas", "documents"]

        self._logger = logger or NullLogger()
        self._default_embedding_function = "DisableChromaEmbeddingFunction"

    async def create_collection_async(self, collection_name: str) -> None:
        """Creates a new collection in Chroma if it does not exist.
            To prevent downloading model file from embedding_function,
            embedding_function is set to "DoNotUseChromaEmbeddingFunction".

        Arguments:
            collection_name {str} -- The name of the collection to create.
            The name of the collection will be converted to snake case.

        Returns:
            None
        """
        self._client.create_collection(
            # Current version of ChromeDB reject camel case collection names.
            name=camel_to_snake(collection_name),
            # ChromaMemoryStore will get embeddings from SemanticTextMemory. Never use this.
            embedding_function=self._default_embedding_function,
        )

    async def get_collection_async(
        self, collection_name: str
    ) -> Optional["Collection"]:
        try:
            # Current version of ChromeDB rejects camel case collection names.
            return self._client.get_collection(
                name=camel_to_snake(collection_name),
                embedding_function=self._default_embedding_function,
            )
        except ValueError:
            return None

    async def get_collections_async(self) -> List[str]:
        """Gets the list of collections.

        Returns:
            List[str] -- The list of collections.
        """
        return [collection.name for collection in self._client.list_collections()]

    async def delete_collection_async(self, collection_name: str) -> None:
        """Deletes a collection.

        Arguments:
            collection_name {str} -- The name of the collection to delete.

        Returns:
            None
        """
        # Current version of ChromeDB reject camel case collection names.
        self._client.delete_collection(name=camel_to_snake(collection_name))

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to check.

        Returns:
            bool -- True if the collection exists; otherwise, False.
        """
        if await self.get_collection_async(collection_name) is None:
            return False
        else:
            return True

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """Upserts a single MemoryRecord.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the record into.
            records {MemoryRecord} -- The record to upsert.

        Returns:
            List[str] -- The unique database key of the record.
        """
        collection = await self.get_collection_async(collection_name)
        if collection is None:
            raise Exception(f"Collection '{collection_name}' does not exist")

        record._key = record._id
        metadata = {
            "timestamp": record._timestamp or "",
            "is_reference": str(record._is_reference),
            "external_source_name": record._external_source_name or "",
            "description": record._description or "",
            "additional_metadata": record._additional_metadata or "",
            "id": record._id or "",
        }

        collection.add(
            metadatas=metadata,
            # by providing embeddings, we can skip the chroma's embedding function call
            embeddings=record.embedding.tolist(),
            documents=record._text,
            ids=record._key,
        )
        return record._key

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        """Upserts a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the records into.
            records {List[MemoryRecord]} -- The records to upsert.

        Returns:
            List[str] -- The unique database keys of the records. In Pinecone, these are the record IDs.
        """
        # upsert_async is checking collection existence
        return [await self.upsert_async(collection_name, record) for record in records]

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool
    ) -> MemoryRecord:
        """Gets a record.

        Arguments:
            collection_name {str} -- The name of the collection to get the record from.
            key {str} -- The unique database key of the record.
            with_embedding {bool} -- Whether to include the embedding in the result. (default: {False})

        Returns:
            MemoryRecord -- The record.
        """
        records = await self.get_batch_async(collection_name, [key], with_embedding)
        try:
            return records[0]
        except IndexError:
            raise Exception(
                f"Record with key '{key}' does not exist in collection '{collection_name}'"
            )

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool
    ) -> List[MemoryRecord]:
        """Gets a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to get the records from.
            keys {List[str]} -- The unique database keys of the records.
            with_embeddings {bool} -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[MemoryRecord] -- The records.
        """
        collection = await self.get_collection_async(collection_name)
        if collection is None:
            raise Exception(f"Collection '{collection_name}' does not exist")

        query_includes = (
            ["embeddings", "metadatas", "documents"]
            if with_embeddings
            else ["metadatas", "documents"]
        )

        value = collection.get(ids=keys, include=query_includes)
        record = query_results_to_records(value, with_embeddings)
        return record

    async def remove_async(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Arguments:
            collection_name {str} -- The name of the collection to remove the record from.
            key {str} -- The unique database key of the record to remove.

        Returns:
            None
        """
        await self.remove_batch_async(collection_name, [key])

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Removes a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to remove the records from.
            keys {List[str]} -- The unique database keys of the records to remove.

        Returns:
            None
        """
        collection = await self.get_collection_async(collection_name=collection_name)
        if collection is not None:
            collection.delete(ids=keys)

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = True,
    ) -> List[Tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding using cosine similarity.

        Arguments:
            collection_name {str} -- The name of the collection to get the nearest matches from.
            embedding {ndarray} -- The embedding to find the nearest matches to.
            limit {int} -- The maximum number of matches to return.
            min_relevance_score {float} -- The minimum relevance score of the matches. (default: {0.0})
            with_embeddings {bool} -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[Tuple[MemoryRecord, float]] -- The records and their relevance scores.
        """
        if with_embeddings is False:
            self._logger.warning(
                "Chroma returns distance score not cosine similarity score.\
                So embeddings are automatically queried from database for calculation."
            )
        collection = await self.get_collection_async(collection_name)
        if collection is None:
            return []

        query_results = collection.query(
            query_embeddings=embedding.tolist(),
            n_results=limit,
            include=self._default_query_includes,
        )

        # Convert the collection of embeddings into a numpy array (stacked)
        embedding_array = array(query_results["embeddings"][0])
        embedding_array = embedding_array.reshape(embedding_array.shape[0], -1)

        # If the query embedding has shape (1, embedding_size),
        # reshape it to (embedding_size,)
        if len(embedding.shape) == 2:
            embedding = embedding.reshape(
                embedding.shape[1],
            )

        similarity_score = chroma_compute_similarity_scores(embedding, embedding_array)

        # Convert query results into memory records
        record_list = [
            (record, distance)
            for record, distance in zip(
                query_results_to_records(query_results, with_embeddings),
                similarity_score,
            )
        ]

        sorted_results = sorted(
            record_list,
            key=lambda x: x[1],
            reverse=True,
        )

        filtered_results = [x for x in sorted_results if x[1] >= min_relevance_score]
        top_results = filtered_results[:limit]

        return top_results

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = True,
    ) -> Tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding using cosine similarity.

        Arguments:
            collection_name {str} -- The name of the collection to get the nearest match from.
            embedding {ndarray} -- The embedding to find the nearest match to.
            min_relevance_score {float} -- The minimum relevance score of the match. (default: {0.0})
            with_embedding {bool} -- Whether to include the embedding in the result. (default: {False})

        Returns:
            Tuple[MemoryRecord, float] -- The record and the relevance score.
        """
        results = await self.get_nearest_matches_async(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        return results[0]


if __name__ == "__main__":
    import asyncio

    import numpy as np

    memory = ChromaMemoryStore()
    memory_record1 = MemoryRecord(
        id="test_id1",
        text="sample text1",
        is_reference=False,
        embedding=np.array([0.5, 0.5]),
        description="description",
        external_source_name="external source",
        timestamp="timestamp",
    )
    memory_record2 = MemoryRecord(
        id="test_id2",
        text="sample text2",
        is_reference=False,
        embedding=np.array([0.25, 0.75]),
        description="description",
        external_source_name="external source",
        timestamp="timestamp",
    )

    asyncio.run(memory.create_collection_async("test_collection"))
    collection = asyncio.run(memory.get_collection_async("test_collection"))

    asyncio.run(
        memory.upsert_batch_async(collection.name, [memory_record1, memory_record2])
    )

    result = asyncio.run(memory.get_async(collection.name, "test_id1", True))
    results = asyncio.run(
        memory.get_nearest_match_async("test_collection", np.array([0.5, 0.5]))
    )
    print(results)
