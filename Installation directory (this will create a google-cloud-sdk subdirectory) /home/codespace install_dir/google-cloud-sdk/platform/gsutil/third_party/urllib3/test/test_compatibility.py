import warnings

import pytest

from urllib3.connection import HTTPConnection
from urllib3.packages.six.moves import http_cookiejar, urllib
from urllib3.response import HTTPResponse


class TestVersionCompatibility(object):
    def test_connection_strict(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # strict=True is deprecated in Py33+
            HTTPConnection("localhost", 12345, strict=True)

            if w:
                pytest.fail(
                    "HTTPConnection raised warning on strict=True: %r" % w[0].message
                )

    def test_connection_source_address(self):
        try:
            # source_address does not exist in Py26-
            HTTPConnection("localhost", 12345, source_address="127.0.0.1")
        except TypeError as e:
            pytest.fail("HTTPConnection raised TypeError on source_address: %r" % e)


class TestCookiejar(object):
    def test_extract(self):
        request = urllib.request.Request("http://google.com")
        cookiejar = http_cookiejar.CookieJar()
        response = HTTPResponse()

        cookies = [
            "sessionhash=abcabcabcabcab; path=/; HttpOnly",
            "lastvisit=1348253375; expires=Sat, 21-Sep-2050 18:49:35 GMT; path=/",
        ]
        for c in cookies:
            response.headers.add("set-cookie", c)
        cookiejar.extract_cookies(response, request)
        assert len(cookiejar) == len(cookies)
