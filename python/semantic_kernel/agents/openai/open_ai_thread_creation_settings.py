# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel


class OpenAIThreadCreationSettings(KernelBaseModel):
    code_interpreter_file_ids: list[str] | None = Field(default_factory=list)
    enable_code_interpreter: bool = Field(False)
    messages: list[ChatMessageContent] | None = Field(default_factory=list)
    enable_file_search: bool = Field(False)
    vector_store_id: list[str] | None = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
