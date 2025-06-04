# Copyright (c) Microsoft. All rights reserved.

import importlib
from typing import TYPE_CHECKING, Any

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

if TYPE_CHECKING:
    from transformers import GenerationConfig


imported = importlib.import_module("transformers")
ready = imported is not None and hasattr(imported, "GenerationConfig")


class HuggingFacePromptExecutionSettings(PromptExecutionSettings):
    """Hugging Face prompt execution settings."""

    do_sample: bool = True
    max_new_tokens: int = 256
    num_return_sequences: int = 1
    stop_sequences: Any = None
    pad_token_id: int = 50256
    eos_token_id: int = 50256
    temperature: float = 1.0
    top_p: float = 1.0

    def get_generation_config(self) -> "GenerationConfig":
        """Get the generation config."""
        if not ready:
            raise ImportError("transformers is not installed.")
        from transformers import GenerationConfig

        return GenerationConfig(
            **self.model_dump(
                include={"max_new_tokens", "pad_token_id", "eos_token_id", "temperature", "top_p"},
                exclude_unset=False,
                exclude_none=True,
                by_alias=True,
            )
        )

    def prepare_settings_dict(self, **kwargs) -> dict[str, Any]:
        """Prepare the settings dictionary."""
        gen_config = self.get_generation_config()
        settings = {
            "generation_config": gen_config,
            "num_return_sequences": self.num_return_sequences,
            "do_sample": self.do_sample,
        }
        settings.update(kwargs)
        return settings
