# Copyright (c) Microsoft. All rights reserved.

import json
import sys
from collections.abc import AsyncGenerator
from functools import partial
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockTextPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.bedrock_settings import BedrockSettings
from semantic_kernel.connectors.ai.bedrock.services.bedrock_base import BedrockBase
from semantic_kernel.connectors.ai.bedrock.services.model_provider.bedrock_model_provider import (
    get_text_completion_request_body,
    parse_streaming_text_completion_response,
    parse_text_completion_response,
)
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidRequestError
from semantic_kernel.utils.async_utils import run_in_executor
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_streaming_text_completion,
    trace_text_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class BedrockTextCompletion(BedrockBase, TextCompletionClientBase):
    """Amazon Bedrock Text Completion Service."""

    def __init__(
        self,
        model_id: str | None = None,
        service_id: str | None = None,
        runtime_client: Any | None = None,
        client: Any | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Amazon Bedrock Text Completion Service.

        Args:
            model_id: The Amazon Bedrock text model ID to use.
            service_id: The Service ID for the text completion service.
            runtime_client: The Amazon Bedrock runtime client to use.
            client: The Amazon Bedrock client to use.
            env_file_path: The path to the .env file to load settings from.
            env_file_encoding: The encoding of the .env file.
        """
        try:
            bedrock_settings = BedrockSettings(
                text_model_id=model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError("Failed to initialize the Amazon Bedrock Text Completion Service.") from e

        if bedrock_settings.text_model_id is None:
            raise ServiceInitializationError("The Amazon Bedrock Text Model ID is missing.")

        super().__init__(
            ai_model_id=bedrock_settings.text_model_id,
            service_id=service_id or bedrock_settings.text_model_id,
            runtime_client=runtime_client,
            client=client,
        )

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return BedrockTextPromptExecutionSettings

    @override
    @trace_text_completion(BedrockBase.MODEL_PROVIDER_NAME)
    async def _inner_get_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list[TextContent]:
        if not isinstance(settings, BedrockTextPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, BedrockTextPromptExecutionSettings)  # nosec

        request_body = get_text_completion_request_body(self.ai_model_id, prompt, settings)
        response_body = await self._async_invoke_model(request_body)
        return parse_text_completion_response(
            self.ai_model_id,
            json.loads(response_body.get("body").read()),
        )

    @override
    @trace_streaming_text_completion(BedrockBase.MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list[StreamingTextContent], Any]:
        # Not all models support streaming: check if the model supports streaming before proceeding
        model_info = await self.get_foundation_model_info(self.ai_model_id)
        if not model_info.get("responseStreamingSupported"):
            raise ServiceInvalidRequestError(f"The model {self.ai_model_id} does not support streaming.")

        if not isinstance(settings, BedrockTextPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, BedrockTextPromptExecutionSettings)  # nosec

        request_body = get_text_completion_request_body(self.ai_model_id, prompt, settings)
        response_stream = await self._async_invoke_model_stream(request_body)
        for event in response_stream.get("body"):
            chunk = event.get("chunk")
            yield [
                parse_streaming_text_completion_response(
                    self.ai_model_id,
                    json.loads(chunk.get("bytes").decode()),
                )
            ]

    # endregion

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

    async def _async_invoke_model_stream(self, request_body: dict) -> Any:
        """Invoke the model asynchronously and return a response stream."""
        return await run_in_executor(
            None,
            partial(
                self.bedrock_runtime_client.invoke_model_with_response_stream,
                body=json.dumps(request_body),
                modelId=self.ai_model_id,
                accept="application/json",
                contentType="application/json",
            ),
        )
