# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class OpenAIAssistantExecutionSettings(KernelBaseModel):
    max_completion_tokens: int | None = Field(None)
    max_prompt_tokens: int | None = Field(None)
    parallel_tool_calls_enabled: bool | None = Field(False)
    truncation_message_count: int | None = Field(None)

    # tool_choice_behavior
