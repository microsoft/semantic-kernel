from typing import Optional

from semantic_kernel.models.contents.streaming_kernel_content import StreamingKernelContent


class StreamingTextContent(StreamingKernelContent):
    text: Optional[str] = None
    encoding: Optional[str] = None

    def __str__(self) -> str:
        return self.text

    def __bytes__(self) -> bytes:
        return self.text.encode(self.encoding if self.encoding else "utf-8") if self.text else b""
