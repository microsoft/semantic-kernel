from typing import Optional

from semantic_kernel.models.chat.chat_role import ChatRole
from semantic_kernel.models.contents.streaming_kernel_content import StreamingKernelContent


class StreamingChatMessageContent(StreamingKernelContent):
    role: ChatRole
    content: Optional[str] = None
    encoding: Optional[str] = None
    # items: Optional[List[ChatMessageContent]] = None

    def __str__(self) -> str:
        return self.content
