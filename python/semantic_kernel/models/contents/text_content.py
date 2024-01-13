from typing import Optional

from semantic_kernel.models.contents.kernel_content import KernelContent


class TextContent(KernelContent):
    text: Optional[str] = None
    encoding: Optional[str] = None

    def __str__(self) -> str:
        return self.text
