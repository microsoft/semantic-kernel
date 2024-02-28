# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class OllamaPromptExecutionSettings(PromptExecutionSettings):
    ai_model_id: str = Field("", serialization_alias="model")
    format: Optional[Literal["json"]] = None
    options: Optional[Dict[str, Any]] = None
    stream: bool = False


class OllamaTextPromptExecutionSettings(OllamaPromptExecutionSettings):
    prompt: Optional[str] = None
    context: Optional[str] = None
    system: Optional[str] = None
    template: Optional[str] = None
    raw: bool = False


class OllamaChatPromptExecutionSettings(OllamaPromptExecutionSettings):
    messages: Optional[List[Dict[str, str]]] = None
