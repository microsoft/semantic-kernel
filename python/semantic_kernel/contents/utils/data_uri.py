# Copyright (c) Microsoft. All rights reserved.

import base64
import binascii
import logging
import re
from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any, TypeVar

from numpy import ndarray
from pydantic import Field, ValidationError, field_validator
from pydantic_core import Url

from semantic_kernel.exceptions import ContentInitializationError
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="DataUri")


class DataUri(KernelBaseModel, validate_assignment=True):
    """A class to represent a data uri.

    If a array is provided, that will be used as the data since it is the most efficient,
    otherwise the bytes will be used, or the string will be converted to bytes.

    When updating either array or bytes, the other will not be updated.

    Args:
        data_bytes: The data as bytes.
        data_str: The data as a string.
        data_array: The data as a numpy array.
        mime_type: The mime type of the data.
        parameters: Any parameters for the data.
        data_format: The format of the data (e.g. base64).

    """

    data_array: ndarray | None = None
    data_bytes: bytes | None = None
    mime_type: str | None = None
    parameters: MutableMapping[str, str] = Field(default_factory=dict)
    data_format: str | None = None

    def __init__(
        self,
        data_bytes: bytes | None = None,
        data_str: str | None = None,
        data_array: ndarray | None = None,
        mime_type: str | None = None,
        parameters: Sequence[str] | Mapping[str, str] | None = None,
        data_format: str | None = None,
        **kwargs: Any,
    ):
        """Initialize the data uri.

        Make sure to set the data_format to base64 so that it can be decoded properly.

        Args:
            data_bytes: The data as bytes.
            data_str: The data as a string.
            data_array: The data as a numpy array.
            mime_type: The mime type of the data.
            parameters: Any parameters for the data.
            data_format: The format of the data (e.g. base64).
            kwargs: Any additional arguments.
        """
        args: dict[str, Any] = {}
        if data_bytes is not None:
            args["data_bytes"] = data_bytes
        if data_array is not None:
            args["data_array"] = data_array

        if mime_type is not None:
            args["mime_type"] = mime_type
        if parameters is not None:
            args["parameters"] = parameters
        if data_format is not None:
            args["data_format"] = data_format

        if data_str is not None and not data_bytes:
            if data_format and data_format.lower() == "base64":
                try:
                    args["data_bytes"] = base64.b64decode(data_str, validate=True)
                except binascii.Error as exc:
                    raise ContentInitializationError("Invalid base64 data.") from exc
            else:
                args["data_bytes"] = data_str.encode("utf-8")
        if "data_array" not in args and "data_bytes" not in args:
            raise ContentInitializationError("Either data_bytes, data_str or data_array must be provided.")
        super().__init__(**args, **kwargs)

    def update_data(self, value: str | bytes | ndarray) -> None:
        """Update the data, using either a string or bytes."""
        match value:
            case ndarray():
                self.data_array = value
            case str():
                if self.data_format and self.data_format.lower() == "base64":
                    self.data_bytes = base64.b64decode(value, validate=True)
                else:
                    self.data_bytes = value.encode("utf-8")
            case _:
                self.data_bytes = value

    @field_validator("parameters", mode="before")
    def _validate_parameters(cls, value: list[str] | dict[str, str] | None) -> dict[str, str]:
        if not value:
            return {}
        if isinstance(value, dict):
            return value

        new: dict[str, str] = {}
        for item in value:
            item = item.strip()
            if not item:
                continue
            if "=" not in item:
                raise ContentInitializationError("Invalid data uri format. The parameter is missing a value.")
            name, val = item.split("=", maxsplit=1)
            new[name] = val
        return new

    @classmethod
    def from_data_uri(cls: type[_T], data_uri: str | Url, default_mime_type: str = "text/plain") -> _T:
        """Create a DataUri object from a data URI string or pydantic URL."""
        if isinstance(data_uri, str):
            try:
                data_uri = Url(data_uri)
            except ValidationError as exc:
                raise ContentInitializationError("Invalid data uri format.") from exc

        data = data_uri.path
        if not data or "," not in data:
            raise ContentInitializationError("Invalid data uri format. The data is missing.")

        pattern = "(((?P<mime_type>[a-zA-Z]+/[a-zA-Z-]+)(?P<parameters>(;[a-zA-Z0-9]+=+[a-zA-Z0-9]+)*))?(;+(?P<data_format>.*)))?(,(?P<data_str>.*))"  # noqa: E501
        match = re.match(pattern, data)
        if not match:
            raise ContentInitializationError("Invalid data uri format.")
        matches = match.groupdict()
        if not matches.get("data_format"):
            matches.pop("data_format")
        if not matches.get("parameters"):
            matches.pop("parameters")
        else:
            matches["parameters"] = matches["parameters"].strip(";").split(";")
        if not matches.get("mime_type"):
            matches["mime_type"] = default_mime_type
        return cls(**matches)  # type: ignore

    def to_string(self, metadata: dict[str, str] | None = None) -> str:
        """Return the data uri as a string."""
        if metadata:
            parameters = ";".join([f"{key}={val}" for key, val in metadata.items()])
            parameters = f";{parameters}" if parameters else ""
        else:
            parameters = ""
        data_format = f"{self.data_format}" if self.data_format else ""
        return f"data:{self.mime_type or ''}{parameters};{data_format},{self._data_str()}"

    def __eq__(self, value: object) -> bool:
        """Check if the data uri is equal to another."""
        if not isinstance(value, DataUri):
            return False
        return self.to_string() == value.to_string()

    def _data_str(self) -> str:
        """Return the data as a string."""
        if self.data_array is not None:
            if self.data_format and self.data_format.lower() == "base64":
                return base64.b64encode(self.data_array.tobytes()).decode("utf-8")
            return self.data_array.tobytes().decode("utf-8")
        if self.data_bytes is not None:
            if self.data_format and self.data_format.lower() == "base64":
                return base64.b64encode(self.data_bytes).decode("utf-8")
            return self.data_bytes.decode("utf-8")
        return ""
