# Copyright (c) Microsoft. All rights reserved.

<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


class PromptRenderingResult(KernelBaseModel):
    """Represents the result of rendering a prompt template.
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
from typing import Any, Optional

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.kernel_pydantic import KernelBaseModel


class PromptRenderingResult(KernelBaseModel):
    """
    Represents the result of rendering a prompt template.
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    Attributes:
        rendered_prompt (str): The rendered prompt.
        ai_service (Any): The AI service that rendered the prompt.
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        execution_settings (PromptExecutionSettings): The execution settings for the prompt.
        function_result (FunctionResult): The result of executing the prompt.
    """

    rendered_prompt: str
    ai_service: AIServiceClientBase
    execution_settings: PromptExecutionSettings
    function_result: FunctionResult | None = None
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
        prompt_template (PromptTemplateConfig): The prompt template used to render the prompt.
    """

    rendered_prompt: str
    ai_service: Any
    execution_settings: Optional[PromptExecutionSettings] = Field(default_factory=PromptExecutionSettings)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
