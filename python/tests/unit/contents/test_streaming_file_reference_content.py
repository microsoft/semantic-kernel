# Copyright (c) Microsoft. All rights reserved.

from xml.etree.ElementTree import Element

import pytest

from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent


def test_create_empty():
    file_reference = StreamingFileReferenceContent()
    assert file_reference.file_id is None


def test_create_file_id():
    file_reference = StreamingFileReferenceContent(file_id="12345")
    assert file_reference.file_id == "12345"


def test_update_file_id():
    file_reference = StreamingFileReferenceContent()
    file_reference.file_id = "12345"
    assert file_reference.file_id == "12345"


def test_to_str():
    file_reference = StreamingFileReferenceContent(file_id="12345")
    assert str(file_reference) == "StreamingFileReferenceContent(file_id=12345)"


def test_to_element():
    file_reference = StreamingFileReferenceContent(file_id="12345")
    element = file_reference.to_element()
    assert element.tag == "streaming_file_reference"
    assert element.get("file_id") == "12345"


def test_from_element():
    element = Element("StreamingFileReferenceContent")
    element.set("file_id", "12345")
    file_reference = StreamingFileReferenceContent.from_element(element)
    assert file_reference.file_id == "12345"


def test_to_dict_simple():
    file_reference = StreamingFileReferenceContent(file_id="12345")
    assert file_reference.to_dict() == {
        "file_id": "12345",
    }


@pytest.mark.parametrize(
    "file_reference",
    [
        pytest.param(StreamingFileReferenceContent(file_id="12345"), id="file_id"),
        pytest.param(StreamingFileReferenceContent(), id="empty"),
    ],
)
def test_element_roundtrip(file_reference):
    element = file_reference.to_element()
    new_file_reference = StreamingFileReferenceContent.from_element(element)
    assert new_file_reference == file_reference


@pytest.mark.parametrize(
    "file_reference",
    [
        pytest.param(StreamingFileReferenceContent(file_id="12345"), id="file_id"),
        pytest.param(StreamingFileReferenceContent(), id="empty"),
    ],
)
def test_to_dict(file_reference):
    expected_dict = {
        "file_id": file_reference.file_id,
    }
    assert file_reference.to_dict() == expected_dict
