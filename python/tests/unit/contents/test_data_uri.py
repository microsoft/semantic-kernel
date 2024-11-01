# Copyright (c) Microsoft. All rights reserved.

from typing import Any

import pytest

from semantic_kernel.contents.utils.data_uri import DataUri
from semantic_kernel.exceptions.content_exceptions import ContentInitializationError


@pytest.mark.parametrize(
    "uri, data_bytes, data_str, mime_type, parameters, data_format",
    [
        pytest.param(
            "data:image/jpeg;base64,dGVzdF9kYXRh",
            b"test_data",
            "dGVzdF9kYXRh",
            "image/jpeg",
            {},
            "base64",
            id="basic_image",
        ),
        pytest.param("data:text/plain;,test_data", None, "test_data", "text/plain", {}, None, id="basic_text"),
        pytest.param(
            "data:application/octet-stream;base64,AQIDBA==",
            b"\x01\x02\x03\x04",
            "AQIDBA==",
            "application/octet-stream",
            {},
            "base64",
            id="basic_binary",
        ),
        pytest.param(
            "data:text/plain;base64,U29t\r\nZQ==\t",
            b"Some",
            "U29tZQ==",
            "text/plain",
            {},
            "base64",
            id="strip_whitespace",
        ),
        pytest.param(
            "data:application/octet-stream;utf8,01-02-03-04",
            None,
            "01-02-03-04",
            "application/octet-stream",
            {},
            "utf8",
            id="utf8",
        ),
    ],
)
def test_data_uri_from_data_uri_str(
    uri: str,
    data_bytes: bytes | None,
    data_str: str | None,
    mime_type: str | None,
    parameters: dict[str, str],
    data_format: str | None,
):
    data_uri = DataUri.from_data_uri(uri)
    assert data_uri.data_bytes == data_bytes
    assert data_uri.data_str == data_str
    assert data_uri.mime_type == mime_type
    assert data_uri.parameters == parameters
    assert data_uri.data_format == data_format


@pytest.mark.parametrize(
    "uri, exception",
    [
        pytest.param("", ContentInitializationError, id="empty"),
        pytest.param("data", ContentInitializationError, id="missing_colon"),
        pytest.param("data:", ContentInitializationError, id="missing_comma"),
        pytest.param("data:something,", ContentInitializationError, id="mime_type_without_subtype"),
        pytest.param("data:something;else,data", ContentInitializationError, id="mime_type_without_subtype2"),
        pytest.param(
            "data:type/subtype;parameterwithoutvalue;else,", ContentInitializationError, id="param_without_value"
        ),
        pytest.param("data:type/subtype;parameter=va=lue;else,", ContentInitializationError, id="param_multiple_eq"),
        pytest.param("data:type/subtype;=value;else,", ContentInitializationError, id="param_without_name"),
        pytest.param("data:image/jpeg;base64,dGVzdF9kYXRh;foo=bar", ContentInitializationError, id="wrong_order"),
        pytest.param("data:text/plain;test_data", ContentInitializationError, id="missing_comma"),
        pytest.param(
            "data:text/plain;base64,something!",
            ContentInitializationError,
            id="invalid_char",
        ),
        pytest.param(
            "data:text/plain;base64,U29",
            ContentInitializationError,
            id="missing_padding",
        ),
    ],
)
def test_data_uri_from_data_uri_fail(uri: str, exception: type[Exception]):
    with pytest.raises(exception):
        DataUri.from_data_uri(uri)


def test_data_uri_to_string_with_extra_metadata():
    uri = DataUri.from_data_uri("data:image/jpeg;base64,dGVzdF9kYXRh")
    assert uri.to_string(metadata={"foo": "bar"}) == "data:image/jpeg;foo=bar;base64,dGVzdF9kYXRh"


def test_default_mime_type():
    uri = DataUri.from_data_uri("data:;base64,dGVzdF9kYXRh", default_mime_type="image/jpeg")
    assert uri.mime_type == "image/jpeg"


@pytest.mark.parametrize(
    "fields, uri",
    [
        pytest.param(
            {
                "data_bytes": b"test_data",
                "mime_type": "image/jpeg",
                "data_format": "base64",
            },
            "data:image/jpeg;base64,dGVzdF9kYXRh",
            id="basic_image",
        ),
        pytest.param(
            {"data_str": "test_data", "mime_type": "text/plain"}, "data:text/plain;,test_data", id="basic_text"
        ),
        pytest.param(
            {
                "data_bytes": b"\x01\x02\x03\x04",
                "mime_type": "application/octet-stream",
                "data_format": "base64",
            },
            "data:application/octet-stream;base64,AQIDBA==",
            id="basic_binary",
        ),
        pytest.param(
            {
                "data_str": "test_data/r/t",
                "mime_type": "image/jpeg",
            },
            "data:image/jpeg;,test_data/r/t",
            id="whitespace_not_base64",
        ),
        pytest.param(
            {
                "data_bytes": b"test_data",
                "mime_type": "image/jpeg",
                "data_format": "base64",
                "parameters": None,
            },
            "data:image/jpeg;base64,dGVzdF9kYXRh",
            id="param_none",
        ),
        pytest.param(
            {
                "data_bytes": b"test_data",
                "mime_type": "image/jpeg",
                "data_format": "base64",
                "parameters": [],
            },
            "data:image/jpeg;base64,dGVzdF9kYXRh",
            id="param_empty_list",
        ),
        pytest.param(
            {
                "data_bytes": b"test_data",
                "mime_type": "image/jpeg",
                "data_format": "base64",
                "parameters": [""],
            },
            "data:image/jpeg;base64,dGVzdF9kYXRh",
            id="param_empty_list",
        ),
        pytest.param(
            {
                "data_bytes": b"test_data",
                "mime_type": "image/jpeg",
                "data_format": "base64",
                "parameters": {},
            },
            "data:image/jpeg;base64,dGVzdF9kYXRh",
            id="param_empty_dict",
        ),
        pytest.param(
            {
                "data_bytes": b"test_data",
                "mime_type": "image/jpeg",
                "data_format": "base64",
                "parameters": {"foo": "bar"},
            },
            "data:image/jpeg;base64,dGVzdF9kYXRh",
            id="param_dict",
        ),
    ],
)
def test_data_uri_from_fields(fields: dict[str, Any], uri: str):
    data_uri = DataUri(**fields)
    assert data_uri.to_string() == uri


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param(
            {
                "data_str": "test_data/r/t",
                "mime_type": "image/jpeg",
                "data_format": "base64",
            },
            id="whitespace",
        ),
        pytest.param(
            {
                "data_str": "test_data/r/t",
                "mime_type": "image/jpeg",
                "data_format": "base64",
                "parameters": ["foo"],
            },
            id="invalid_params",
        ),
    ],
)
def test_data_uri_from_fields_fail(fields: dict[str, Any]):
    with pytest.raises(ContentInitializationError):
        DataUri(**fields)


def test_eq():
    data_uri1 = DataUri.from_data_uri("data:image/jpeg;base64,dGVzdF9kYXRh")
    data_uri2 = DataUri.from_data_uri("data:image/jpeg;base64,dGVzdF9kYXRh")
    assert data_uri1 == data_uri2
    assert data_uri1 != "data:image/jpeg;base64,dGVzdF9kYXRh"
    assert data_uri1 != DataUri.from_data_uri("data:image/jpeg;base64,dGVzdF9kYXRi")
