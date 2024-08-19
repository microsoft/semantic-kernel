# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import onnxruntime_genai as OnnxRuntimeGenAi

from semantic_kernel.connectors.ai.onnx.onnx_prompt_execution_settings import OnnxTextPromptExecutionSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidResponseError
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OnnxTextCompletion(TextCompletionClientBase):
    """Onnx text completion service."""
    
    model: Any
    tokenizer: Any
    
    def __init__(
        self,
        ai_model_path: str,
        ai_model_id: str | None = None,
    ) -> None:
        """Initializes a new instance of the OnnxTextCompletion class.

        Args:
            ai_model_path (str): Local path to the ONNX model Folder.
            ai_model_id (str, optional): The ID of the AI model. Defaults to None.
        """
        if ai_model_id is None:
            ai_model_id = ai_model_path
            
        try:
            model = OnnxRuntimeGenAi.Model(ai_model_path)
            tokenizer = OnnxRuntimeGenAi.Tokenizer(model)
        except Exception as e:
            raise ServiceInitializationError(f"Failed to initialize OnnxTextCompletion service: {e}")
            
        super().__init__(
            ai_model_id=ai_model_id,
            model=model,
            tokenizer=tokenizer,
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
            settings (OnnxTextPromptExecutionSettings): Settings for the request.

        Returns:
            List[TextContent]: A list of TextContent objects representing the response(s) from the LLM.
        """
        if not isinstance(settings, OnnxTextPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OnnxTextPromptExecutionSettings)  # nosec

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
            settings (OnnxTextPromptExecutionSettings): Request settings.

        Yields:
            List[StreamingTextContent]: List of StreamingTextContent objects.
        """
        if not isinstance(settings, OnnxTextPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OnnxTextPromptExecutionSettings)  # nosec
        
        async for new_token in self._generate_next_token(prompt, settings):
            yield [
                StreamingTextContent(
                    choice_index=0, inner_content=new_token, text=new_token, ai_model_id=self.ai_model_id
                )
            ]
                
        return
    
    async def _generate_next_token(
        self, 
        prompt: str, 
        settings: OnnxTextPromptExecutionSettings
    ) -> AsyncGenerator[str, Any]:
        try:
            input_tokens = self.tokenizer.encode(prompt)
            params = OnnxRuntimeGenAi.GeneratorParams(self.model)
            params.set_search_options(**settings.prepare_settings_dict())
            params.input_ids = input_tokens
            generator = OnnxRuntimeGenAi.Generator(self.model, params)
            
            tokenizer_stream = self.tokenizer.create_stream()
            
            while not generator.is_done():
                generator.compute_logits()
                generator.generate_next_token()
                new_token = tokenizer_stream.decode(generator.get_next_tokens()[0])
                yield new_token
        except Exception as e:
            raise ServiceInvalidResponseError("Failed to get text content with ONNX") from e
        
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Create a request settings object."""
        return OnnxTextPromptExecutionSettings
