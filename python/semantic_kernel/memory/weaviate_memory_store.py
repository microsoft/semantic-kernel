import asyncio
from dataclasses import dataclass
from logging import Logger
from typing import Optional

import weaviate
from weaviate.embedded import EmbeddedOptions

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
