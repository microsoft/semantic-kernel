# Copyright (c) Microsoft. All rights reserved.


from typing import Any

from pydantic import Field

from semantic_kernel.agents.open_ai.open_ai_assistant_execution_options import OpenAIAssistantExecutionOptions
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class OpenAIAssistantDefinition(KernelBaseModel):
    """OpenAI Assistant Definition class."""

    ai_model_id: str | None = None
    description: str | None = None
    id: str | None = Field(None)
    instructions: str | None = Field(None)
    name: str | None = Field(None)
    enable_code_interpreter: bool | None = Field(False)
    enable_file_search: bool | None = Field(False)
    enable_json_response: bool | None = Field(False)
    file_ids: list[str] | None = Field(default_factory=list, max_length=20)
    temperature: float | None = Field(None)
    top_p: float | None = Field(None)
    vector_store_ids: list[str] | None = Field(default_factory=list, max_length=1)
    metadata: dict[str, Any] | None = Field(default_factory=dict, max_length=16)
    exection_options: OpenAIAssistantExecutionOptions | None = Field(None)
