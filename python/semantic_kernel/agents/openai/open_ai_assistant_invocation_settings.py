# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class OpenAIAssistantInvocationSettings(KernelBaseModel):
    ai_model_id: str | None = None
    enable_code_interpreter: bool = Field(False)
    enable_file_search: bool = Field(False)
    enable_json_response: bool = Field(False)
    max_completion_tokens: int | None = Field(None)
    max_prompt_tokens: int | None = Field(None)
    parallel_tool_calls_enabled: bool | None = Field(False)
    truncation_message_count: int | None = Field(None)
    temperature: float = Field(None)
    top_p: float = Field(None)
    metadata: dict[str, str] = Field(default_factory=dict)

    # tool call behavior
