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

from semantic_kernel.connectors.ai.astraflow.prompt_execution_settings.astraflow_prompt_execution_settings import (
    AstraflowEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.astraflow.services.astraflow_handler import AstraflowHandler
from semantic_kernel.connectors.ai.astraflow.services.astraflow_model_types import AstraflowModelTypes
from semantic_kernel.connectors.ai.astraflow.settings.astraflow_settings import AstraflowSettings
from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

logger: logging.Logger = logging.getLogger(__name__)

# Default Astraflow embedding model when none is specified
DEFAULT_ASTRAFLOW_EMBEDDING_MODEL = "BAAI/bge-m3"


class AstraflowTextEmbedding(AstraflowHandler, EmbeddingGeneratorBase):
    """Astraflow text embedding service.

    Astraflow (by UCloud / 优刻得) is an OpenAI-compatible model aggregation
    platform supporting 200+ models.  See https://astraflow.ucloud.cn/
    """

    def __init__(
        self,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
        service_id: str | None = None,
    ) -> None:
        """Initialize an AstraflowTextEmbedding service.

        Args:
            ai_model_id (str | None): Astraflow embedding model ID, e.g. ``BAAI/bge-m3``.
                Defaults to ``DEFAULT_ASTRAFLOW_EMBEDDING_MODEL`` when not provided.
            api_key (str | None): Astraflow API key.  When provided it overrides the
                ``ASTRAFLOW_API_KEY`` / ``ASTRAFLOW_CN_API_KEY`` environment variables.
            base_url (str | None): Custom API base URL.  Defaults to the global endpoint
                ``https://api-us-ca.umodelverse.ai/v1``.  Set to
                ``https://api.modelverse.cn/v1`` to use the China endpoint.
            client (AsyncOpenAI | None): An existing OpenAI-compatible client to use.
            env_file_path (str | None): Path to a .env file used as a fallback for
                environment variables.
            service_id (str | None): Service ID for the model.
        """
        try:
            astraflow_settings = AstraflowSettings(
                api_key=api_key,
                base_url=base_url,
                embedding_model_id=ai_model_id,
                env_file_path=env_file_path,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Astraflow settings.", ex) from ex

        if not astraflow_settings.embedding_model_id:
            astraflow_settings.embedding_model_id = DEFAULT_ASTRAFLOW_EMBEDDING_MODEL
            logger.warning(f"Default Astraflow embedding model set as: {astraflow_settings.embedding_model_id}")

        # Resolve effective API key
        effective_api_key = astraflow_settings.api_key or astraflow_settings.cn_api_key
        if not effective_api_key:
            logger.warning(
                "No Astraflow API key found. "
                "Set ASTRAFLOW_API_KEY (global) or ASTRAFLOW_CN_API_KEY (China). "
                "Inference may fail."
            )

        if not client:
            client = AsyncOpenAI(
                api_key=effective_api_key.get_secret_value() if effective_api_key else None,
                base_url=astraflow_settings.base_url,
            )

        super().__init__(
            ai_model_id=astraflow_settings.embedding_model_id,
            api_key=effective_api_key.get_secret_value() if effective_api_key else None,
            ai_model_type=AstraflowModelTypes.EMBEDDING,
            service_id=service_id or astraflow_settings.embedding_model_id,
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
        """Return embeddings for the given texts in the unedited format.

        Args:
            texts: The texts to generate embeddings for.
            settings: Prompt execution settings.  A new
                ``AstraflowEmbeddingPromptExecutionSettings`` is created when
                omitted.
            batch_size: Number of texts to process per API call.
            kwargs: Additional keyword arguments applied to the settings.
        """
        if not settings:
            settings = AstraflowEmbeddingPromptExecutionSettings(ai_model_id=self.ai_model_id)
        else:
            if not isinstance(settings, AstraflowEmbeddingPromptExecutionSettings):
                settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AstraflowEmbeddingPromptExecutionSettings)  # nosec
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        for key, value in kwargs.items():
            setattr(settings, key, value)

        raw_embeddings: list[Any] = []
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

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return AstraflowEmbeddingPromptExecutionSettings

    @classmethod
    def from_dict(cls: type["AstraflowTextEmbedding"], settings: dict[str, Any]) -> "AstraflowTextEmbedding":
        """Initialize an Astraflow text embedding service from a dictionary of settings.

        Args:
            settings: A dictionary of settings for the service.
        """
        return cls(
            ai_model_id=settings.get("ai_model_id"),
            api_key=settings.get("api_key"),
            env_file_path=settings.get("env_file_path"),
            service_id=settings.get("service_id"),
        )
