# Copyright (c) Microsoft. All rights reserved.
<<<<<<< main
=======

from typing import Any, Dict, List, Literal, Optional
>>>>>>> ms/small_fixes

from typing import Any, Literal

from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)


class OllamaPromptExecutionSettings(PromptExecutionSettings):
<<<<<<< main
    """Settings for Ollama prompt execution."""

    format: Literal["json"] | None = None
    options: dict[str, Any] | None = None

    # TODO(@taochen): Add individual properties for execution settings and
    # convert them to the appropriate types in the options dictionary.
=======
    ai_model_id: str = Field("", serialization_alias="model")
    format: Optional[Literal["json"]] = None
    options: Optional[Dict[str, Any]] = None
    stream: bool = False
>>>>>>> ms/small_fixes


class OllamaTextPromptExecutionSettings(OllamaPromptExecutionSettings):
    """Settings for Ollama text prompt execution."""

    system: str | None = None
    template: str | None = None
    context: str | None = None
    raw: bool | None = None


class OllamaChatPromptExecutionSettings(OllamaPromptExecutionSettings):
    """Settings for Ollama chat prompt execution."""


class OllamaEmbeddingPromptExecutionSettings(OllamaPromptExecutionSettings):
    """Settings for Ollama embedding prompt execution."""
