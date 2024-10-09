# Copyright (c) Microsoft. All rights reserved.

from xml.etree.ElementTree import Element

import pytest

from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent

test_cases = [
    pytest.param(StreamingAnnotationContent(file_id="12345"), id="file_id"),
    pytest.param(StreamingAnnotationContent(quote="This is a quote."), id="quote"),
    pytest.param(StreamingAnnotationContent(start_index=5, end_index=20), id="indices"),
    pytest.param(
        StreamingAnnotationContent(file_id="12345", quote="This is a quote.", start_index=5, end_index=20),
        id="all_fields",
    ),
]


def test_create_empty():
    annotation = StreamingAnnotationContent()
    assert annotation.file_id is None
    assert annotation.quote is None
    assert annotation.start_index is None
    assert annotation.end_index is None


def test_create_file_id():
    annotation = StreamingAnnotationContent(file_id="12345")
    assert annotation.file_id == "12345"


def test_create_quote():
    annotation = StreamingAnnotationContent(quote="This is a quote.")
    assert annotation.quote == "This is a quote."


def test_create_indices():
    annotation = StreamingAnnotationContent(start_index=5, end_index=20)
    assert annotation.start_index == 5
    assert annotation.end_index == 20


def test_create_all_fields():
    annotation = StreamingAnnotationContent(file_id="12345", quote="This is a quote.", start_index=5, end_index=20)
    assert annotation.file_id == "12345"
    assert annotation.quote == "This is a quote."
    assert annotation.start_index == 5
    assert annotation.end_index == 20


def test_update_file_id():
    annotation = StreamingAnnotationContent()
    annotation.file_id = "12345"
    assert annotation.file_id == "12345"


def test_update_quote():
    annotation = StreamingAnnotationContent()
    annotation.quote = "This is a quote."
    assert annotation.quote == "This is a quote."


def test_update_indices():
    annotation = StreamingAnnotationContent()
    annotation.start_index = 5
    annotation.end_index = 20
    assert annotation.start_index == 5
    assert annotation.end_index == 20


def test_to_str():
    annotation = StreamingAnnotationContent(file_id="12345", quote="This is a quote.", start_index=5, end_index=20)
    assert (
        str(annotation)
        == "StreamingAnnotationContent(file_id=12345, quote=This is a quote., start_index=5, end_index=20)"
    )


def test_to_element():
    annotation = StreamingAnnotationContent(file_id="12345", quote="This is a quote.", start_index=5, end_index=20)
    element = annotation.to_element()
    assert element.tag == "streaming_annotation"
    assert element.get("file_id") == "12345"
    assert element.get("quote") == "This is a quote."
    assert element.get("start_index") == "5"
    assert element.get("end_index") == "20"


def test_from_element():
    element = Element("StreamingAnnotationContent")
    element.set("file_id", "12345")
    element.set("quote", "This is a quote.")
    element.set("start_index", "5")
    element.set("end_index", "20")
    annotation = StreamingAnnotationContent.from_element(element)
    assert annotation.file_id == "12345"
    assert annotation.quote == "This is a quote."
    assert annotation.start_index == 5
    assert annotation.end_index == 20


def test_to_dict():
    annotation = StreamingAnnotationContent(file_id="12345", quote="This is a quote.", start_index=5, end_index=20)
    assert annotation.to_dict() == {
        "type": "text",
        "text": f"{annotation.file_id} {annotation.quote} (Start Index={annotation.start_index}->End Index={annotation.end_index})",  # noqa: E501
    }


@pytest.mark.parametrize("annotation", test_cases)
def test_element_roundtrip(annotation):
    element = annotation.to_element()
    new_annotation = StreamingAnnotationContent.from_element(element)
    assert new_annotation == annotation


@pytest.mark.parametrize("annotation", test_cases)
def test_to_dict_call(annotation):
    expected_dict = {
        "type": "text",
        "text": f"{annotation.file_id} {annotation.quote} (Start Index={annotation.start_index}->End Index={annotation.end_index})",  # noqa: E501
    }
    assert annotation.to_dict() == expected_dict
