# Copyright (c) Microsoft. All rights reserved.


import tempfile
from pathlib import Path

import pytest
from numpy import array

from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.exceptions.content_exceptions import ContentInitializationError

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


def test_can_read_with_data():
    """Test can_read property returns True when data is available."""
    binary = BinaryContent(data=b"test_data", mime_type="application/pdf")
    assert binary.can_read is True


def test_can_read_without_data():
    """Test can_read property returns False when no data is available."""
    binary = BinaryContent(uri="http://example.com/file.pdf")
    assert binary.can_read is False


def test_can_read_empty():
    """Test can_read property returns False for empty BinaryContent."""
    binary = BinaryContent()
    assert binary.can_read is False


def test_from_file_success():
    """Test from_file class method successfully creates BinaryContent from a file."""
    test_data = b"This is test file content"
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(test_data)
        temp_file_path = temp_file.name

    try:
        binary = BinaryContent.from_file(temp_file_path, mime_type="application/pdf")
        assert binary.data == test_data
        assert binary.mime_type == "application/pdf"
        assert binary.uri == temp_file_path
        assert binary.can_read is True
        # Verify data_string works (should be base64 encoded)
        assert binary.data_string == "VGhpcyBpcyB0ZXN0IGZpbGUgY29udGVudA=="
    finally:
        Path(temp_file_path).unlink()


def test_from_file_with_path_object():
    """Test from_file class method works with Path objects."""
    test_data = b"Path object test content"
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(test_data)
        temp_path = Path(temp_file.name)

    try:
        binary = BinaryContent.from_file(temp_path, mime_type="text/plain")
        assert binary.data == test_data
        assert binary.mime_type == "text/plain"
        assert binary.uri == str(temp_path)
        # Verify data_string works (should be base64 encoded)
        assert binary.data_string == "UGF0aCBvYmplY3QgdGVzdCBjb250ZW50"
    finally:
        temp_path.unlink()


def test_from_file_binary_data():
    """Test from_file handles binary data correctly without encoding errors."""
    # Test with actual binary PDF-like data
    test_data = b"%PDF-1.4\n%\xf6\xe4\xfc\xdf\n1 0 obj\n<<\n/Type /Catalog"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(test_data)
        temp_file_path = temp_file.name

    try:
        binary = BinaryContent.from_file(temp_file_path, mime_type="application/pdf")
        assert binary.data == test_data
        assert binary.mime_type == "application/pdf"
        assert binary.can_read is True
        # Should not raise Unicode decode error
        data_string = binary.data_string
        assert isinstance(data_string, str)
        assert len(data_string) > 0
    finally:
        Path(temp_file_path).unlink()


def test_from_file_nonexistent():
    """Test from_file raises FileNotFoundError for nonexistent files."""
    with pytest.raises(FileNotFoundError, match="File not found"):
        BinaryContent.from_file("/nonexistent/file.pdf")


def test_from_file_directory():
    """Test from_file raises ContentInitializationError for directories."""
    with (
        tempfile.TemporaryDirectory() as temp_dir,
        pytest.raises(ContentInitializationError, match="Path is not a file"),
    ):
        BinaryContent.from_file(temp_dir)
