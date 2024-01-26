# Copyright (c) Microsoft. All rights reserved.
from typing import Optional

from semantic_kernel.models.chat.chat_role import ChatRole
from semantic_kernel.models.contents.kernel_content import KernelContent


class ChatMessageContent(KernelContent):
    """This is the base class for chat message response content.

    All Chat Completion Services should return a instance of this class as response.
    Or they can implement their own subclass of this class and return an instance.

    Args:
        inner_content: Optional[Any] - The inner content of the response,
            this should hold all the information from the response so even
            when not creating a subclass a developer can leverage the full thing.
        ai_model_id: Optional[str] - The id of the AI model that generated this response.
        metadata: Dict[str, Any] - Any metadata that should be attached to the response.
        role: ChatRole - The role of the chat message.
        content: Optional[str] - The text of the response.
        encoding: Optional[str] - The encoding of the text.

    Methods:
        __str__: Returns the content of the response.
    """

    role: ChatRole
    content: Optional[str] = None
    encoding: Optional[str] = None

    def __str__(self) -> str:
        return self.content
