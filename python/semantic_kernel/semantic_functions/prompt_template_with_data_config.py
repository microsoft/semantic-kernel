# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from semantic_kernel.semantic_functions.prompt_template_config import PromptTemplateConfig


@dataclass
class PromptTemplateWithDataConfig(PromptTemplateConfig):
    @dataclass
    class CompletionConfig(PromptTemplateConfig.CompletionConfig):
        inputLanguage: str = None
        outputLanguage: str = None

    @staticmethod
    def from_dict(data: dict) -> "PromptTemplateWithDataConfig":
        config = super().from_dict(data)

        completion_keys = [
            "inputLanguage",
            "outputLanguage"
        ]
        for comp_key in completion_keys:
            if comp_key in data["completion"]:
                setattr(config.completion, comp_key, data["completion"][comp_key])

        return config

    @staticmethod
    def from_completion_parameters(
        temperature: float = 0.0,
        top_p: float = 1.0,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        max_tokens: int = 256,
        number_of_responses: int = 1,
        stop_sequences: List[str] = [],
        token_selection_biases: Dict[int, int] = {},
        chat_system_prompt: str = None,
        function_call: Optional[str] = None,
        inputLanguage = None,
        outputLanguage = None
    ) -> "PromptTemplateWithDataConfig":
        config = PromptTemplateConfig()
        config.completion.temperature = temperature
        config.completion.top_p = top_p
        config.completion.presence_penalty = presence_penalty
        config.completion.frequency_penalty = frequency_penalty
        config.completion.max_tokens = max_tokens
        config.completion.number_of_responses = number_of_responses
        config.completion.stop_sequences = stop_sequences
        config.completion.token_selection_biases = token_selection_biases
        config.completion.chat_system_prompt = chat_system_prompt
        config.completion.function_call = function_call
        config.completion.inputLanguage = inputLanguage
        config.completion.outputLanguage = outputLanguage
        return config
