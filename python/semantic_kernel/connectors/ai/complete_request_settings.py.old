# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from semantic_kernel.semantic_functions.prompt_template_config import (
        PromptTemplateConfig,
    )


@dataclass
class CompleteRequestSettings:
    temperature: float = 0.0
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    max_tokens: int = 256
    stop_sequences: List[str] = field(default_factory=list)
    number_of_responses: int = 1
    logprobs: int = 0
    token_selection_biases: Dict[int, int] = field(default_factory=dict)
    chat_system_prompt: str = "Assistant is a large language model."

    def update_from_completion_config(
        self, completion_config: "PromptTemplateConfig.CompletionConfig"
    ):
        self.temperature = completion_config.temperature
        self.top_p = completion_config.top_p
        self.presence_penalty = completion_config.presence_penalty
        self.frequency_penalty = completion_config.frequency_penalty
        self.max_tokens = completion_config.max_tokens
        self.stop_sequences = completion_config.stop_sequences
        self.number_of_responses = completion_config.number_of_responses
        self.token_selection_biases = completion_config.token_selection_biases

        if completion_config.chat_system_prompt:
            self.chat_system_prompt = completion_config.chat_system_prompt

    @staticmethod
    def from_completion_config(
        completion_config: "PromptTemplateConfig.CompletionConfig",
    ) -> "CompleteRequestSettings":
        settings = CompleteRequestSettings()
        settings.update_from_completion_config(completion_config)
        return settings
