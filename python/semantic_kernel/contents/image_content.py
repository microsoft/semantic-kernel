# Copyright (c) Microsoft. All rights reserved.

import base64
import logging
import mimetypes
import sys
from typing import Any, Literal, TypeVar

from semantic_kernel.exceptions.content_exceptions import ContentInitializationError

if sys.version < "3.11":
    from typing_extensions import Self
else:
    from typing import Self

from xml.etree.ElementTree import Element  # nosec

from pydantic import Field, model_validator
from pydantic_core import Url

from semantic_kernel.contents.const import IMAGE_CONTENT_TAG, ContentTypes
from semantic_kernel.contents.kernel_content import KernelContent

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="ImageContent")


class ImageContent(KernelContent):
    """This represent image content.

    This can be created either with a uri for a image or with the bytes data of the image.
    Use the .from_image_file method to create an instance from a image file.
        This reads the file and guesses the mime_type.
    If both uri and data is provided, data will be used and a warning is logged.

    Args:
        inner_content (Any): The inner content of the response,
            this should hold all the information from the response so even
            when not creating a subclass a developer can leverage the full thing.
        ai_model_id (str | None): The id of the AI model that generated this response.
        metadata (dict[str, Any]): Any metadata that should be attached to the response.
        uri (Url | None): The uri of the image.
        data (bytes | None): The data of the image.
        mime_type (str | None): The mime type of the image, only used with data.

    Methods:
        from_image_path: Create an instance from an image file.
        __str__: Returns the string representation of the image.

    Raises:
        ValidationError: If neither uri or data is provided.

    """

    content_type: Literal[ContentTypes.IMAGE_CONTENT] = Field(IMAGE_CONTENT_TAG, init=False)  # type: ignore
    uri: Url | None = None
    data: bytes | None = None
    mime_type: str | None = None

    @model_validator(mode="after")
    def validate_uri_and_or_data(self) -> Self:
        """Validate that either uri or data is provided."""
        if not self.uri and not self.data:
            raise ContentInitializationError("Either uri or data must be provided.")
        if self.uri and self.data:
            logger.warning('Both "uri" and "data" are provided, "data" will be used.')
        return self

    def __str__(self) -> str:
        """Return the string representation of the image."""
        return (
            f"data:{self.mime_type};base64,{ base64.b64encode(self.data).decode('utf-8')}"
            if self.data
            else str(self.uri)
        )

    def to_element(self) -> Element:
        """Convert the instance to an Element."""
        element = Element(IMAGE_CONTENT_TAG)
        if self.data:
            element.text = str(self)
        if self.uri:
            element.set("uri", str(self.uri))
        if self.mime_type:
            element.set("mime_type", self.mime_type)
        return element

    @classmethod
    def from_element(cls: type[_T], element: Element) -> _T:
        """Create an instance from an Element."""
        if element.tag != IMAGE_CONTENT_TAG:
            raise ValueError(f"Element tag is not {IMAGE_CONTENT_TAG}")

        if element.text:
            return cls(
                data=base64.b64decode(element.text.split(",")[1].encode()),
                mime_type=element.text.split(",")[0].split(";")[0].split(":")[1],
            )

        return cls(
            uri=element.get("uri", None),
            mime_type=element.get("mime_type", None),
        )

    @classmethod
    def from_image_path(cls: type[_T], image_path: str) -> _T:
        """Create an instance from an image file."""
        mime_type = mimetypes.guess_type(image_path)[0]
        with open(image_path, "rb") as image_file:
            return cls(data=image_file.read(), mime_type=mime_type)

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {"type": "image_url", "image_url": {"url": str(self)}}
