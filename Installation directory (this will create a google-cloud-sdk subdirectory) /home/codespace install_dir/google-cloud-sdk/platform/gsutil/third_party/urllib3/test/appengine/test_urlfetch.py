"""These tests ensure that when running in App Engine standard with the
App Engine sandbox enabled that urllib3 appropriately uses the App
Engine-patched version of httplib to make requests."""

import httplib
import pytest
import StringIO
from mock import patch

from ..test_no_ssl import TestWithoutSSL


class MockResponse(object):
    def __init__(self, content, status_code, content_was_truncated, final_url, headers):

        self.content = content
        self.status_code = status_code
        self.content_was_truncated = content_was_truncated
        self.final_url = final_url
        self.header_msg = httplib.HTTPMessage(
            StringIO.StringIO(
                "".join(["%s: %s\n" % (k, v) for k, v in headers.iteritems()] + ["\n"])
            )
        )
        self.headers = headers


@pytest.mark.usefixtures("sandbox")
class TestHTTP(TestWithoutSSL):
    def test_urlfetch_called_with_http(self):
        """Check that URLFetch is used to fetch non-https resources."""
        resp = MockResponse(
            "OK", 200, False, "http://www.google.com", {"content-type": "text/plain"}
        )
        fetch_patch = patch("google.appengine.api.urlfetch.fetch", return_value=resp)
        with fetch_patch as fetch_mock:
            import urllib3

            pool = urllib3.HTTPConnectionPool("www.google.com", "80")
            r = pool.request("GET", "/")
            assert r.status == 200, r.data
            assert fetch_mock.call_count == 1


@pytest.mark.usefixtures("sandbox")
class TestHTTPS(object):
    @pytest.mark.xfail(
        reason="This is not yet supported by urlfetch, presence of the ssl "
        "module will bypass urlfetch."
    )
    def test_urlfetch_called_with_https(self):
        """
        Check that URLFetch is used when fetching https resources
        """
        resp = MockResponse(
            "OK", 200, False, "https://www.google.com", {"content-type": "text/plain"}
        )
        fetch_patch = patch("google.appengine.api.urlfetch.fetch", return_value=resp)
        with fetch_patch as fetch_mock:
            import urllib3

            pool = urllib3.HTTPSConnectionPool("www.google.com", "443")
            pool.ConnectionCls = urllib3.connection.UnverifiedHTTPSConnection
            r = pool.request("GET", "/")
            assert r.status == 200, r.data
            assert fetch_mock.call_count == 1
