# Copyright (c) Microsoft. All rights reserved.

import base64
import json

import pytest

from semantic_kernel.connectors.ai.anthropic.services.utils import (
    _format_user_message,
    kernel_function_metadata_to_function_call_format,
)
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata

_PNG_DATA_URI = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)
_PNG_BYTES = base64.b64decode(_PNG_DATA_URI.split(",", 1)[1])


def test_function_call_format_skips_params_excluded_from_function_choices() -> None:
    metadata = KernelFunctionMetadata(
        name="lookup",
        description="Look up a user",
        is_prompt=False,
        parameters=[
            KernelParameterMetadata(
                name="query", description="What to look up", schema_data={"type": "string"}, is_required=True
            ),
            KernelParameterMetadata(
                name="token",
                description="Internal",
                schema_data={"type": "string"},
                is_required=True,
                include_in_function_choices=False,
            ),
        ],
    )

    result = kernel_function_metadata_to_function_call_format(metadata)

    assert list(result["input_schema"]["properties"]) == ["query"]
    assert result["input_schema"]["required"] == ["query"]


def _user_message(items: list[object]) -> ChatMessageContent:
    return ChatMessageContent(role=AuthorRole.USER, items=items)


def test_format_user_message_text_only_keeps_string_content() -> None:
    result = _format_user_message(_user_message([TextContent(text="hello")]))

    assert result == {"role": "user", "content": "hello"}


def test_format_user_message_keeps_data_image_block() -> None:
    message = _user_message([
        TextContent(text="Analyze this image"),
        ImageContent(data_uri=_PNG_DATA_URI),
    ])

    blocks = _format_user_message(message)["content"]

    assert blocks[0] == {"type": "text", "text": "Analyze this image"}
    assert blocks[1]["type"] == "image"
    assert blocks[1]["source"]["type"] == "base64"
    assert blocks[1]["source"]["media_type"] == "image/png"
    assert blocks[1]["source"]["data"]


def test_format_user_message_image_only_is_a_valid_request() -> None:
    result = _format_user_message(_user_message([ImageContent(data_uri=_PNG_DATA_URI)]))

    blocks = result["content"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "image"
    assert blocks[0]["source"]["data"]


def test_format_user_message_uri_image_uses_url_source() -> None:
    url = "https://example.com/chart.png"
    result = _format_user_message(_user_message([ImageContent(uri=url)]))

    assert result["content"][0]["source"] == {"type": "url", "url": url}
    # The URI is stored as a pydantic Url object, so the payload must stay JSON-serializable.
    assert json.loads(json.dumps(result)) == result


def test_format_user_message_preserves_block_order() -> None:
    message = _user_message([
        TextContent(text="before"),
        ImageContent(data_uri=_PNG_DATA_URI),
        TextContent(text="after"),
    ])

    blocks = _format_user_message(message)["content"]

    assert [block["type"] for block in blocks] == ["text", "image", "text"]


def test_format_user_message_detects_media_type_of_raw_bytes() -> None:
    result = _format_user_message(_user_message([ImageContent(data=_PNG_BYTES)]))

    source = result["content"][0]["source"]
    assert source["type"] == "base64"
    assert source["media_type"] == "image/png"
    assert base64.b64decode(source["data"]) == _PNG_BYTES


@pytest.mark.parametrize(
    ("data", "media_type"),
    [
        (b"\x89PNG\r\n\x1a\n\x00\x00\x00\x00", "image/png"),
        (b"\xff\xd8\xff\xe0" + b"\x00" * 12, "image/jpeg"),
        (b"GIF87a" + b"\x00" * 12, "image/gif"),
        (b"GIF89a" + b"\x00" * 12, "image/gif"),
        (b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 8, "image/webp"),
    ],
)
def test_format_user_message_detects_supported_image_formats(data: bytes, media_type: str) -> None:
    result = _format_user_message(_user_message([ImageContent(data=data)]))

    assert result["content"][0]["source"]["media_type"] == media_type


def test_format_user_message_keeps_explicit_image_media_type() -> None:
    result = _format_user_message(_user_message([ImageContent(data=_PNG_BYTES, mime_type="image/png")]))

    assert result["content"][0]["source"]["media_type"] == "image/png"


def test_format_user_message_skips_image_with_unsupported_media_type(caplog: pytest.LogCaptureFixture) -> None:
    message = _user_message([TextContent(text="hello"), ImageContent(data=b"not-an-image")])

    result = _format_user_message(message)

    assert result["content"] == [{"type": "text", "text": "hello"}]
    assert "Skipping ImageContent with an unsupported" in caplog.text


def test_format_user_message_skips_non_image_data_uri(caplog: pytest.LogCaptureFixture) -> None:
    message = _user_message([ImageContent(data_uri="data:text/plain;base64,aGk=")])

    result = _format_user_message(message)

    assert result["content"] == []
    assert "Skipping ImageContent with an unsupported" in caplog.text
