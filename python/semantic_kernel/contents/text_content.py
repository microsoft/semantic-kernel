# Copyright (c) Microsoft. All rights reserved.

from html import unescape
from typing import ClassVar, Literal, TypeVar
from xml.etree.ElementTree import Element  # nosec

from pydantic import Field

from semantic_kernel.contents.const import TEXT_CONTENT_TAG, ContentTypes
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.exceptions.content_exceptions import ContentInitializationError

_T = TypeVar("_T", bound="TextContent")


class TextContent(KernelContent):
    """This represents text response content.

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

    content_type: Literal[ContentTypes.TEXT_CONTENT] = Field(TEXT_CONTENT_TAG, init=False)  # type: ignore
    tag: ClassVar[str] = TEXT_CONTENT_TAG
    text: str
    encoding: str | None = None

    def __str__(self) -> str:
        """Return the text of the response."""
        return self.text

    def to_element(self) -> Element:
        """Convert the instance to an Element."""
        element = Element(self.tag)
        element.text = self.text
        if self.encoding:
            element.set("encoding", self.encoding)
        return element

    @classmethod
    def from_element(cls: type[_T], element: Element) -> _T:
        """Create an instance from an Element."""
        if element.tag != cls.tag:
            raise ContentInitializationError(f"Element tag is not {cls.tag}")  # pragma: no cover

        return cls(text=unescape(element.text) if element.text else "", encoding=element.get("encoding", None))

    def to_dict(self) -> dict[str, str]:
        """Convert the instance to a dictionary."""
        return {"type": "text", "text": self.text}

    def __hash__(self) -> int:
        """Return the hash of the text content."""
        return hash((self.tag, self.text, self.encoding))
