# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class OpenAIAssistantDefinition(KernelBaseModel):
    ai_model_id: str | None = None
    description: str | None = None
    id: str | None = Field(None)
    instructions: str | None = Field(None)
    name: str | None = Field(None)
    enable_code_interpreter: bool = Field(False)
    enable_file_search: bool = Field(False)
    file_ids: list[str] = Field(default_factory=list)

    """
    A set of up to 16 key/value pairs that can be attached to an agent, used for
    storing additional information about that object in a structured format.
    Keys may be up to 64 characters in length and values may be up to 512 characters in length.
    """
    metadata: dict[str, str] = Field(default_factory=dict)
