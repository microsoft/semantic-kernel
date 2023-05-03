from dataclasses import dataclass
from typing import Optional
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
import weaviate
from semantic_kernel.utils.null_logger import NullLogger
from logging import Logger
from weaviate.embedded import EmbeddedOptions


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
