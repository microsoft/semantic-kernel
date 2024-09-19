# Copyright (c) Microsoft. All rights reserved.

import json
import os
from collections.abc import AsyncGenerator
from typing import Any

import onnxruntime_genai as OnnxRuntimeGenAi

from semantic_kernel.connectors.ai.onnx.onnx_gen_ai_prompt_execution_settings import OnnxGenAIPromptExecutionSettings
from semantic_kernel.contents import ImageContent
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidResponseError
from semantic_kernel.kernel_pydantic import KernelBaseModel


class OnnxGenAICompletionBase(KernelBaseModel):
    """Base class for OnnxGenAI Completion services."""

    model: Any
    tokenizer: Any
    tokenizer_stream: Any
    enable_multi_modality: bool = False

    def __init__(self, ai_model_path: str, **kwargs) -> None:
        """Creates a new instance of the OnnxGenAICompletionBase class, loads model & tokenizer.

        Args:
            ai_model_path (str): Path to Onnx Model.
            **kwargs: Additional keyword arguments.

        Raises:
            ServiceInitializationError: When model cannot be loaded
        """
        try:
            json_gen_ai_config = os.path.join(ai_model_path + "/genai_config.json")
            with open(json_gen_ai_config) as file:
                config: dict = json.load(file)
                enable_multi_modality = "vision" in config.get("model", {})
                model = OnnxRuntimeGenAi.Model(ai_model_path)
                tokenizer = model.create_multimodal_processor() if enable_multi_modality else OnnxRuntimeGenAi.Tokenizer(model)
                tokenizer_stream = tokenizer.create_stream()
        except Exception as e:
            raise ServiceInitializationError(f"Failed to initialize OnnxTextCompletion service: {e}")

        super().__init__(
            model=model,
            tokenizer=tokenizer,
            tokenizer_stream=tokenizer_stream,
            enable_multi_modality=enable_multi_modality,
            **kwargs,
        )

    def _prepare_input_params(
        self, prompt: str, settings: OnnxGenAIPromptExecutionSettings, image: ImageContent | None = None
    ) -> Any:
        params = OnnxRuntimeGenAi.GeneratorParams(self.model)
        params.set_search_options(**settings.prepare_settings_dict())
        if not self.enable_multi_modality:
            input_tokens = self.tokenizer.encode(prompt)
        else:
            if image is not None:
                # With the use of Pybind there is currently no way to load images from bytes
                # We can only open images from a file path currently
                image = OnnxRuntimeGenAi.Images.open(str(image.uri))
            input_tokens = self.tokenizer(prompt, images=image)
        params.set_inputs(input_tokens)
        return params

    async def _generate_next_token(
        self,
        prompt: str,
        settings: OnnxGenAIPromptExecutionSettings,
        image: ImageContent | None = None,
    ) -> AsyncGenerator[str, Any]:
        try:
            params = self._prepare_input_params(prompt, settings, image)
            generator = OnnxRuntimeGenAi.Generator(self.model, params)

            while not generator.is_done():
                generator.compute_logits()
                generator.generate_next_token()
                new_token = self.tokenizer_stream.decode(generator.get_next_tokens()[0])
                yield new_token
        except Exception as e:
            raise ServiceInvalidResponseError("Failed Inference with ONNX") from e
