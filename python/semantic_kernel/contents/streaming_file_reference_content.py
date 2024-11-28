# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, ClassVar, Literal, TypeVar
from xml.etree.ElementTree import Element  # nosec

from pydantic import Field

from semantic_kernel.contents.const import STREAMING_FILE_REFERENCE_CONTENT_TAG, ContentTypes
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.utils.experimental_decorator import experimental_class

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="StreamingFileReferenceContent")


@experimental_class
class StreamingFileReferenceContent(KernelContent):
    """Streaming File reference content."""

    content_type: Literal[ContentTypes.STREAMING_FILE_REFERENCE_CONTENT] = Field(
        STREAMING_FILE_REFERENCE_CONTENT_TAG,  # type: ignore
        init=False,
    )
    tag: ClassVar[str] = STREAMING_FILE_REFERENCE_CONTENT_TAG
    file_id: str | None = None

    def __str__(self) -> str:
        """Return the string representation of the file reference content."""
        return f"StreamingFileReferenceContent(file_id={self.file_id})"

    def to_element(self) -> Element:
        """Convert the file reference content to an Element."""
        element = Element(self.tag)
        if self.file_id:
            element.set("file_id", self.file_id)
        return element

    @classmethod
    def from_element(cls: type[_T], element: Element) -> _T:
        """Create an instance from an Element."""
        return cls(
            file_id=element.get("file_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "file_id": self.file_id,
        }
