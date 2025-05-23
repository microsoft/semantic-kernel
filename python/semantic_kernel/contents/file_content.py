# Copyright (c) Microsoft. All rights reserved.

import logging
import mimetypes
import os
from typing import Any, ClassVar, Literal, TypeVar
from numpy import ndarray
from pydantic import Field
from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.const import ContentTypes, FILE_CONTENT_TAG
from semantic_kernel.utils.feature_stage_decorator import experimental

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="FileContent")


@experimental
class FileContent(BinaryContent):
    """File Content class.

    This can be created either from bytes data or a file path. The filename and mime_type are required for correct serialization.
    """

    content_type: Literal[ContentTypes.FILE_CONTENT] = Field(FILE_CONTENT_TAG, init=False)  # type: ignore
    tag: ClassVar[str] = FILE_CONTENT_TAG
    filename: str | None = None

    def __init__(
        self,
        filename: str | None = None,
        uri: str | None = None,
        data_uri: str | None = None,
        data: str | bytes | ndarray | None = None,
        data_format: str | None = None,
        mime_type: str | None = None,
        **kwargs: Any,
    ):
        # Always use base64 for file data for consistency with serialization
        if data is not None and data_format is None:
            data_format = "base64"
        super().__init__(
            uri=uri,
            data_uri=data_uri,
            data=data,
            data_format=data_format,
            mime_type=mime_type,
            **kwargs,
        )
        self.filename = filename
        if self.filename is None and uri is not None:
            self.filename = os.path.basename(uri)

    @classmethod
    def from_file(cls: type[_T], file_path: str, **kwargs: Any) -> _T:
        mime_type, _ = mimetypes.guess_type(file_path)
        with open(file_path, "rb") as f:
            data = f.read()
        filename = os.path.basename(file_path)
        # Always use base64 for file data for consistency with serialization
        return cls(
            filename=filename,
            data=data,
            mime_type=mime_type,
            data_format="base64",
            **kwargs,
        )

    def __str__(self) -> str:
        if self.data is not None and self.mime_type is not None:
            import base64

            encoded = base64.b64encode(self.data).decode("ascii")
            return f"data:{self.mime_type};base64,{encoded}"
        elif self.uri is not None:
            return str(self.uri)
        return ""

    def to_element(self) -> Any:
        return {"type": "input_file", "filename": self.filename, "file_data": str(self)}

    @classmethod
    def from_element(cls: type[_T], element: Any) -> _T:
        # Parse file_data as data URI if present
        import re
        import base64

        file_data = element.get("file_data")
        filename = element.get("filename")
        data = None
        mime_type = None
        data_format = None
        if file_data and file_data.startswith("data:"):
            # Example: data:application/pdf;base64,....
            match = re.match(r"data:([^;]+);base64,(.*)", file_data)
            if match:
                mime_type = match.group(1)
                data = base64.b64decode(match.group(2))
                data_format = "base64"
        return cls(
            filename=filename, data=data, mime_type=mime_type, data_format=data_format
        )

    def to_dict(self) -> dict[str, Any]:
        return {"type": "input_file", "filename": self.filename, "file_data": str(self)}
