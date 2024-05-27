# Copyright (c) Microsoft. All rights reserved.

from html import unescape
from xml.etree.ElementTree import Element

from semantic_kernel.contents.const import TEXT_CONTENT_TAG
from semantic_kernel.contents.kernel_content import KernelContent


class TextContent(KernelContent):
    """This is the base class for text response content.

    All Text Completion Services should return an instance of this class as response.
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

    text: str
    encoding: str | None = None

    def __str__(self) -> str:
        return self.text

    def to_element(self) -> Element:
        """Convert the instance to an Element."""
        element = Element(TEXT_CONTENT_TAG)
        element.text = self.text
        if self.encoding:
            element.set("encoding", self.encoding)
        return element

    @classmethod
    def from_element(cls, element: Element) -> "TextContent":
        """Create an instance from an Element."""
        if element.tag != TEXT_CONTENT_TAG:
            raise ValueError(f"Element tag is not {TEXT_CONTENT_TAG}")

        return TextContent(text=unescape(element.text) if element.text else "", encoding=element.get("encoding", None))

    def to_dict(self) -> dict[str, str]:
        """Convert the instance to a dictionary."""
        return {"type": "text", "text": self.text}
