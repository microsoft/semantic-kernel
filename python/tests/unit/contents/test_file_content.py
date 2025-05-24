# Copyright (c) Microsoft. All rights reserved.

import os
import pytest

from semantic_kernel.contents.file_content import FileContent

test_cases = [
    pytest.param(
        FileContent(
            filename="sample_file.pdf",
            data=b"test_pdf_data",
            mime_type="application/pdf",
        ),
        id="data",
    ),
    pytest.param(
        FileContent.from_file(
            file_path=os.path.join(
                os.path.dirname(__file__), "../../", "assets/sample_file.pdf"
            )
        ),
        id="file_path",
    ),
]


def test_create_data():
    file = FileContent(
        filename="sample_file.pdf", data=b"test_pdf_data", mime_type="application/pdf"
    )
    assert file.mime_type == "application/pdf"
    assert file.data == b"test_pdf_data"
    assert file.filename == "sample_file.pdf"


def test_create_file_from_path():
    file_path = os.path.join(
        os.path.dirname(__file__), "../../", "assets/sample_file.pdf"
    )
    file = FileContent.from_file(file_path=file_path)
    assert file.mime_type == "application/pdf"
    assert file.filename == "sample_file.pdf"
    assert file.data is not None


def test_to_str_data():
    file = FileContent(
        filename="sample_file.pdf", data=b"test_pdf_data", mime_type="application/pdf"
    )
    assert str(file).startswith("data:application/pdf;")


@pytest.mark.parametrize("file", test_cases)
def test_element_roundtrip(file):
    element = file.to_element()
    new_file = FileContent.from_element(element)
    assert new_file == file


@pytest.mark.parametrize("file", test_cases)
def test_to_dict(file):
    assert file.to_dict() == {
        "type": "input_file",
        "filename": "sample_file.pdf",
        "file_data": str(file),
    }
