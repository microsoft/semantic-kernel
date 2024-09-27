# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Optional

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.kernel_pydantic import KernelBaseModel


class PromptRenderingResult(KernelBaseModel):
    """
    Represents the result of rendering a prompt template.

    Attributes:
        rendered_prompt (str): The rendered prompt.
        ai_service (Any): The AI service that rendered the prompt.
        prompt_template (PromptTemplateConfig): The prompt template used to render the prompt.
    """

    rendered_prompt: str
    ai_service: Any
    execution_settings: Optional[PromptExecutionSettings] = Field(default_factory=PromptExecutionSettings)
