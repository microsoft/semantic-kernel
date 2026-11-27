# Copyright (c) Microsoft. All rights reserved.

import os

import pytest

from semantic_kernel.contents.image_content import ImageContent

test_cases = [
    pytest.param(ImageContent(uri="http://test_uri"), id="uri"),
    pytest.param(ImageContent(data=b"test_data", mime_type="image/jpeg", data_format="base64"), id="data"),
    pytest.param(ImageContent(uri="http://test_uri", data=b"test_data", mime_type="image/jpeg"), id="both"),
    pytest.param(
        ImageContent.from_image_path(
            image_path=os.path.join(os.path.dirname(__file__), "../../", "assets/sample_image.jpg")
        ),
        id="image_file",
    ),
]


def test_create_uri():
    image = ImageContent(uri="http://test_uri")
    assert str(image.uri) == "http://test_uri/"


def test_create_file_from_path():
    image_path = os.path.join(os.path.dirname(__file__), "../../", "assets/sample_image.jpg")
    image = ImageContent.from_image_path(image_path=image_path)
    assert image.mime_type == "image/jpeg"
    assert image.data_uri.startswith("data:image/jpeg;")
    assert image.data is not None


def test_create_data():
    image = ImageContent(data=b"test_data", mime_type="image/jpeg")
    assert image.mime_type == "image/jpeg"
    assert image.data == b"test_data"


def test_to_str_uri():
    image = ImageContent(uri="http://test_uri")
    assert str(image) == "http://test_uri/"


def test_to_str_data():
    image = ImageContent(data=b"test_data", mime_type="image/jpeg", data_format="base64")
    assert str(image) == "data:image/jpeg;base64,dGVzdF9kYXRh"


@pytest.mark.parametrize("image", test_cases)
def test_element_roundtrip(image):
    element = image.to_element()
    new_image = ImageContent.from_element(element)
    assert new_image == image


@pytest.mark.parametrize("image", test_cases)
def test_to_dict(image):
    assert image.to_dict() == {"type": "image_url", "image_url": {"url": str(image)}}


def test_image_content_raw_bytes_without_data_format():
    """Test ImageContent with raw non-UTF8 binary bytes doesn't raise UnicodeDecodeError."""
    from semantic_kernel.contents.chat_message_content import ChatMessageContent

    raw_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    image = ImageContent(data=raw_png, mime_type="image/png")
    assert image.data_uri == "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg=="
    assert str(image) == "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg=="

    # Element and prompt conversion
    element = image.to_element()
    assert element.text == "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg=="

    msg = ChatMessageContent(role="user", items=[image])
    prompt = msg.to_prompt()
    assert "<image>data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==</image>" in prompt


def test_image_content_xml_unsafe_payload_prompt_roundtrip():
    """Test ImageContent with control characters (e.g. b'\\x00\\x01') roundtrips cleanly in chat prompt XML."""
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent

    raw_payload = b"\x00\x01\x02"
    image = ImageContent(data=raw_payload, mime_type="image/png")
    assert image.data_uri == "data:image/png;base64,AAEC"

    msg = ChatMessageContent(role="user", items=[image])
    rendered = msg.to_prompt()
    assert "<image>data:image/png;base64,AAEC</image>" in rendered

    # Verify round-trip parsing via ChatHistory.from_rendered_prompt
    history = ChatHistory.from_rendered_prompt(rendered)
    assert len(history.messages) == 1
    assert len(history.messages[0].items) == 1
    parsed_item = history.messages[0].items[0]
    assert isinstance(parsed_item, ImageContent)
    assert parsed_item.data == raw_payload


