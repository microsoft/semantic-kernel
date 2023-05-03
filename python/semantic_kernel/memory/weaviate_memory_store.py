import asyncio
from dataclasses import dataclass
from logging import Logger
from typing import List, Optional

import weaviate
from weaviate.embedded import EmbeddedOptions

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger

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
    ],
}


@dataclass
class WeaviateConfig:
    use_embed: bool = False
    url: str = None
    api_key: str = None


class WeaviateMemoryStore(MemoryStoreBase):
    class FieldMapper:
        """
        This inner class is responsible for mapping attribute names between
        the SK's memory record and weaviate's schema. It provides methods
        for converting between the two naming conventions.
        """

        SK_TO_WEAVIATE_MAPPING = {
            "_key": "key",
            "_timestamp": "timestamp",
            "_is_reference": "isReference",
            "_external_source_name": "externalSourceName",
            "_id": "skId",
            "_description": "description",
            "_text": "text",
            "_embedding": "vector",
        }

        WEAVIATE_TO_SK_MAPPING = {v: k for k, v in SK_TO_WEAVIATE_MAPPING.items()}

        @classmethod
        def sk_to_weaviate(cls, sk_dict):
            return {
                cls.SK_TO_WEAVIATE_MAPPING.get(k, k): v
                for k, v in sk_dict.items()
                if k in cls.SK_TO_WEAVIATE_MAPPING
            }

        @classmethod
        def weaviate_to_sk(cls, weaviate_dict):
            return {
                cls.WEAVIATE_TO_SK_MAPPING.get(k, k): v
                for k, v in weaviate_dict.items()
                if k in cls.WEAVIATE_TO_SK_MAPPING
            }

    def __init__(self, config: WeaviateConfig, logger: Optional[Logger] = None):
        self._logger = logger or NullLogger()
        self.config = config
        self.client = self._initialize_client()

    def _initialize_client(self):
        if self.config.use_embed:
            return weaviate.Client(embedded_options=EmbeddedOptions())
        elif self.config.url:
            if self.api_key:
                return weaviate.Client(
                    url=self.config.url,
                    auth_client_secret=weaviate.auth.AuthApiKey(
                        api_key=self.config.api_key
                    ),
                )
            else:
                return weaviate.Client(url=self.config.url)
        else:
            raise ValueError("Weaviate config must have either url or use_embed set")

    async def create_collection_async(self, collection_name: str) -> None:
        schema = SCHEMA.copy()
        schema["class"] = collection_name
        await asyncio.to_thread(self.client.schema.create_class, schema)

    async def get_collections_async(self) -> List[str]:
        schemas = await asyncio.to_thread(self.client.schema.get)
        return [schema["class"] for schema in schemas["classes"]]

    async def delete_collection_async(self, collection_name: str) -> bool:
        await asyncio.to_thread(self.client.schema.delete_class, collection_name)

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        collections = await self.get_collections_async()
        return collection_name in collections

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        weaviate_record = self.FieldMapper.sk_to_weaviate(vars(record))

        vector = weaviate_record.pop("vector", None)
        weaviate_id = weaviate.util.generate_uuid5(weaviate_record, collection_name)

        return await asyncio.to_thread(
            self.client.data_object.create,
            data_object=weaviate_record,
            uuid=weaviate_id,
            vector=vector,
            class_name=collection_name,
        )

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        def _upsert_batch_inner():
            results = []
            with self.client.batch as batch:
                for record in records:
                    weaviate_record = self.FieldMapper.sk_to_weaviate(vars(record))
                    vector = weaviate_record.pop("vector", None)
                    weaviate_id = weaviate.util.generate_uuid5(
                        weaviate_record, collection_name
                    )
                    batch.add_data_object(
                        data_object=weaviate_record,
                        uuid=weaviate_id,
                        vector=vector,
                        class_name=collection_name,
                    )
                    results.append(weaviate_id)

            return results

        return await asyncio.to_thread(_upsert_batch_inner)
