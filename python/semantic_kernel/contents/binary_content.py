# Copyright (c) Microsoft. All rights reserved.

import logging
import os
from typing import Annotated, Any, ClassVar, Literal, TypeVar
from xml.etree.ElementTree import Element  # nosec

from pydantic import Field, FilePath, UrlConstraints, computed_field
from pydantic_core import Url

from semantic_kernel.contents.const import BINARY_CONTENT_TAG, ContentTypes
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.contents.utils.data_uri import DataUri
from semantic_kernel.exceptions.content_exceptions import ContentInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="BinaryContent")

DataUrl = Annotated[Url, UrlConstraints(allowed_schemes=["data"])]


@experimental_class
class BinaryContent(KernelContent):
    """This is a base class for different types of binary content.

    This can be created either the bytes data or a data uri, additionally it can have a uri.
    The uri is a reference to the source, and might or might not point to the same thing as the data.

    Ideally only subclasses of this class are used, like ImageContent.

    Methods:
        __str__: Returns the string representation of the content.

    Raises:
        ValidationError: If any arguments are malformed.

    """

    content_type: Literal[ContentTypes.BINARY_CONTENT] = Field(BINARY_CONTENT_TAG, init=False)  # type: ignore
    uri: Url | str | None = None
    default_mime_type: ClassVar[str] = "text/plain"
    tag: ClassVar[str] = BINARY_CONTENT_TAG
    _data_uri: DataUri | None = None

    def __init__(
        self,
        uri: Url | str | None = None,
        data_uri: DataUrl | str | None = None,
        data: str | bytes | None = None,
        data_format: str | None = None,
        mime_type: str | None = None,
        **kwargs: Any,
    ):
        """Create a Binary Content object, either from a data_uri or data.

        Args:
            uri (Url | str | None): The reference uri of the content.
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
        """
        _data_uri = None
        if data_uri:
            _data_uri = DataUri.from_data_uri(data_uri, self.default_mime_type)
            if "metadata" in kwargs:
                kwargs["metadata"].update(_data_uri.parameters)
            else:
                kwargs["metadata"] = _data_uri.parameters
        elif data:
            if isinstance(data, str):
                _data_uri = DataUri(
                    data_str=data, data_format=data_format, mime_type=mime_type or self.default_mime_type
                )
            else:
                _data_uri = DataUri(
                    data_bytes=data, data_format=data_format, mime_type=mime_type or self.default_mime_type
                )

        if uri is not None:
            if isinstance(uri, str) and os.path.exists(uri):
                uri = str(FilePath(uri))
            elif isinstance(uri, str):
                uri = Url(uri)

        super().__init__(uri=uri, **kwargs)
        self._data_uri = _data_uri

    @computed_field  # type: ignore
    @property
    def data_uri(self) -> str:
        """Get the data uri."""
        if self._data_uri:
            return self._data_uri.to_string(self.metadata)
        return ""

    @data_uri.setter
    def data_uri(self, value: str):
        """Set the data uri."""
        self._data_uri = DataUri.from_data_uri(value)
        self.metadata.update(self._data_uri.parameters)

    @property
    def data(self) -> bytes:
        """Get the data."""
        if self._data_uri and self._data_uri.data_bytes:
            return self._data_uri.data_bytes
        if self._data_uri and self._data_uri.data_str:
            return self._data_uri.data_str.encode("utf-8")
        return b""

    @data.setter
    def data(self, value: str | bytes):
        """Set the data."""
        if self._data_uri:
            self._data_uri.update_data(value)
        else:
            if isinstance(value, str):
                self._data_uri = DataUri(data_str=value, mime_type=self.mime_type)
            else:
                self._data_uri = DataUri(data_bytes=value, mime_type=self.mime_type)

    @property
    def mime_type(self) -> str:
        """Get the mime type."""
        if self._data_uri and self._data_uri.mime_type:
            return self._data_uri.mime_type
        return self.default_mime_type

    @mime_type.setter
    def mime_type(self, value: str):
        """Set the mime type."""
        if self._data_uri:
            self._data_uri.mime_type = value

    def __str__(self) -> str:
        """Return the string representation of the content."""
        return self.data_uri if self._data_uri else str(self.uri)

    def to_element(self) -> Element:
        """Convert the instance to an Element."""
        element = Element(self.tag)
        if self._data_uri:
            element.text = self.data_uri
        if self.uri:
            element.set("uri", str(self.uri))
        return element

    @classmethod
    def from_element(cls: type[_T], element: Element) -> _T:
        """Create an instance from an Element."""
        if element.tag != cls.tag:
            raise ContentInitializationError(f"Element tag is not {cls.tag}")  # pragma: no cover

        if element.text:
            return cls(data_uri=element.text, uri=element.get("uri", None))

        return cls(uri=element.get("uri", None))

    def write_to_file(self, path: str | FilePath) -> None:
        """Write the data to a file."""
        with open(path, "wb") as file:
            file.write(self.data)

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {"type": "binary", "binary": {"uri": str(self)}}
