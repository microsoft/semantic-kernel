# Copyright (c) Microsoft. All rights reserved.

import logging
import os
from unittest.mock import patch

import pytest

from semantic_kernel.contents.image_content import ImageContent


def test_create_uri():
    image = ImageContent(uri="http://test_uri")
    assert str(image.uri) == "http://test_uri/"


def test_create_file():
    path = __file__
    path = os.path.dirname(path)

    image_path = os.path.join(path, "sample_image.jpg")
    image = ImageContent.from_image_file(image_path=image_path)
    assert image.mime_type == "image/jpeg"
    assert image.data is not None


def test_create_data():
    image = ImageContent(data=b"test_data", mime_type="image/jpeg")
    assert image.mime_type == "image/jpeg"
    assert image.data == b"test_data"


def test_create_empty_fail():
    with pytest.raises(ValueError):
        ImageContent()


def test_create_both_log():
    with patch("semantic_kernel.contents.image_content.logger", spec=logging.Logger) as mock_log:
        ImageContent(uri="http://test_uri", data=b"test_data", mime_type="image/jpeg")
        mock_log.warning.assert_called_once_with('Both "uri" and "data" are provided, "data" will be used.')


def test_to_str_uri():
    image = ImageContent(uri="http://test_uri")
    assert str(image) == "http://test_uri/"


def test_to_str_data():
    image = ImageContent(data=b"test_data", mime_type="image/jpeg")
    assert str(image) == "data:image/jpeg;base64,dGVzdF9kYXRh"
