# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pydantic import ValidationError

from semantic_kernel.connectors.ai.onnx.onnx_gen_ai_prompt_execution_settings import OnnxGenAIPromptExecutionSettings
from semantic_kernel.connectors.ai.onnx.onnx_gen_ai_settings import OnnxGenAISettings
from semantic_kernel.connectors.ai.onnx.services.onnx_gen_ai_completion_base import OnnxGenAICompletionBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import ServiceInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OnnxGenAITextCompletion(TextCompletionClientBase, OnnxGenAICompletionBase):
    """OnnxGenAI text completion service."""

    def __init__(
        self,
        ai_model_path: str | None = None,
        ai_model_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the OnnxGenAITextCompletion class.

        Args:
            ai_model_path (str | None): Local path to the ONNX model Folder.
            ai_model_id (str, optional): The ID of the AI model. Defaults to None.
            env_file_path (str | None): Use the environment settings file as a fallback
                to environment variables.
            env_file_encoding (str | None): The encoding of the environment settings file.
        """
        try:
            settings = OnnxGenAISettings.create(
                model_path=ai_model_path,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Invalid settings for OnnxGenAITextCompletion: {e}")

        if ai_model_id is None:
            ai_model_id = settings.model_path

        super().__init__(
            ai_model_id=ai_model_id,
            ai_model_path=settings.model_path,
        )

    @override
    async def get_text_contents(
        self,
        prompt: str,
        settings: PromptExecutionSettings,
    ) -> list[TextContent]:
        """This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (OnnxGenAIPromptExecutionSettings): Settings for the request.

        Returns:
            List[TextContent]: A list of TextContent objects representing the response(s) from the LLM.
        """
        if not isinstance(settings, OnnxGenAIPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OnnxGenAIPromptExecutionSettings)  # nosec

        new_tokens = ""
        async for new_token in self._generate_next_token(prompt, settings):
            new_tokens += new_token

        return [
            TextContent(
                text=new_tokens,
                ai_model_id=self.ai_model_id,
            )
        ]

    @override
    async def get_streaming_text_contents(
        self,
        prompt: str,
        settings: PromptExecutionSettings,
    ) -> AsyncGenerator[list[StreamingTextContent], Any]:
        """Streams a text completion using a Onnx model.

        Note that this method does not support multiple responses.

        Args:
            prompt (str): Prompt to complete.
            settings (OnnxGenAIPromptExecutionSettings): Request settings.

        Yields:
            List[StreamingTextContent]: List of StreamingTextContent objects.
        """
        if not isinstance(settings, OnnxGenAIPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OnnxGenAIPromptExecutionSettings)  # nosec

        async for new_token in self._generate_next_token(prompt, settings):
            yield [
                StreamingTextContent(
                    choice_index=0, inner_content=new_token, text=new_token, ai_model_id=self.ai_model_id
                )
            ]

        return

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Create a request settings object."""
        return OnnxGenAIPromptExecutionSettings
