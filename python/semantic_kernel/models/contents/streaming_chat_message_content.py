from typing import Optional

from semantic_kernel.models.chat.chat_role import ChatRole
from semantic_kernel.models.chat.finish_reason import FinishReason
from semantic_kernel.models.contents.streaming_kernel_content import StreamingKernelContent


class StreamingChatMessageContent(StreamingKernelContent):
    role: Optional[ChatRole] = ChatRole.ASSISTANT
    content: Optional[str] = None
    encoding: Optional[str] = None
    finish_reason: Optional[FinishReason] = None

    def __str__(self) -> str:
        return self.content or ""

    def __bytes__(self) -> bytes:
        return self.content.encode(self.encoding if self.encoding else "utf-8") if self.content else b""
