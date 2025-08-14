# Copyright (c) Microsoft. All rights reserved.

"""Reasoning content model."""

from html import unescape
from typing import ClassVar, Literal, TypeVar
from xml.etree.ElementTree import Element  # nosec

from pydantic import Field

from semantic_kernel.contents.const import REASONING_CONTENT_TAG, ContentTypes
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.exceptions.content_exceptions import ContentInitializationError

_T = TypeVar("_T", bound="ReasoningContent")


class ReasoningContent(KernelContent):
    """Represents reasoning content.

    Mirrors the .NET ReasoningContent which only exposes text. Any provider-specific
    fields (like ids, encrypted blobs, statuses) should be placed in `metadata`.
    """

    content_type: Literal[ContentTypes.REASONING_CONTENT] = Field(REASONING_CONTENT_TAG, init=False)
    tag: ClassVar[str] = REASONING_CONTENT_TAG
    text: str = ""

    def __str__(self) -> str:
        """Return the text of the reasoning content."""
        return self.text

    def to_element(self) -> Element:
        """Convert the instance to an XML Element."""
        element = Element(self.tag)
        element.text = self.text
        return element

    @classmethod
    def from_element(cls: type[_T], element: Element) -> _T:
        """Create an instance from an XML Element."""
        if element.tag != cls.tag:
            raise ContentInitializationError(f"Element tag is not {cls.tag}")  # pragma: no cover
        return cls(text=unescape(element.text) if element.text else "")

    def to_dict(self) -> dict[str, str]:
        """Convert the instance to a dictionary suitable for message serialization."""
        return {"type": "reasoning", "text": self.text}
