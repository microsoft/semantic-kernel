# Copyright (c) Microsoft. All rights reserved.

import mimetypes
from typing import Any, ClassVar, Literal, TypeVar

from pydantic import Field

from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.const import AUDIO_CONTENT_TAG, ContentTypes
from semantic_kernel.utils.experimental_decorator import experimental_class

_T = TypeVar("_T", bound="AudioContent")


@experimental_class
class AudioContent(BinaryContent):
    """Audio Content class.

    This can be created either the bytes data or a data uri, additionally it can have a uri.
    The uri is a reference to the source, and might or might not point to the same thing as the data.

    Use the .from_audio_file method to create an instance from an audio file.
    This reads the file and guesses the mime_type.

    If both data_uri and data is provided, data will be used and a warning is logged.

    Args:
        uri (Url | None): The reference uri of the content.
        data_uri (DataUrl | None): The data uri of the content.
        data (str | bytes | None): The data of the content.
        data_format (str | None): The format of the data (e.g. base64).
        mime_type (str | None): The mime type of the audio, only used with data.
        kwargs (Any): Any additional arguments:
            inner_content (Any): The inner content of the response,
                this should hold all the information from the response so even
                when not creating a subclass a developer can leverage the full thing.
            ai_model_id (str | None): The id of the AI model that generated this response.
            metadata (dict[str, Any]): Any metadata that should be attached to the response.
    """

    content_type: Literal[ContentTypes.AUDIO_CONTENT] = Field(AUDIO_CONTENT_TAG, init=False)  # type: ignore
    tag: ClassVar[str] = AUDIO_CONTENT_TAG

    @classmethod
    def from_audio_file(cls: type[_T], path: str) -> "AudioContent":
        """Create an instance from an audio file."""
        mime_type = mimetypes.guess_type(path)[0]
        with open(path, "rb") as audio_file:
            return cls(data=audio_file.read(), data_format="base64", mime_type=mime_type, uri=path)

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {"type": "audio_url", "audio_url": {"uri": str(self)}}
