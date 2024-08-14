# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class OnnxPromptExecutionSettings(PromptExecutionSettings):
    """Onnx prompt execution settings."""

    do_sample: bool = True
    max_new_tokens: int = 256
    num_return_sequences: int = 1
    stop_sequences: Any = None
    pad_token_id: int = 50256
    eos_token_id: int = 50256
    temperature: float = 1.0
    top_p: float = 1.0
