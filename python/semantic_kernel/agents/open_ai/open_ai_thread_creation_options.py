# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class OpenAIThreadCreationOptions(KernelBaseModel):
    """OpenAI Assistant Thread Creation Settings class."""

    code_interpreter_file_ids: list[str] | None = Field(default_factory=list, max_length=64)
    messages: list[ChatMessageContent] | None = Field(default_factory=list)
    vector_store_id: str | None = Field(None)
    metadata: dict[str, str] = Field(default_factory=dict)
