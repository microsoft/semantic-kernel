# Copyright (c) Microsoft. All rights reserved.

import base64
import logging
import mimetypes
from typing import Any
from xml.etree.ElementTree import Element  # nosec

from pydantic import ValidationError, model_validator
from pydantic_core import Url

from semantic_kernel.contents.const import IMAGE_CONTENT_TAG
from semantic_kernel.contents.kernel_content import KernelContent

logger = logging.getLogger(__name__)


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
        from_image_file: Create an instance from an image file.
        __str__: Returns the string representation of the image.

    Raises:
        ValidationError: If neither uri or data is provided.

    """

    uri: Url | None = None
    data: bytes | None = None
    mime_type: str | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_uri_and_or_data(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate that either uri or data is provided."""
        if not values.get("uri") and not values.get("data"):
            raise ValidationError("Either uri or data must be provided.")
        if values.get("uri") and values.get("data"):
            logger.warning('Both "uri" and "data" are provided, "data" will be used.')
        return values

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
    def from_element(cls, element: Element) -> "ImageContent":
        """Create an instance from an Element."""
        if element.tag != IMAGE_CONTENT_TAG:
            raise ValueError(f"Element tag is not {IMAGE_CONTENT_TAG}")

        if element.text:
            return ImageContent(
                data=base64.b64decode(element.text.split(",")[1].encode()),
                mime_type=element.text.split(",")[0].split(";")[0].split(":")[1],
            )

        return ImageContent(
            uri=element.get("uri", None),
            mime_type=element.get("mime_type", None),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {"type": "image_url", "image_url": {"url": str(self)}}

    @classmethod
    def from_image_file(cls, image_path: str) -> "ImageContent":
        """Create an instance from an image file."""
        mime_type = mimetypes.guess_type(image_path)[0]
        with open(image_path, "rb") as image_file:
            return ImageContent(data=image_file.read(), mime_type=mime_type)
