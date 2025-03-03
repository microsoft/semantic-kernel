# Copyright (c) Microsoft. All rights reserved.

import logging
import mimetypes
from typing import Any, ClassVar, Literal, TypeVar

from numpy import ndarray
from pydantic import Field
from typing_extensions import deprecated

from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.const import IMAGE_CONTENT_TAG, ContentTypes
from semantic_kernel.utils.feature_stage_decorator import experimental

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="ImageContent")


@experimental
class ImageContent(BinaryContent):
    """Image Content class.

    This can be created either the bytes data or a data uri, additionally it can have a uri.
    The uri is a reference to the source, and might or might not point to the same thing as the data.

    Use the .from_image_file method to create an instance from a image file.
    This reads the file and guesses the mime_type.

    If both data_uri and data is provided, data will be used and a warning is logged.

    Args:
        uri (Url | None): The reference uri of the content.
        data_uri (DataUrl | None): The data uri of the content.
        data (str | bytes | None): The data of the content.
        data_format (str | None): The format of the data (e.g. base64).
        mime_type (str | None): The mime type of the image, only used with data.
        kwargs (Any): Any additional arguments:
            inner_content (Any): The inner content of the response,
                this should hold all the information from the response so even
                when not creating a subclass a developer can leverage the full thing.
            ai_model_id (str | None): The id of the AI model that generated this response.
            metadata (dict[str, Any]): Any metadata that should be attached to the response.

    Methods:
        from_image_path: Create an instance from an image file.
        __str__: Returns the string representation of the image.

    Raises:
        ValidationError: If neither uri or data is provided.
    """

    content_type: Literal[ContentTypes.IMAGE_CONTENT] = Field(IMAGE_CONTENT_TAG, init=False)  # type: ignore
    tag: ClassVar[str] = IMAGE_CONTENT_TAG

    def __init__(
        self,
        uri: str | None = None,
        data_uri: str | None = None,
        data: str | bytes | ndarray | None = None,
        data_format: str | None = None,
        mime_type: str | None = None,
        **kwargs: Any,
    ):
        """Create an Image Content object, either from a data_uri or data.

        Args:
            uri: The reference uri of the content.
            data_uri: The data uri of the content.
            data: The data of the content.
            data_format: The format of the data (e.g. base64).
            mime_type: The mime type of the image, only used with data.
            kwargs: Any additional arguments:
            inner_content: The inner content of the response,
                this should hold all the information from the response so even
                when not creating a subclass a developer
                can leverage the full thing.
            ai_model_id: The id of the AI model that generated this response.
            metadata: Any metadata that should be attached to the response.
        """
        super().__init__(
            uri=uri,
            data_uri=data_uri,
            data=data,
            data_format=data_format,
            mime_type=mime_type,
            **kwargs,
        )

    @classmethod
    @deprecated("The `from_image_path` method is deprecated; use `from_image_file` instead.", category=None)
    def from_image_path(cls: type[_T], image_path: str) -> _T:
        """Create an instance from an image file."""
        return cls.from_image_file(image_path)

    @classmethod
    def from_image_file(cls: type[_T], path: str) -> _T:
        """Create an instance from an image file."""
        mime_type = mimetypes.guess_type(path)[0]
        with open(path, "rb") as image_file:
            return cls(data=image_file.read(), data_format="base64", mime_type=mime_type, uri=path)

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {"type": "image_url", "image_url": {"url": str(self)}}
