from typing import Optional

from semantic_kernel.models.chat.chat_role import ChatRole
from semantic_kernel.models.contents.kernel_content import KernelContent


class ChatMessageContent(KernelContent):
    role: ChatRole
    content: Optional[str] = None
    encoding: Optional[str] = None

    def __str__(self) -> str:
        return self.content
