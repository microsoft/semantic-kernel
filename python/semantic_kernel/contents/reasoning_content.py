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

    Exposes a human-readable reasoning ``text``. Any provider-specific fields (for example: ids, encrypted blobs,
    statuses, token info) must be carried in ``metadata`` on the base ``KernelContent``.

    Attributes:
        content_type: Literal identifying this instance as reasoning content.
        tag: XML tag name used when serializing to/from XML.
        text: The reasoning text to surface to callers.

    Methods:
        __str__: Return the reasoning text.
        to_element: Serialize to an XML Element using ``tag`` and ``text``.
        from_element: Deserialize from an XML Element into a ReasoningContent.
        to_dict: Serialize to a dict suitable for message payloads.
    """

    content_type: Literal[ContentTypes.REASONING_CONTENT] = Field(REASONING_CONTENT_TAG, init=False)
    tag: ClassVar[str] = REASONING_CONTENT_TAG
    text: str | None = None

    def __str__(self) -> str:
        """Return the text of the reasoning content."""
        return self.text or ""

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
        return {"type": "reasoning", "text": self.text or ""}
