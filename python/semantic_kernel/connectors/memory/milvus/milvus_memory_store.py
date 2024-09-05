# Copyright (c) Microsoft. All rights reserved.

import logging
from datetime import datetime
from typing import Any

from numpy import array, expand_dims, ndarray
from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

from semantic_kernel.exceptions import ServiceResourceNotFoundError, ServiceResponseException
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.experimental_decorator import experimental_class, experimental_function

logger: logging.Logger = logging.getLogger(__name__)

# Index parameters
_INDEX_TYPE = "IVF_FLAT"
_NLIST = 1024

SEARCH_FIELD_ID = "id"
SEARCH_FIELD_TEXT = "text"
SEARCH_FIELD_EMBEDDING = "embedding"
SEARCH_FIELD_SRC = "external_source_name"
SEARCH_FIELD_DESC = "description"
SEARCH_FIELD_METADATA = "additional_metadata"
SEARCH_FIELD_IS_REF = "is_reference"
SEARCH_FIELD_TIMESTAMP = "timestamp"

OUTPUT_FIELDS_W_EMBEDDING = [
    SEARCH_FIELD_ID,
    SEARCH_FIELD_TEXT,
    SEARCH_FIELD_SRC,
    SEARCH_FIELD_DESC,
    SEARCH_FIELD_METADATA,
    SEARCH_FIELD_IS_REF,
    SEARCH_FIELD_EMBEDDING,
    SEARCH_FIELD_TIMESTAMP,
]
OUTPUT_FIELDS_WO_EMBEDDING = [
    SEARCH_FIELD_ID,
    SEARCH_FIELD_TEXT,
    SEARCH_FIELD_SRC,
    SEARCH_FIELD_DESC,
    SEARCH_FIELD_METADATA,
    SEARCH_FIELD_IS_REF,
    SEARCH_FIELD_TIMESTAMP,
]


@experimental_function
def memoryrecord_to_milvus_dict(mem: MemoryRecord) -> dict[str, Any]:
    """Convert a memoryrecord into a dict.

    Args:
        mem (MemoryRecord): MemoryRecord to convert.

    Returns:
        dict: Dict result.
    """
    ret_dict = {}
    # Grab all the class vars
    for key, val in vars(mem).items():
        if val is not None:
            # Remove underscore
            if isinstance(val, datetime):
                val = val.isoformat()
            ret_dict[key[1:]] = val
    return ret_dict


@experimental_function
def milvus_dict_to_memoryrecord(milvus_dict: dict[str, Any]) -> MemoryRecord:
    """Convert Milvus search result dict into MemoryRecord.

    Args:
        milvus_dict (dict): Search hit

    Returns:
        MemoryRecord
    """
    # Embedding needs conversion to numpy array
    embedding = milvus_dict.get(SEARCH_FIELD_EMBEDDING)
    if embedding is not None:
        embedding = array(embedding)
    return MemoryRecord(
        is_reference=milvus_dict.get(SEARCH_FIELD_IS_REF),
        external_source_name=milvus_dict.get(SEARCH_FIELD_SRC),
        id=milvus_dict.get(SEARCH_FIELD_ID),
        description=milvus_dict.get(SEARCH_FIELD_DESC),
        text=milvus_dict.get(SEARCH_FIELD_TEXT),
        additional_metadata=milvus_dict.get(SEARCH_FIELD_METADATA),
        embedding=embedding,
        key=milvus_dict.get("key"),
        timestamp=milvus_dict.get(SEARCH_FIELD_TIMESTAMP),
    )


@experimental_function
def create_fields(dimensions: int) -> list[FieldSchema]:
    """Create the fields for the Milvus collection."""
    return [
        FieldSchema(
            name=SEARCH_FIELD_ID,
            dtype=DataType.VARCHAR,
            is_primary=True,
            auto_id=False,
            max_length=100,
        ),
        FieldSchema(
            name=SEARCH_FIELD_TEXT,
            dtype=DataType.VARCHAR,
            max_length=65535,
        ),
        FieldSchema(
            name=SEARCH_FIELD_SRC,
            dtype=DataType.VARCHAR,
            max_length=400,
        ),
        FieldSchema(
            name=SEARCH_FIELD_DESC,
            dtype=DataType.VARCHAR,
            max_length=800,
        ),
        FieldSchema(
            name=SEARCH_FIELD_METADATA,
            dtype=DataType.VARCHAR,
            max_length=800,
        ),
        FieldSchema(
            name=SEARCH_FIELD_EMBEDDING,
            dtype=DataType.FLOAT_VECTOR,
            dim=dimensions,
        ),
        FieldSchema(
            name=SEARCH_FIELD_IS_REF,
            dtype=DataType.BOOL,
        ),
        FieldSchema(
            name=SEARCH_FIELD_TIMESTAMP,
            dtype=DataType.VARCHAR,
            max_length=100,
        ),
    ]


@experimental_class
class MilvusMemoryStore(MemoryStoreBase):
    """Memory store based on Milvus."""

    def __init__(
        self,
        uri: str = "http://localhost:19530",
        token: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Memory store based on Milvus.

        For more details on how to get the service started, take a look here:
        - Milvus: https://milvus.io/docs/get_started.md
        - Zilliz Cloud: https://docs.zilliz.com/docs/quick-start


        Args:
            uri (str, optional): The uri of the cluster. Defaults to
                "http://localhost:19530".
            token (Optional[str], optional): The token to connect to the cluster if
                authentication is required. Defaults to None.
            **kwargs (Any): Unused.
        """
        connections.connect("default", uri=uri, token=token)
        self.collections: dict[str, Collection] = {}

    async def create_collection(
        self,
        collection_name: str,
        dimension_num: int = 1536,
        distance_type: str | None = "IP",
        overwrite: bool = False,
        consistency: str = "Session",
    ) -> None:
        """Create a Milvus collection.

        Args:
            collection_name (str): The name of the collection.
            dimension_num (Optional[int], optional): The size of the embeddings being
                stored. Defaults to 1536.
            distance_type (Optional[str], optional): Which distance function, at the
                moment only "IP" and "L2" are supported. Defaults to "IP".
            overwrite (bool, optional): Whether to overwrite any existing collection
                with the same name. Defaults to False.
            consistency (str, optional): Which consistency level to use:
                Strong, Session, Bounded, Eventually. Defaults to "Session".
        """
        schema = CollectionSchema(
            create_fields(dimension_num), "Semantic Kernel Milvus Collection", enable_dynamic_field=True
        )
        index_param = {"index_type": _INDEX_TYPE, "params": {"nlist": _NLIST}, "metric_type": distance_type}
        if utility.has_collection(collection_name) and overwrite:
            utility.drop_collection(collection_name=collection_name)
        self.collections[collection_name] = Collection(
            name=collection_name,
            schema=schema,
            consistency_level=consistency,
        )
        self.collections[collection_name].create_index(SEARCH_FIELD_EMBEDDING, index_param)

    async def get_collections(
        self,
    ) -> list[str]:
        """Return a list of present collections.

        Returns:
            List[str]: List of collection names.
        """
        return utility.list_collections()

    async def delete_collection(self, collection_name: str | None = None, all: bool = False) -> None:
        """Delete the specified collection.

        If all is True, all collections in the cluster will be removed.

        Args:
            collection_name (str, optional): The name of the collection to delete. Defaults to "".
            all (bool, optional): Whether to delete all collections. Defaults to False.
        """
        if collection_name and utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            del self.collections[collection_name]
            return
        if all:
            for collection in utility.list_collections():
                utility.drop_collection(collection)
            self.collections = {}

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Return if the collection exists in the cluster.

        Args:
            collection_name (str): The name of the collection.

        Returns:
            bool: True if it exists, False otherwise.
        """
        return utility.has_collection(collection_name)

    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Upsert a single MemoryRecord into the collection.

        Args:
            collection_name (str): The name of the collection.
            record (MemoryRecord): The record to store.

        Returns:
            str: The ID of the inserted record.
        """
        # Use the batch insert with a total batch
        res = await self.upsert_batch(
            collection_name=collection_name,
            records=[record],
            batch_size=0,
        )
        return res[0]

    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord], batch_size=100) -> list[str]:
        """_summary_.

        Args:
            collection_name (str): The collection name.
            records (List[MemoryRecord]): A list of memory records.
            batch_size (int, optional): Batch size of the insert, 0 is a batch
                size of total size. Defaults to 100.

        Raises:
            Exception: Collection doesnt exist.
            e: Failed to upsert a record.

        Returns:
            List[str]: A list of inserted ID's.
        """
        # Check if the collection exists.
        if collection_name not in utility.list_collections():
            logger.debug(f"Collection {collection_name} does not exist, cannot insert.")
            raise ServiceResourceNotFoundError(f"Collection {collection_name} does not exist, cannot insert.")
        # Convert the records to dicts
        insert_list = [memoryrecord_to_milvus_dict(record) for record in records]
        try:
            ids = self.collections[collection_name].upsert(data=insert_list).primary_keys
            self.collections[collection_name].flush()
            return ids
        except Exception as e:
            logger.debug(f"Upsert failed due to: {e}")
            raise ServiceResponseException(f"Upsert failed due to: {e}") from e

    async def get(self, collection_name: str, key: str, with_embedding: bool) -> MemoryRecord:
        """Get the MemoryRecord corresponding to the key.

        Args:
            collection_name (str): The collection to get from.
            key (str): The ID to grab.
            with_embedding (bool): Whether to include the embedding in the results.

        Returns:
            MemoryRecord: The MemoryRecord for the key.
        """
        res = await self.get_batch(collection_name=collection_name, keys=[key], with_embeddings=with_embedding)
        return res[0]

    async def get_batch(self, collection_name: str, keys: list[str], with_embeddings: bool) -> list[MemoryRecord]:
        """Get the MemoryRecords corresponding to the keys.

        Args:
            collection_name (str): _description_
            keys (List[str]): _description_
            with_embeddings (bool): _description_

        Raises:
            Exception: _description_
            e: _description_

        Returns:
            List[MemoryRecord]: _description_
        """
        # Check if the collection exists
        if not utility.has_collection(collection_name):
            logger.debug(f"Collection {collection_name} does not exist, cannot get.")
            raise ServiceResourceNotFoundError(f"Collection {collection_name} does not exist, cannot get.")

        try:
            self.collections[collection_name].load()
            gets = self.collections[collection_name].query(
                expr=f"{SEARCH_FIELD_ID} in {keys}",
                output_fields=OUTPUT_FIELDS_W_EMBEDDING if with_embeddings else OUTPUT_FIELDS_WO_EMBEDDING,
            )
        except Exception as e:
            logger.debug(f"Get failed due to: {e}")
            raise ServiceResponseException(f"Get failed due to: {e}") from e
        return [milvus_dict_to_memoryrecord(get) for get in gets]

    async def remove(self, collection_name: str, key: str) -> None:
        """Remove the specified record based on key.

        Args:
            collection_name (str): Collection to remove from.
            key (str): The key to remove.
        """
        await self.remove_batch(collection_name=collection_name, keys=[key])

    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Remove multiple records based on keys.

        Args:
            collection_name (str): Collection to remove from
            keys (List[str]): The list of keys.

        Raises:
            Exception: Collection doesnt exist.
            e: Failure to remove key.
        """
        if collection_name not in utility.list_collections():
            logger.debug(f"Collection {collection_name} does not exist, cannot remove.")
            raise ServiceResourceNotFoundError(f"Collection {collection_name} does not exist, cannot remove.")
        try:
            self.collections[collection_name].load()
            result = self.collections[collection_name].delete(
                expr=f"{SEARCH_FIELD_ID} in {keys}",
            )
            self.collections[collection_name].flush()
        except Exception as e:
            logger.debug(f"Remove failed due to: {e}")
            raise ServiceResponseException(f"Remove failed due to: {e}") from e
        if result.delete_count != len(keys):
            logger.debug(f"Failed to remove all keys, {result.delete_count} removed out of {len(keys)}")
            raise ServiceResponseException(
                f"Failed to remove all keys, {result.delete_count} removed out of {len(keys)}"
            )

    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = False,
    ) -> list[tuple[MemoryRecord, float]]:
        """Find the nearest `limit` matches for an embedding.

        Args:
            collection_name (str): The collection to search.
            embedding (ndarray): The embedding to search.
            limit (int): The total results to display.
            min_relevance_score (float, optional): Minimum distance to include. Defaults to None.
            with_embeddings (bool, optional): Whether to include embeddings in result. Defaults to False.

        Raises:
            Exception: Missing collection
            e: Failure to search

        Returns:
            List[Tuple[MemoryRecord, float]]: MemoryRecord and distance tuple.
        """
        # Check if collection exists
        if collection_name not in utility.list_collections():
            logger.debug(f"Collection {collection_name} does not exist, cannot search.")
            raise ServiceResourceNotFoundError(f"Collection {collection_name} does not exist, cannot search.")
        # Search requests takes a list of requests.
        if len(embedding.shape) == 1:
            embedding = expand_dims(embedding, axis=0)

        try:
            self.collections[collection_name].load()
            metric = self.collections[collection_name].index(index_name=SEARCH_FIELD_EMBEDDING).params["metric_type"]
            # Try with passed in metric
            results = self.collections[collection_name].search(
                data=embedding,
                anns_field=SEARCH_FIELD_EMBEDDING,
                limit=limit,
                output_fields=OUTPUT_FIELDS_W_EMBEDDING if with_embeddings else OUTPUT_FIELDS_WO_EMBEDDING,
                param={"metric_type": metric},
            )[0]
        except Exception as e:
            logger.debug(f"Search failed: {e}")
            raise ServiceResponseException(f"Search failed: {e}") from e
        return [
            (milvus_dict_to_memoryrecord(result.fields), result.distance)
            for result in results
            if result.distance >= min_relevance_score
        ]

    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> tuple[MemoryRecord, float] | None:
        """Find the nearest match for an embedding.

        Args:
            collection_name (str): The collection to search.
            embedding (ndarray): The embedding to search for.
            min_relevance_score (float, optional): T. Defaults to 0.0.
            with_embedding (bool, optional): Whether to include embedding in result. Defaults to False.

        Returns:
            Tuple[MemoryRecord, float]: A tuple of record and distance.
        """
        m = await self.get_nearest_matches(
            collection_name,
            embedding,
            1,
            min_relevance_score,
            with_embedding,
        )
        if len(m) > 0:
            return m[0]
        return None
