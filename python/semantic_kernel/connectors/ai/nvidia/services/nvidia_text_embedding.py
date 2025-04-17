# Copyright (c) Microsoft. All rights reserved.

import asyncio
import copy
import logging
import sys
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from numpy import array, ndarray
from openai import AsyncOpenAI
from pydantic import ValidationError

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.nvidia.prompt_execution_settings.nvidia_prompt_execution_settings import (
    NvidiaEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.nvidia.services.nvidia_handler import NvidiaHandler
from semantic_kernel.connectors.ai.nvidia.services.nvidia_model_types import NvidiaModelTypes
from semantic_kernel.connectors.ai.nvidia.settings.nvidia_settings import NvidiaSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class NvidiaTextEmbedding(NvidiaHandler, EmbeddingGeneratorBase):
    """Nvidia text embedding service."""

    def __init__(
        self,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
        service_id: str | None = None,
    ) -> None:
        """Initializes a new instance of the NvidiaTextEmbedding class.

        Args:
            ai_model_id (str): NVIDIA model card string, see
                https://Nvidia.co/sentence-transformers
            api_key: NVIDIA API key, see https://console.NVIDIA.com/settings/keys
                (Env var NVIDIA_API_KEY)
            base_url: HttpsUrl | None - base_url: The url of the NVIDIA endpoint. The base_url consists of the endpoint,
                and more information refer https://docs.api.nvidia.com/nim/reference/
                use endpoint if you only want to supply the endpoint.
                (Env var NVIDIA_BASE_URL)
            client (Optional[AsyncOpenAI]): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as
                a fallback to environment variables. (Optional)
            service_id (str): Service ID for the model. (optional)
        """
        try:
            nvidia_settings = NvidiaSettings(
                api_key=api_key,
                base_url=base_url,
                embedding_model_id=ai_model_id,
                env_file_path=env_file_path,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create NVIDIA settings.", ex) from ex
        if not nvidia_settings.embedding_model_id:
            nvidia_settings.embedding_model_id = "nvidia/nv-embedqa-e5-v5"
            logger.warning(f"Default embedding model set as: {nvidia_settings.embedding_model_id}")
        if not nvidia_settings.api_key:
            logger.warning("API_KEY is missing, inference may fail.")
        if not client:
            client = AsyncOpenAI(api_key=nvidia_settings.api_key.get_secret_value(), base_url=nvidia_settings.base_url)
        super().__init__(
            ai_model_id=nvidia_settings.embedding_model_id,
            api_key=nvidia_settings.api_key.get_secret_value() if nvidia_settings.api_key else None,
            ai_model_type=NvidiaModelTypes.EMBEDDING,
            service_id=service_id or nvidia_settings.embedding_model_id,
            env_file_path=env_file_path,
            client=client,
        )

    @override
    async def generate_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        batch_size: int | None = None,
        **kwargs: Any,
    ) -> ndarray:
        raw_embeddings = await self.generate_raw_embeddings(texts, settings, batch_size, **kwargs)
        return array(raw_embeddings)

    @override
    async def generate_raw_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        batch_size: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Returns embeddings for the given texts in the unedited format.

        Args:
            texts (List[str]): The texts to generate embeddings for.
            settings (NvidiaEmbeddingPromptExecutionSettings): The settings to use for the request.
            batch_size (int): The batch size to use for the request.
            kwargs (Dict[str, Any]): Additional arguments to pass to the request.
        """
        if not settings:
            settings = NvidiaEmbeddingPromptExecutionSettings(ai_model_id=self.ai_model_id)
        else:
            if not isinstance(settings, NvidiaEmbeddingPromptExecutionSettings):
                settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, NvidiaEmbeddingPromptExecutionSettings)  # nosec
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        for key, value in kwargs.items():
            setattr(settings, key, value)

        # move input_type and truncate to extra-body
        if not settings.extra_body:
            settings.extra_body = {}
        settings.extra_body.setdefault("input_type", settings.input_type)
        if settings.truncate is not None:
            settings.extra_body.setdefault("truncate", settings.truncate)

        raw_embeddings = []
        tasks = []

        batch_size = batch_size or len(texts)
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_settings = copy.deepcopy(settings)
            batch_settings.input = batch
            tasks.append(self._send_request(settings=batch_settings))

        results = await asyncio.gather(*tasks)
        for raw_embedding in results:
            assert isinstance(raw_embedding, list)  # nosec
            raw_embeddings.extend(raw_embedding)

        return raw_embeddings

    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return NvidiaEmbeddingPromptExecutionSettings

    @classmethod
    def from_dict(cls: type["NvidiaTextEmbedding"], settings: dict[str, Any]) -> "NvidiaTextEmbedding":
        """Initialize an Open AI service from a dictionary of settings.

        Args:
            settings: A dictionary of settings for the service.
        """
        return cls(
            ai_model_id=settings.get("ai_model_id"),
            api_key=settings.get("api_key"),
            env_file_path=settings.get("env_file_path"),
            service_id=settings.get("service_id"),
        )
