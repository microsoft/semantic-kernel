# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import sys
from functools import partial
from typing import TYPE_CHECKING, Any

from numpy import array, ndarray
from pydantic import ValidationError

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import (
    BedrockEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.bedrock.bedrock_settings import BedrockSettings
from semantic_kernel.connectors.ai.bedrock.services.bedrock_base import BedrockBase
from semantic_kernel.connectors.ai.bedrock.services.model_provider.bedrock_model_provider import (
    get_text_embedding_request_body,
    parse_text_embedding_response,
)
from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidRequestError
from semantic_kernel.utils.async_utils import run_in_executor

if TYPE_CHECKING:
    pass


class BedrockTextEmbedding(BedrockBase, EmbeddingGeneratorBase):
    """Amazon Bedrock Text Embedding Service."""

    def __init__(
        self,
        model_id: str | None = None,
        service_id: str | None = None,
        runtime_client: Any | None = None,
        client: Any | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Amazon Bedrock Text Embedding Service.

        Args:
            model_id: The Amazon Bedrock text embedding model ID to use.
            service_id: The Service ID for the text embedding service.
            runtime_client: The Amazon Bedrock runtime client to use.
            client: The Amazon Bedrock client to use.
            env_file_path: The path to the .env file to load settings from.
            env_file_encoding: The encoding of the .env file.
        """
        try:
            bedrock_settings = BedrockSettings(
                embedding_model_id=model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError("Failed to initialize the Amazon Bedrock Text Embedding Service.") from e

        if bedrock_settings.embedding_model_id is None:
            raise ServiceInitializationError("The Amazon Bedrock Text Embedding Model ID is missing.")

        super().__init__(
            ai_model_id=bedrock_settings.embedding_model_id,
            service_id=service_id or bedrock_settings.embedding_model_id,
            runtime_client=runtime_client,
            client=client,
        )

    @override
    async def generate_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> ndarray:
        model_info = await self.get_foundation_model_info(self.ai_model_id)
        if "TEXT" not in model_info.get("inputModalities", []):
            # Image embedding is not supported yet in SK
            raise ServiceInvalidRequestError(f"The model {self.ai_model_id} does not support text input.")
        if "EMBEDDING" not in model_info.get("outputModalities", []):
            raise ServiceInvalidRequestError(f"The model {self.ai_model_id} does not support embedding output.")

        if not settings:
            settings = BedrockEmbeddingPromptExecutionSettings()
        elif not isinstance(settings, BedrockEmbeddingPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, BedrockEmbeddingPromptExecutionSettings)  # nosec

        results = await asyncio.gather(*[
            self._async_invoke_model(get_text_embedding_request_body(self.ai_model_id, text, settings))
            for text in texts
        ])

        return array([
            array(parse_text_embedding_response(self.ai_model_id, json.loads(result.get("body").read())))
            for result in results
        ])

    @override
    def get_prompt_execution_settings_class(
        self,
    ) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return BedrockEmbeddingPromptExecutionSettings

    async def _async_invoke_model(self, request_body: dict) -> Any:
        """Invoke the model asynchronously."""
        return await run_in_executor(
            None,
            partial(
                self.bedrock_runtime_client.invoke_model,
                body=json.dumps(request_body),
                modelId=self.ai_model_id,
                accept="application/json",
                contentType="application/json",
            ),
        )
