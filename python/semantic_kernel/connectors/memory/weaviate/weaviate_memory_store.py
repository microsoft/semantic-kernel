# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import Final

import numpy as np
import weaviate

from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)

SCHEMA = {
    "class": "MemoryRecord",
    "description": "A document from semantic kernel.",
    "properties": [
        {
            "name": "key",
            "description": "The key of the record.",
            "dataType": ["string"],
        },
        {
            "name": "timestamp",
            "description": "The timestamp of the record.",
            "dataType": ["date"],
        },
        {
            "name": "isReference",
            "description": "Whether the record is a reference record.",
            "dataType": ["boolean"],
        },
        {
            "name": "externalSourceName",
            "description": "The name of the external source.",
            "dataType": ["string"],
        },
        {
            "name": "skId",
            "description": "A unique identifier for the record.",
            "dataType": ["string"],
        },
        {
            "name": "description",
            "description": "The description of the record.",
            "dataType": ["text"],
        },
        {
            "name": "text",
            "description": "The text of the record.",
            "dataType": ["text"],
        },
        {
            "name": "additionalMetadata",
            "description": "Optional custom metadata of the record.",
            "dataType": ["string"],
        },
    ],
}

ALL_PROPERTIES = [property["name"] for property in SCHEMA["properties"]]


class FieldMapper:
    """This maps attribute names between the SK's memory record and weaviate's schema.

    It provides methods for converting between the two naming conventions.
    """

    SK_TO_WEAVIATE_MAPPING: Final[dict[str, str]] = {
        "_key": "key",
        "_timestamp": "timestamp",
        "_is_reference": "isReference",
        "_external_source_name": "externalSourceName",
        "_id": "skId",
        "_description": "description",
        "_text": "text",
        "_additional_metadata": "additionalMetadata",
        "_embedding": "vector",
    }

    WEAVIATE_TO_SK_MAPPING: Final[dict[str, str]] = {v: k for k, v in SK_TO_WEAVIATE_MAPPING.items()}

    @classmethod
    def sk_to_weaviate(cls, sk_dict):
        """Used to convert a MemoryRecord to a dict of attribute-values that can be used by Weaviate."""
        return {cls.SK_TO_WEAVIATE_MAPPING.get(k, k): v for k, v in sk_dict.items() if k in cls.SK_TO_WEAVIATE_MAPPING}

    @classmethod
    def weaviate_to_sk(cls, weaviate_dict):
        """Used to convert a Weaviate object to a dict that can be used to initialize a MemoryRecord."""
        return {
            cls.WEAVIATE_TO_SK_MAPPING.get(k, k): v for k, v in weaviate_dict.items() if k in cls.WEAVIATE_TO_SK_MAPPING
        }

    @classmethod
    def remove_underscore_prefix(cls, sk_dict):
        """Used to initialize a MemoryRecord from a SK's dict of private attribute-values."""
        return {key.lstrip("_"): value for key, value in sk_dict.items()}


@experimental
class WeaviateMemoryStore(MemoryStoreBase):
    """A memory store that uses Weaviate as the backend."""

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        use_embed: bool = False,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initializes a new instance of the WeaviateMemoryStore.

        Args:
            url (str): The URL of the Weaviate instance.
            api_key (str): The API key to use for authentication.
            use_embed (bool): Whether to use the client embedding options.
            env_file_path (str): Whether to use the environment settings (.env) file.
            env_file_encoding (str): The encoding of the environment settings (.env) file. Defaults to 'utf-8'.
        """
        from semantic_kernel.connectors.memory.weaviate.weaviate_settings import WeaviateSettings

        self.settings = WeaviateSettings(
            url=url,
            api_key=api_key,
            use_embed=use_embed,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
        )
        if self.settings.use_embed:
            self.client = weaviate.Client(embedded_options=weaviate.EmbeddedOptions())
        elif self.settings.api_key and self.settings.url:
            self.client = weaviate.Client(
                url=str(self.settings.url),
                auth_client_secret=weaviate.auth.AuthApiKey(api_key=self.settings.api_key.get_secret_value()),
            )
        elif self.settings.url:
            self.client = weaviate.Client(url=str(self.settings.url))
        else:
            raise MemoryConnectorInitializationError("WeaviateMemoryStore requires a URL or API key, or to use embed.")

    async def create_collection(self, collection_name: str) -> None:
        """Creates a new collection in Weaviate."""
        schema = SCHEMA.copy()
        schema["class"] = collection_name
        await asyncio.get_running_loop().run_in_executor(None, self.client.schema.create_class, schema)

    async def get_collections(self) -> list[str]:
        """Returns a list of all collections in Weaviate."""
        schemas = await asyncio.get_running_loop().run_in_executor(None, self.client.schema.get)
        return [schema["class"] for schema in schemas["classes"]]

    async def delete_collection(self, collection_name: str) -> bool:
        """Deletes a collection in Weaviate."""
        await asyncio.get_running_loop().run_in_executor(None, self.client.schema.delete_class, collection_name)

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Checks if a collection exists in Weaviate."""
        collections = await self.get_collections()
        return collection_name in collections

    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Upserts a record into Weaviate."""
        weaviate_record = FieldMapper.sk_to_weaviate(vars(record))

        vector = weaviate_record.pop("vector", None)
        weaviate_id = weaviate.util.generate_uuid5(weaviate_record, collection_name)

        return await asyncio.get_running_loop().run_in_executor(
            None,
            self.client.data_object.create,
            weaviate_record,
            collection_name,
            weaviate_id,
            vector,
        )

    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        """Upserts a batch of records into Weaviate."""

        def _upsert_batch_inner():
            results = []
            with self.client.batch as batch:
                for record in records:
                    weaviate_record = FieldMapper.sk_to_weaviate(vars(record))
                    vector = weaviate_record.pop("vector", None)
                    weaviate_id = weaviate.util.generate_uuid5(weaviate_record, collection_name)
                    batch.add_data_object(
                        data_object=weaviate_record,
                        uuid=weaviate_id,
                        vector=vector,
                        class_name=collection_name,
                    )
                    results.append(weaviate_id)

            return results

        return await asyncio.get_running_loop().run_in_executor(None, _upsert_batch_inner)

    async def get(self, collection_name: str, key: str, with_embedding: bool) -> MemoryRecord:
        """Gets a record from Weaviate by key."""
        # Call the batched version with a single key
        results = await self.get_batch(collection_name, [key], with_embedding)
        return results[0] if results else None

    async def get_batch(self, collection_name: str, keys: list[str], with_embedding: bool) -> list[MemoryRecord]:
        """Gets a batch of records from Weaviate by keys."""
        queries = self._build_multi_get_query(collection_name, keys, with_embedding)

        results = await asyncio.get_running_loop().run_in_executor(None, self.client.query.multi_get(queries).do)

        get_dict = results.get("data", {}).get("Get", {})

        return [self._convert_weaviate_doc_to_memory_record(doc) for docs in get_dict.values() for doc in docs]

    def _build_multi_get_query(self, collection_name: str, keys: list[str], with_embedding: bool):
        queries = []
        for i, key in enumerate(keys):
            query = self.client.query.get(collection_name, ALL_PROPERTIES).with_where({
                "path": ["key"],
                "operator": "Equal",
                "valueString": key,
            })
            if with_embedding:
                query = query.with_additional("vector")

            query = query.with_alias(f"query_{i}")

            queries.append(query)

        return queries

    def _convert_weaviate_doc_to_memory_record(self, weaviate_doc: dict) -> MemoryRecord:
        weaviate_doc_copy = weaviate_doc.copy()
        vector = weaviate_doc_copy.pop("_additional", {}).get("vector")
        weaviate_doc_copy["vector"] = np.array(vector) if vector else None
        sk_doc = FieldMapper.weaviate_to_sk(weaviate_doc_copy)
        mem_vals = FieldMapper.remove_underscore_prefix(sk_doc)
        return MemoryRecord(**mem_vals)

    async def remove(self, collection_name: str, key: str) -> None:
        """Removes a record from Weaviate by key."""
        await self.remove_batch(collection_name, [key])

    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Removes a batch of records from Weaviate by keys."""
        for key in keys:
            where = {
                "path": ["key"],
                "operator": "Equal",
                "valueString": key,
            }

            await asyncio.get_running_loop().run_in_executor(
                None, self.client.batch.delete_objects, collection_name, where
            )

    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: np.ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> list[tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding in Weaviate."""
        nearVector = {
            "vector": embedding,
            "certainty": min_relevance_score,
        }

        additional = ["certainty"]
        if with_embeddings:
            additional.append("vector")

        query = (
            self.client.query.get(collection_name, ALL_PROPERTIES)
            .with_near_vector(nearVector)
            .with_additional(additional)
            .with_limit(limit)
        )

        results = await asyncio.get_running_loop().run_in_executor(None, query.do)

        get_dict = results.get("data", {}).get("Get", {})

        return [
            (
                self._convert_weaviate_doc_to_memory_record(doc),
                item["_additional"]["certainty"],
            )
            for items in get_dict.values()
            for item in items
            for doc in [item]
        ]

    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: np.ndarray,
        min_relevance_score: float,
        with_embedding: bool,
    ) -> tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding in Weaviate."""
        results = await self.get_nearest_matches(
            collection_name,
            embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )

        return results[0]
