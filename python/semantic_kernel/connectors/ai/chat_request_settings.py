# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from semantic_kernel.semantic_functions.prompt_template_config import (
        PromptTemplateConfig,
    )


@dataclass
class ChatRequestSettings:
    temperature: float = 0.0
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    number_of_responses: int = 1
    max_tokens: int = 256
    token_selection_biases: Dict[int, int] = field(default_factory=dict)

    def update_from_completion_config(
        self, completion_config: "PromptTemplateConfig.CompletionConfig"
    ):
        self.temperature = completion_config.temperature
        self.top_p = completion_config.top_p
        self.presence_penalty = completion_config.presence_penalty
        self.frequency_penalty = completion_config.frequency_penalty
        self.number_of_responses = completion_config.number_of_responses
        self.max_tokens = completion_config.max_tokens

    @staticmethod
    def from_completion_config(
        completion_config: "PromptTemplateConfig.CompletionConfig",
    ) -> "ChatRequestSettings":
        settings = ChatRequestSettings()
        settings.update_from_completion_config(completion_config)
        return settings
