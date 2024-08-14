# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.connectors.ai.onnx.onnx_prompt_execution_settings import OnnxPromptExecutionSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OnnxTextCompletion(TextCompletionClientBase):
    """Onnx text completion service."""

    def __init__(
        self,
        ai_model_path: str,
    ) -> None:
        """Initializes a new instance of the OnnxTextCompletion class.

        Args:
            ai_model_path (str): Local path to the ONNX model.
        """
        super().__init__(
            ai_model_id=ai_model_path,
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
            settings (OnnxPromptExecutionSettings): Settings for the request.

        Returns:
            List[TextContent]: A list of TextContent objects representing the response(s) from the LLM.
        """
        if not isinstance(settings, OnnxPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OnnxPromptExecutionSettings)  # nosec

        raise NotImplementedError("OnnxTextCompletion.get_text_contents")

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
            settings (OnnxPromptExecutionSettings): Request settings.

        Yields:
            List[StreamingTextContent]: List of StreamingTextContent objects.
        """
        if not isinstance(settings, OnnxPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OnnxPromptExecutionSettings)  # nosec
        
        yield [
            StreamingTextContent(
                choice_index="",
                text="",
            )
        ]
        raise NotImplementedError("OnnxTextCompletion.get_streaming_text_contents")
        
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Create a request settings object."""
        return OnnxPromptExecutionSettings
