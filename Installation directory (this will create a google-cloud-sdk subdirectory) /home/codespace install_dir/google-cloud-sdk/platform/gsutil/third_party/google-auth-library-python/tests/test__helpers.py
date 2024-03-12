# Copyright 2016 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime

import pytest  # type: ignore
from six.moves import urllib

from google.auth import _helpers


class SourceClass(object):
    def func(self):  # pragma: NO COVER
        """example docstring"""


def test_copy_docstring_success():
    def func():  # pragma: NO COVER
        pass

    _helpers.copy_docstring(SourceClass)(func)

    assert func.__doc__ == SourceClass.func.__doc__


def test_copy_docstring_conflict():
    def func():  # pragma: NO COVER
        """existing docstring"""
        pass

    with pytest.raises(ValueError):
        _helpers.copy_docstring(SourceClass)(func)


def test_copy_docstring_non_existing():
    def func2():  # pragma: NO COVER
        pass

    with pytest.raises(AttributeError):
        _helpers.copy_docstring(SourceClass)(func2)


def test_utcnow():
    assert isinstance(_helpers.utcnow(), datetime.datetime)


def test_datetime_to_secs():
    assert _helpers.datetime_to_secs(datetime.datetime(1970, 1, 1)) == 0
    assert _helpers.datetime_to_secs(datetime.datetime(1990, 5, 29)) == 643939200


def test_to_bytes_with_bytes():
    value = b"bytes-val"
    assert _helpers.to_bytes(value) == value


def test_to_bytes_with_unicode():
    value = u"string-val"
    encoded_value = b"string-val"
    assert _helpers.to_bytes(value) == encoded_value


def test_to_bytes_with_nonstring_type():
    with pytest.raises(ValueError):
        _helpers.to_bytes(object())


def test_from_bytes_with_unicode():
    value = u"bytes-val"
    assert _helpers.from_bytes(value) == value


def test_from_bytes_with_bytes():
    value = b"string-val"
    decoded_value = u"string-val"
    assert _helpers.from_bytes(value) == decoded_value


def test_from_bytes_with_nonstring_type():
    with pytest.raises(ValueError):
        _helpers.from_bytes(object())


def _assert_query(url, expected):
    parts = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qs(parts.query)
    assert query == expected


def test_update_query_params_no_params():
    uri = "http://www.google.com"
    updated = _helpers.update_query(uri, {"a": "b"})
    assert updated == uri + "?a=b"


def test_update_query_existing_params():
    uri = "http://www.google.com?x=y"
    updated = _helpers.update_query(uri, {"a": "b", "c": "d&"})
    _assert_query(updated, {"x": ["y"], "a": ["b"], "c": ["d&"]})


def test_update_query_replace_param():
    base_uri = "http://www.google.com"
    uri = base_uri + "?x=a"
    updated = _helpers.update_query(uri, {"x": "b", "y": "c"})
    _assert_query(updated, {"x": ["b"], "y": ["c"]})


def test_update_query_remove_param():
    base_uri = "http://www.google.com"
    uri = base_uri + "?x=a"
    updated = _helpers.update_query(uri, {"y": "c"}, remove=["x"])
    _assert_query(updated, {"y": ["c"]})


def test_scopes_to_string():
    cases = [
        ("", ()),
        ("", []),
        ("", ("",)),
        ("", [""]),
        ("a", ("a",)),
        ("b", ["b"]),
        ("a b", ["a", "b"]),
        ("a b", ("a", "b")),
        ("a b", (s for s in ["a", "b"])),
    ]
    for expected, case in cases:
        assert _helpers.scopes_to_string(case) == expected


def test_string_to_scopes():
    cases = [("", []), ("a", ["a"]), ("a b c d e f", ["a", "b", "c", "d", "e", "f"])]

    for case, expected in cases:
        assert _helpers.string_to_scopes(case) == expected


def test_padded_urlsafe_b64decode():
    cases = [
        ("YQ==", b"a"),
        ("YQ", b"a"),
        ("YWE=", b"aa"),
        ("YWE", b"aa"),
        ("YWFhYQ==", b"aaaa"),
        ("YWFhYQ", b"aaaa"),
        ("YWFhYWE=", b"aaaaa"),
        ("YWFhYWE", b"aaaaa"),
    ]

    for case, expected in cases:
        assert _helpers.padded_urlsafe_b64decode(case) == expected


def test_unpadded_urlsafe_b64encode():
    cases = [(b"", b""), (b"a", b"YQ"), (b"aa", b"YWE"), (b"aaa", b"YWFh")]

    for case, expected in cases:
        assert _helpers.unpadded_urlsafe_b64encode(case) == expected
