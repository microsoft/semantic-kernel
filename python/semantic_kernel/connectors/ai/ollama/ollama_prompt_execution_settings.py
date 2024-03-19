# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class OllamaPromptExecutionSettings(PromptExecutionSettings):
    ai_model_id: str = Field("", serialization_alias="model")
    format: Optional[Literal["json"]] = None
    options: Optional[Dict[str, Any]] = None
    stream: bool = False

    def prepare_settings_dict(self, **kwargs) -> Dict[str, Any]:
        settings = super().prepare_settings_dict(**kwargs)
        # Despite the `serialization_alias` above, it seems like the 'model' is often not set.
        if 'model' not in settings:
            settings['model'] = self.ai_model_id
        return settings


class OllamaTextPromptExecutionSettings(OllamaPromptExecutionSettings):
    prompt: Optional[str] = None
    context: Optional[str] = None
    system: Optional[str] = None
    template: Optional[str] = None
    raw: bool = False


class OllamaChatPromptExecutionSettings(OllamaPromptExecutionSettings):
    messages: Optional[List[Dict[str, str]]] = None
