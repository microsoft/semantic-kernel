# Copyright (c) Microsoft. All rights reserved.
from typing import Optional

from semantic_kernel.contents.kernel_content import KernelContent


class TextContent(KernelContent):
    """This is the base class for text response content.

    All Text Completion Services should return a instance of this class as response.
    Or they can implement their own subclass of this class and return an instance.

    Args:
        inner_content: Optional[Any] - The inner content of the response,
            this should hold all the information from the response so even
            when not creating a subclass a developer can leverage the full thing.
        ai_model_id: Optional[str] - The id of the AI model that generated this response.
        metadata: Dict[str, Any] - Any metadata that should be attached to the response.
        text: Optional[str] - The text of the response.
        encoding: Optional[str] - The encoding of the text.

    Methods:
        __str__: Returns the text of the response.
    """

    text: Optional[str] = None
    encoding: Optional[str] = None

    def __str__(self) -> str:
        return self.text
