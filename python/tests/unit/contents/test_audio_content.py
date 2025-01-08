# Copyright (c) Microsoft. All rights reserved.

import os

import pytest

from semantic_kernel.contents.audio_content import AudioContent

test_cases = [
    pytest.param(AudioContent(uri="http://test_uri"), id="uri"),
    pytest.param(AudioContent(data=b"test_data", mime_type="image/jpeg", data_format="base64"), id="data"),
    pytest.param(AudioContent(uri="http://test_uri", data=b"test_data", mime_type="image/jpeg"), id="both"),
    pytest.param(
        AudioContent.from_image_path(
            image_path=os.path.join(os.path.dirname(__file__), "../../", "assets/sample_image.jpg")
        ),
        id="image_file",
    ),
]


def test_create_uri():
    image = AudioContent(uri="http://test_uri")
    assert str(image.uri) == "http://test_uri/"


def test_create_file_from_path():
    image_path = os.path.join(os.path.dirname(__file__), "../../", "assets/sample_image.jpg")
    image = AudioContent.from_image_path(image_path=image_path)
    assert image.mime_type == "image/jpeg"
    assert image.data_uri.startswith("data:image/jpeg;")
    assert image.data is not None


def test_create_data():
    image = AudioContent(data=b"test_data", mime_type="image/jpeg")
    assert image.mime_type == "image/jpeg"
    assert image.data == b"test_data"


def test_to_str_uri():
    image = AudioContent(uri="http://test_uri")
    assert str(image) == "http://test_uri/"


def test_to_str_data():
    image = AudioContent(data=b"test_data", mime_type="image/jpeg", data_format="base64")
    assert str(image) == "data:image/jpeg;base64,dGVzdF9kYXRh"


@pytest.mark.parametrize("image", test_cases)
def test_element_roundtrip(image):
    element = image.to_element()
    new_image = AudioContent.from_element(element)
    assert new_image == image


@pytest.mark.parametrize("image", test_cases)
def test_to_dict(image):
    assert image.to_dict() == {"type": "image_url", "image_url": {"url": str(image)}}
