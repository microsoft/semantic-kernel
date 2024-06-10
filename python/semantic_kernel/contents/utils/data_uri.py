# Copyright (c) Microsoft. All rights reserved.

import base64
import logging
import re
import sys
from typing import Any, TypeVar

from semantic_kernel.exceptions.content_exceptions import ContentInitializationError

if sys.version < "3.11":
    from typing_extensions import Self
else:
    from typing import Self

from pydantic import Field, field_validator, model_validator
from pydantic_core import Url

from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="DataUri")


class DataUri(KernelBaseModel, validate_assignment=True):
    data_bytes: bytes | None = None
    data_str: str | None = None
    mime_type: str | None = None
    parameters: dict[str, str] = Field(default_factory=dict)
    data_format: str | None = None

    def update_data(self, value: str | bytes):
        """Update the data, using either a string or bytes."""
        if isinstance(value, str):
            self.data_str = value
        else:
            self.data_bytes = value

    @model_validator(mode="before")
    @classmethod
    def _validate_data(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate the data."""
        if not values.get("data_bytes") and not values.get("data_str"):
            raise ContentInitializationError("Either data_bytes or data_str must be provided.")
        return values

    @model_validator(mode="after")
    def _parse_data(self) -> Self:
        """Parse the data bytes to str."""
        if not self.data_str and self.data_bytes:
            if self.data_format and self.data_format.lower() == "base64":
                self.data_str = base64.b64encode(self.data_bytes).decode("utf-8")
            else:
                self.data_str = self.data_bytes.decode("utf-8")
        return self

    @classmethod
    def from_data_uri(cls: type[_T], data_uri: str | Url, default_mime_type: str = "text/plain") -> _T:
        """Create a DataUri object from a data URI string or pydantic URL."""
        if isinstance(data_uri, str):
            data_uri = Url(data_uri)

        data = data_uri.path
        if not data or "," not in data:
            raise ContentInitializationError("Invalid data uri format. The data is missing.")

        pattern = "((?P<mime_type>[a-zA-Z]+/[a-zA-Z]+)(?P<parameters>(;[a-zA-Z0-9]+=+[a-zA-Z0-9]+)*)(;+(?P<data_format>.*)))?(,(?P<data_str>.*))"  # noqa: E501
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
        return cls(**matches)

    @field_validator("parameters", mode="before")
    def _validate_parameters(cls, value: list[str] | dict[str, str] | None = None) -> dict[str, str] | None:
        if not value:
            return None
        if isinstance(value, dict):
            return value

        new: dict[str, str] = {}
        for item in value:
            if item.strip() == "":
                continue
            if "=" not in item:
                raise ValueError("Invalid data uri format. The parameter is missing a value.")
            name, val = item.split("=", maxsplit=1)
            new[name] = val
        return new

    def to_string(self, metadata: dict[str, str] = {}) -> str:
        """Return the data uri as a string."""
        parameters = ";".join([f"{key}={val}" for key, val in metadata.items()])
        parameters = f";{parameters}" if parameters else ""
        data_format = f"{self.data_format}" if self.data_format else ""
        return f"data:{self.mime_type or ''}{parameters};{data_format},{self.data_str}"

    def __eq__(self, value: object) -> bool:
        """Check if the data uri is equal to another."""
        if not isinstance(value, DataUri):
            return False
        return self.to_string() == value.to_string()
