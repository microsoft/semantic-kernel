# Copyright (c) Microsoft. All rights reserved.


import pytest
from numpy import array

from semantic_kernel.contents.binary_content import BinaryContent

test_cases = [
    pytest.param(BinaryContent(uri="http://test_uri"), id="uri"),
    pytest.param(BinaryContent(data=b"test_data", mime_type="image/jpeg", data_format="base64"), id="data"),
    pytest.param(BinaryContent(data="test_data", mime_type="image/jpeg"), id="data_str"),
    pytest.param(BinaryContent(uri="http://test_uri", data=b"test_data", mime_type="image/jpeg"), id="both"),
    pytest.param(BinaryContent(data_uri="data:image/jpeg;base64,dGVzdF9kYXRh"), id="data_uri"),
    pytest.param(BinaryContent(data_uri="data:image/jpeg;base64,dGVzdF9kYXRh"), id="data_uri_with_params"),
    pytest.param(
        BinaryContent(data_uri="data:image/jpeg;foo=bar;base64,dGVzdF9kYXRh", metadata={"bar": "baz"}),
        id="data_uri_with_params_and_metadata",
    ),
    pytest.param(
        BinaryContent(data=array([1, 2, 3]), mime_type="application/json", data_format="base64"), id="data_array"
    ),
]


def test_create_empty():
    binary = BinaryContent()
    assert binary.uri is None
    assert binary.data == b""
    assert binary.mime_type == "text/plain"
    assert binary.metadata == {}


def test_create_uri():
    binary = BinaryContent(uri="http://test_uri")
    assert str(binary.uri) == "http://test_uri/"


def test_create_data():
    binary = BinaryContent(data=b"test_data", mime_type="application/json")
    assert binary.mime_type == "application/json"
    assert binary.data == b"test_data"


def test_create_data_uri():
    binary = BinaryContent(data_uri="data:application/json;base64,dGVzdF9kYXRh")
    assert binary.mime_type == "application/json"
    assert binary.data.decode() == "test_data"


def test_create_data_uri_with_params():
    binary = BinaryContent(data_uri="data:image/jpeg;foo=bar;base64,dGVzdF9kYXRh")
    assert binary.metadata == {"foo": "bar"}


def test_create_data_uri_with_params_and_metadata():
    binary = BinaryContent(data_uri="data:image/jpeg;foo=bar;base64,dGVzdF9kYXRh", metadata={"bar": "baz"})
    assert binary.metadata == {"foo": "bar", "bar": "baz"}


def test_update_data():
    binary = BinaryContent()
    binary.data = b"test_data"
    binary.mime_type = "application/json"
    assert binary.mime_type == "application/json"
    assert binary.data == b"test_data"


def test_update_data_str():
    binary = BinaryContent()
    binary.data = "test_data"
    binary.mime_type = "application/json"
    assert binary.mime_type == "application/json"
    assert binary.data == b"test_data"


def test_update_existing_data():
    binary = BinaryContent(data_uri="data:image/jpeg;foo=bar;base64,dGVzdF9kYXRh", metadata={"bar": "baz"})
    assert binary._data_uri is not None
    binary._data_uri.data_format = None
    binary.data = "test_data"
    binary.data = b"test_data"
    assert binary.data == b"test_data"


def test_update_data_uri():
    binary = BinaryContent()
    binary.data_uri = "data:image/jpeg;foo=bar;base64,dGVzdF9kYXRh"
    assert binary.mime_type == "image/jpeg"
    assert binary.data.decode() == "test_data"
    assert binary.metadata == {"foo": "bar"}


def test_to_str_uri():
    binary = BinaryContent(uri="http://test_uri")
    assert str(binary) == "http://test_uri/"


def test_to_str_data():
    binary = BinaryContent(data=b"test_data", mime_type="image/jpeg", data_format="base64")
    assert str(binary) == "data:image/jpeg;base64,dGVzdF9kYXRh"


@pytest.mark.parametrize("binary", test_cases)
def test_element_roundtrip(binary):
    element = binary.to_element()
    new_image = BinaryContent.from_element(element)
    assert new_image == binary


@pytest.mark.parametrize("binary", test_cases)
def test_to_dict(binary):
    assert binary.to_dict() == {"type": "binary", "binary": {"uri": str(binary)}}
