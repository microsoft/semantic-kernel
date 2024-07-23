# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel


class OpenAIThreadCreationSettings(KernelBaseModel):
    code_interpreter_file_ids: list[str] | None = Field(default_factory=list, max_length=64)
    messages: list[ChatMessageContent] | None = Field(default_factory=list)
    vector_store_ids: list[str] | None = Field(default_factory=list, max_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)
