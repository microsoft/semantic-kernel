# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class OpenAIAssistantInvocationOptions(KernelBaseModel):
    """OpenAI Assistant Invocation Settings class."""

    ai_model_id: str | None = None
    enable_code_interpreter: bool | None = Field(False)
    enable_file_search: bool | None = Field(False)
    enable_json_response: bool | None = Field(False)
    max_completion_tokens: int | None = Field(None)
    max_prompt_tokens: int | None = Field(None)
    parallel_tool_calls_enabled: bool | None = Field(False)
    truncation_message_count: int | None = Field(None)
    temperature: float | None = Field(None)
    top_p: float | None = Field(None)
    metadata: dict[str, str] | None = Field(default_factory=dict, max_length=16)
