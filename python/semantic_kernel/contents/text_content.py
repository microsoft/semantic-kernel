# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from semantic_kernel.contents.kernel_content import KernelContent


class TextContent(KernelContent):
    """This is the base class for text response content.

    All Text Completion Services should return a instance of this class as response.
    Or they can implement their own subclass of this class and return an instance.

    Args:
        inner_content: Any - The inner content of the response,
            this should hold all the information from the response so even
            when not creating a subclass a developer can leverage the full thing.
        ai_model_id: str | None - The id of the AI model that generated this response.
        metadata: dict[str, Any] - Any metadata that should be attached to the response.
        text: str | None - The text of the response.
        encoding: str | None - The encoding of the text.

    Methods:
        __str__: Returns the text of the response.
    """

    text: str | None = None
    encoding: str | None = None

    def __str__(self) -> str:
        return self.text or ""
