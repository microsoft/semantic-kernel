# Copyright (c) Microsoft. All rights reserved.

import json
import os
from collections.abc import AsyncGenerator
from typing import Any

from semantic_kernel.connectors.ai.onnx.onnx_gen_ai_prompt_execution_settings import OnnxGenAIPromptExecutionSettings
from semantic_kernel.contents import AudioContent, ImageContent
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidResponseError
from semantic_kernel.kernel_pydantic import KernelBaseModel

try:
    import onnxruntime_genai as OnnxRuntimeGenAi

    ready = True
except ImportError:
    ready = False


class OnnxGenAICompletionBase(KernelBaseModel):
    """Base class for OnnxGenAI Completion services."""

    model: Any
    tokenizer: Any
    tokenizer_stream: Any
    enable_multi_modality: bool = False

    def __init__(self, ai_model_path: str, **kwargs) -> None:
        """Creates a new instance of the OnnxGenAICompletionBase class, loads model & tokenizer.

        Args:
            ai_model_path : Path to Onnx Model.
            **kwargs: Additional keyword arguments.

        Raises:
            ServiceInitializationError: When model cannot be loaded
        """
        if not ready:
            raise ImportError("onnxruntime-genai is not installed.")
        try:
            json_gen_ai_config = os.path.join(ai_model_path + "/genai_config.json")
            with open(json_gen_ai_config) as file:
                config: dict = json.load(file)
                enable_multi_modality = "vision" in config.get("model", {})
                model = OnnxRuntimeGenAi.Model(ai_model_path)
                if enable_multi_modality:
                    tokenizer = model.create_multimodal_processor()
                else:
                    tokenizer = OnnxRuntimeGenAi.Tokenizer(model)
                tokenizer_stream = tokenizer.create_stream()
        except Exception as ex:
            raise ServiceInitializationError("Failed to initialize OnnxCompletion service", ex) from ex

        super().__init__(
            model=model,
            tokenizer=tokenizer,
            tokenizer_stream=tokenizer_stream,
            enable_multi_modality=enable_multi_modality,
            **kwargs,
        )

    async def _generate_next_token_async(
        self,
        prompt: str,
        settings: OnnxGenAIPromptExecutionSettings,
        images: list[ImageContent] | None = None,
        audios: list[AudioContent] | None = None,
    ) -> AsyncGenerator[list[str], Any]:
        try:
            params = OnnxRuntimeGenAi.GeneratorParams(self.model)
            params.set_search_options(**settings.prepare_settings_dict())
            generator = OnnxRuntimeGenAi.Generator(self.model, params)
            if not self.enable_multi_modality:
                input_tokens = self.tokenizer.encode(prompt)
                generator.append_tokens(input_tokens)
            else:
                # With the use of Pybind in ONNX there is currently no way to load images from bytes
                # We can only open images & audios from a file path currently
                if images is not None:
                    images = OnnxRuntimeGenAi.Images.open([str(image.uri) for image in images])
                if audios is not None:
                    audios = OnnxRuntimeGenAi.Audios.open([str(audio.uri) for audio in audios])
                input_tokens = self.tokenizer(prompt, images=images, audios=audios)
                generator.set_inputs(input_tokens)

            while not generator.is_done():
                generator.generate_next_token()
                new_token_choices = [self.tokenizer_stream.decode(token) for token in generator.get_next_tokens()]
                yield new_token_choices
            del generator
        except Exception as ex:
            raise ServiceInvalidResponseError("Failed Inference with ONNX", ex) from ex

    async def _generate_next_token(
        self,
        prompt: str,
        settings: OnnxGenAIPromptExecutionSettings,
        images: list[ImageContent] | None = None,
        audios: list[AudioContent] | None = None,
    ):
        token_choices: list[str] = []
        async for new_token_choice in self._generate_next_token_async(prompt, settings, images, audios=audios):
            # zip only works if the lists are the same length
            if len(token_choices) == 0:
                token_choices = new_token_choice
            else:
                token_choices = [old_token + new_token for old_token, new_token in zip(token_choices, new_token_choice)]
        return token_choices
