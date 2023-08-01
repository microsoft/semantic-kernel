# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional, Tuple

from numpy import array, expand_dims, ndarray
from pymilvus.milvus_client import milvus_client

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger


def memoryrecord_to_milvus_dict(mem: MemoryRecord) -> dict:
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
            ret_dict[key[1:]] = val
    return ret_dict


def milvus_dict_to_memoryrecord(milvus_dict: dict) -> MemoryRecord:
    """Convert Milvus search result dict into MemoryRecord.

    Args:
        milvus_dict (dict): Search hit

    Returns:
        MemoryRecord
    """
    # Embedding needs conversion to numpy array
    embedding = milvus_dict.get("embedding", None)
    if embedding is not None:
        embedding = array(embedding)
    return MemoryRecord(
        is_reference=milvus_dict.get("is_reference", None),
        external_source_name=milvus_dict.get("external_source_name", None),
        id=milvus_dict.get("id", None),
        description=milvus_dict.get("description", None),
        text=milvus_dict.get("text", None),
        additional_metadata=milvus_dict.get("additional_metadata", None),
        embedding=embedding,
        key=milvus_dict.get("key", None),
        timestamp=milvus_dict.get("timestamp", None),
    )


# Default field values
ID_FIELD = "id"
ID_TYPE = "str"
EMBEDDING_FIELD = "embedding"


class MilvusMemoryStore(MemoryStoreBase):
    def __init__(
        self,
        uri: str = "http://localhost:19530",
        token: Optional[str] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        """MilvusMemoryStore allows for searching for records using Milvus/Zilliz Cloud.

        For more details on how to get the service started, take a look here:
            Milvus: https://milvus.io/docs/get_started.md
            Zilliz Cloud: https://docs.zilliz.com/docs/quick-start


        Args:
            uri (str, optional): The uri of the cluster. Defaults to
                "http://localhost:19530".
            token (Optional[str], optional): The token to connect to the cluster if
                authentication is required. Defaults to None.
            logger (Optional[Logger], optional): Logger to use. Defaults to None.
        """
        self._uri = uri
        self._token = (token,)
        self._logger = logger or NullLogger()
        self._client = milvus_client.MilvusClient(
            uri=uri,
            token=token,
        )
        self._metric_cache = {}

    async def create_collection_async(
        self,
        collection_name: str,
        dimension_num: Optional[int] = 1536,
        distance_type: Optional[str] = "IP",
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
        if collection_name in self._client.list_collections():
            if overwrite:
                self._client.drop_collection(collection_name=collection_name)
                self._client.create_collection(
                    collection_name=collection_name,
                    dimension=dimension_num,
                    primary_field_name=ID_FIELD,
                    id_type=ID_TYPE,
                    auto_id=False,
                    vector_field_name=EMBEDDING_FIELD,
                    metric_type=distance_type,
                    max_length=65_535,
                    consistency_level=consistency,
                )
        else:
            self._client.create_collection(
                collection_name=collection_name,
                dimension=dimension_num,
                primary_field_name=ID_FIELD,
                id_type=ID_TYPE,
                auto_id=False,
                vector_field_name=EMBEDDING_FIELD,
                metric_type=distance_type,
                max_length=65_535,
                consistency_level=consistency,
            )

    async def get_collections_async(
        self,
    ) -> List[str]:
        """Return a list of present collections.

        Returns:
            List[str]: List of collection names.
        """
        return self._client.list_collections()

    async def delete_collection_async(
        self, collection_name: str = "", all: bool = False
    ) -> None:
        """Delete the specified collection.

        If all is True, all collections in the cluster will be removed.

        Args:
            collection_name (str, optional): The name of the collection to delete. Defaults to "".
            all (bool, optional): Whether to delete all collections. Defaults to False.
        """
        cols = self._client.list_collections()
        if all:
            for x in cols:
                self._client.drop_collection(x)
        elif collection_name in cols:
            self._client.drop_collection(collection_name)

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """Return if the collection exists in the cluster.

        Args:
            collection_name (str): The name of the collection.

        Returns:
            bool: True if it exists, False otherwise.
        """
        return True if collection_name in self._client.list_collections() else False

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """Upsert a single MemoryRecord into the collection.

        Args:
            collection_name (str): The name of the collection.
            record (MemoryRecord): The record to store.

        Returns:
            str: The ID of the inserted record.
        """
        # Use the batch insert with a total batch
        res = await self.upsert_batch_async(
            collection_name=collection_name,
            records=[record],
            batch_size=0,
        )
        return res[0]

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord], batch_size=100
    ) -> List[str]:
        """_summary_

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
        if collection_name not in self._client.list_collections():
            self._logger.debug(
                f"Collection {collection_name} does not exist, cannot insert."
            )
            raise Exception(
                f"Collection {collection_name} does not exist, cannot insert."
            )
        # Convert the records to dicts
        insert_list = [memoryrecord_to_milvus_dict(record) for record in records]
        # The ids to remove
        delete_ids = [insert[ID_FIELD] for insert in insert_list]
        try:
            # First delete then insert to have upsert
            self._client.delete(collection_name=collection_name, pks=delete_ids)
            return self._client.insert(
                collection_name=collection_name, data=insert_list, batch_size=batch_size
            )
        except Exception as e:
            self._logger.debug(f"Upsert failed due to: {e}")
            raise e

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool
    ) -> MemoryRecord:
        """Get the MemoryRecord corresponding to the key.

        Args:
            collection_name (str): The collection to get from.
            key (str): The ID to grab.
            with_embedding (bool): Whether to include the embedding in the results.

        Returns:
            MemoryRecord: The MemoryRecord for the key.
        """
        res = await self.get_batch_async(
            collection_name=collection_name, keys=[key], with_embeddings=with_embedding
        )
        return res[0]

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool
    ) -> List[MemoryRecord]:
        """Get the MemoryRecords corresponding to the keys

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
        if collection_name not in self._client.list_collections():
            self._logger.debug(
                f"Collection {collection_name} does not exist, cannot get."
            )
            raise Exception("Collection {collection_name} does not exist, cannot get.")
        try:
            gets = self._client.get(
                collection_name=collection_name,
                ids=keys,
                output_fields=["*"] if not with_embeddings else ["*", EMBEDDING_FIELD],
            )
            return [milvus_dict_to_memoryrecord(get) for get in gets]
        except Exception as e:
            self._logger.debug(f"Get failed due to: {e}")
            raise e

    async def remove_async(self, collection_name: str, key: str) -> None:
        """Remove the specified record based on key.

        Args:
            collection_name (str): Collection to remove from.
            key (str): The key to remove.
        """
        await self.remove_batch_async(collection_name=collection_name, keys=[key])

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Remove multiple records based on keys.

        Args:
            collection_name (str): Collection to remove from
            keys (List[str]): The list of keys.

        Raises:
            Exception: Collection doesnt exist.
            e: Failure to remove key.
        """
        if collection_name not in self._client.list_collections():
            self._logger.debug(
                f"Collection {collection_name} does not exist, cannot remove."
            )
            raise Exception(
                f"Collection {collection_name} does not exist, cannot remove."
            )
        try:
            self._client.delete(
                collection_name=collection_name,
                pks=keys,
            )
        except Exception as e:
            self._logger.debug(f"Remove failed due to: {e}")
            raise e

    def _search(self, collection_name, data, limit, distance_metric):
        """Helper function to search with correct distance metric due to bug"""
        # TODO Remove after https://github.com/milvus-io/milvus/issues/25504
        # Simple way to select opposite
        distance_pairs = {
            "l2": "IP",
            "ip": "L2",
        }
        try:
            # Try with passed in metric
            results = self._client.search(
                collection_name=collection_name,
                data=data,
                limit=limit,
                search_params={"metric_type": distance_metric},
                output_fields=["*"],
            )[0]
            return results, distance_metric
        except Exception as e:
            self._logger.debug(f"Search failed with IP, testing L2: {e}")
            try:
                distance_metric = distance_pairs[distance_metric.lower()]
                results = self._client.search(
                    collection_name=collection_name,
                    data=data,
                    limit=limit,
                    search_params={"metric_type": distance_metric},
                    output_fields=["*"],
                )[0]
                return results, distance_metric
            except Exception as e:
                self._logger.debug(f"Search failed with L2: {e}")
                raise e

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = None,
        with_embeddings: bool = False,
    ) -> List[Tuple[MemoryRecord, float]]:
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
        if collection_name not in self._client.list_collections():
            self._logger.debug(
                f"Collection {collection_name} does not exist, cannot search."
            )
            raise Exception(
                f"Collection {collection_name} does not exist, cannot search."
            )
        # Search requests takes a list of requests.
        if len(embedding.shape) == 1:
            embedding = expand_dims(embedding, axis=0)

        # Search based on the cached metric
        results, search_type = self._search(
            collection_name=collection_name,
            data=embedding,
            limit=limit,
            distance_metric=self._metric_cache.get(collection_name, None) or "IP",
        )

        # Update cached metric
        self._metric_cache[collection_name] = search_type

        cleaned_results = []

        if with_embeddings:
            ids = []

        # Clean up results, filter and get ids for fetch
        for x in results:
            if min_relevance_score is not None and x["distance"] < min_relevance_score:
                continue
            cleaned_results.append(x)
            if with_embeddings:
                ids.append(x[ID_FIELD])

        if with_embeddings:
            try:
                vectors = self._client.get(
                    collection_name=collection_name,
                    ids=ids,
                    output_fields=[EMBEDDING_FIELD],
                )
            except Exception as e:
                self._logger.debug(f"Get embeddings in search failed due to: {e}.")
                raise e

            vectors = {res[ID_FIELD]: res[EMBEDDING_FIELD] for res in vectors}
            for res in results:
                res["entity"][EMBEDDING_FIELD] = vectors[res[ID_FIELD]]

        results = [
            (milvus_dict_to_memoryrecord(result["entity"]), result["distance"])
            for result in results
        ]

        return results

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = None,
        with_embedding: bool = False,
    ) -> Tuple[MemoryRecord, float]:
        """Find the nearest match for an embedding.

        Args:
            collection_name (str): The collection to search.
            embedding (ndarray): The embedding to search for.
            min_relevance_score (float, optional): T. Defaults to 0.0.
            with_embedding (bool, optional): Whether to include embedding in result. Defaults to False.

        Returns:
            Tuple[MemoryRecord, float]: A tuple of record and distance.
        """
        m = await self.get_nearest_matches_async(
            collection_name,
            embedding,
            1,
            min_relevance_score,
            with_embedding,
        )
        if len(m) > 0:
            return m[0]
        else:
            return None
