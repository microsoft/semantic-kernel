# Copyright (c) Microsoft. All rights reserved.

from html import unescape
from typing import ClassVar, Literal, TypeVar
from xml.etree.ElementTree import Element  # nosec

from pydantic import Field

from semantic_kernel.contents.const import TEXT_CONTENT_TAG, ContentTypes
from semantic_kernel.contents.content_concatenation_mixin import ContentConcatenationMixin
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.exceptions.content_exceptions import ContentAdditionException, ContentInitializationError

_T = TypeVar("_T", bound="TextContent")


class TextContent(ContentConcatenationMixin, KernelContent):
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
    choice_index: int | None = None
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

    def __bytes__(self) -> bytes:
        """Return the content of the response encoded in the encoding."""
        return self.text.encode(self.encoding if self.encoding else "utf-8") if self.text else b""

    def __add__(self, other: "TextContent") -> "TextContent":
        """When combining two TextContent instances, the text fields are combined.

        The addition should follow these rules:
            1. The inner_content of the two will be combined. If they are not lists, they will be converted to lists.
            2. ai_model_id should be the same.
            3. encoding should be the same.
            4. choice_index should be the same.
            5. Metadata will be combined.
        """
        if isinstance(other, TextContent) and self.choice_index != other.choice_index:
            raise ContentAdditionException("Cannot add TextContent with different choice_index")
        if self.ai_model_id != other.ai_model_id:
            raise ContentAdditionException("Cannot add TextContent from different ai_model_id")
        if self.encoding != other.encoding:
            raise ContentAdditionException("Cannot add TextContent with different encoding")

        return TextContent(
            choice_index=self.choice_index,
            inner_content=self._merge_inner_contents(other.inner_content),
            ai_model_id=self.ai_model_id,
            metadata=self.metadata | other.metadata,
            text=(self.text or "") + (other.text or ""),
            encoding=self.encoding,
        )
