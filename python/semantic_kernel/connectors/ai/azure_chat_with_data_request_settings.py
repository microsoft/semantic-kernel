# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.semantic_functions.prompt_template_with_data_config import (
    PromptTemplateWithDataConfig,
)


@dataclass
class AzureChatWithDataRequestSettings(ChatRequestSettings):
    inputLanguage: str = None
    outputLanguage: str = None

    def update_from_completion_config(
        self, completion_config: "PromptTemplateWithDataConfig.CompletionConfig"
    ):
        super().update_from_completion_config(completion_config)
        if hasattr(completion_config, "inputLanguage"):
            self.inputLanguage = completion_config.inputLanguage
        if hasattr(completion_config, "outputLanguage"):
            self.outputLanguage = completion_config.outputLanguage

    @staticmethod
    def from_completion_config(
        completion_config: "PromptTemplateWithDataConfig.CompletionConfig",
    ) -> "AzureChatWithDataRequestSettings":
        settings = AzureChatWithDataRequestSettings()
        settings.update_from_completion_config(completion_config)
        return settings
