from test import SHORT_TIMEOUT
from test.with_dummyserver import test_connectionpool

import pytest

import dummyserver.testcase
import urllib3.exceptions
import urllib3.util.retry
import urllib3.util.url
from urllib3.contrib import appengine


# This class is used so we can re-use the tests from the connection pool.
# It proxies all requests to the manager.
class MockPool(object):
    def __init__(self, host, port, manager, scheme="http"):
        self.host = host
        self.port = port
        self.manager = manager
        self.scheme = scheme

    def request(self, method, url, *args, **kwargs):
        url = self._absolute_url(url)
        return self.manager.request(method, url, *args, **kwargs)

    def urlopen(self, method, url, *args, **kwargs):
        url = self._absolute_url(url)
        return self.manager.urlopen(method, url, *args, **kwargs)

    def _absolute_url(self, path):
        return urllib3.util.url.Url(
            scheme=self.scheme, host=self.host, port=self.port, path=path
        ).url


# Note that this doesn't run in the sandbox, it only runs with the URLFetch
# API stub enabled. There's no need to enable the sandbox as we know for a fact
# that URLFetch is used by the connection manager.
@pytest.mark.usefixtures("testbed")
class TestGAEConnectionManager(test_connectionpool.TestConnectionPool):
    def setup_method(self, method):
        self.manager = appengine.AppEngineManager()
        self.pool = MockPool(self.host, self.port, self.manager)

    # Tests specific to AppEngineManager

    def test_exceptions(self):
        # DeadlineExceededError -> TimeoutError
        with pytest.raises(urllib3.exceptions.TimeoutError):
            self.pool.request(
                "GET",
                "/sleep?seconds={}".format(5 * SHORT_TIMEOUT),
                timeout=SHORT_TIMEOUT,
            )

        # InvalidURLError -> ProtocolError
        with pytest.raises(urllib3.exceptions.ProtocolError):
            self.manager.request("GET", "ftp://invalid/url")

        # DownloadError -> ProtocolError
        with pytest.raises(urllib3.exceptions.ProtocolError):
            self.manager.request("GET", "http://0.0.0.0")

        # ResponseTooLargeError -> AppEnginePlatformError
        with pytest.raises(appengine.AppEnginePlatformError):
            self.pool.request(
                "GET", "/nbytes?length=33554433"
            )  # One byte over 32 megabytes.

        # URLFetch reports the request too large error as a InvalidURLError,
        # which maps to a AppEnginePlatformError.
        body = b"1" * 10485761  # One byte over 10 megabytes.
        with pytest.raises(appengine.AppEnginePlatformError):
            self.manager.request("POST", "/", body=body)

    # Re-used tests below this line.
    # Subsumed tests
    test_timeout_float = None  # Covered by test_exceptions.

    # Non-applicable tests
    test_conn_closed = None
    test_nagle = None
    test_socket_options = None
    test_disable_default_socket_options = None
    test_defaults_are_applied = None
    test_tunnel = None
    test_keepalive = None
    test_keepalive_close = None
    test_connection_count = None
    test_connection_count_bigpool = None
    test_for_double_release = None
    test_release_conn_parameter = None
    test_stream_keepalive = None
    test_cleanup_on_connection_error = None
    test_read_chunked_short_circuit = None
    test_read_chunked_on_closed_response = None

    # Tests that should likely be modified for appengine specific stuff
    test_timeout = None
    test_connect_timeout = None
    test_connection_error_retries = None
    test_total_timeout = None
    test_none_total_applies_connect = None
    test_timeout_success = None
    test_source_address_error = None
    test_bad_connect = None
    test_partial_response = None
    test_dns_error = None


@pytest.mark.usefixtures("testbed")
class TestGAEConnectionManagerWithSSL(dummyserver.testcase.HTTPSDummyServerTestCase):
    def setup_method(self, method):
        self.manager = appengine.AppEngineManager()
        self.pool = MockPool(self.host, self.port, self.manager, "https")

    def test_exceptions(self):
        # SSLCertificateError -> SSLError
        # SSLError is raised with dummyserver because URLFetch doesn't allow
        # self-signed certs.
        with pytest.raises(urllib3.exceptions.SSLError):
            self.pool.request("GET", "/")


@pytest.mark.usefixtures("testbed")
class TestGAERetry(test_connectionpool.TestRetry):
    def setup_method(self, method):
        self.manager = appengine.AppEngineManager()
        self.pool = MockPool(self.host, self.port, self.manager)

    def test_default_method_whitelist_retried(self):
        """urllib3 should retry methods in the default method whitelist"""
        retry = urllib3.util.retry.Retry(total=1, status_forcelist=[418])
        # Use HEAD instead of OPTIONS, as URLFetch doesn't support OPTIONS
        resp = self.pool.request(
            "HEAD",
            "/successful_retry",
            headers={"test-name": "test_default_whitelist"},
            retries=retry,
        )
        assert resp.status == 200

    def test_retry_return_in_response(self):
        headers = {"test-name": "test_retry_return_in_response"}
        retry = urllib3.util.retry.Retry(total=2, status_forcelist=[418])
        resp = self.pool.request(
            "GET", "/successful_retry", headers=headers, retries=retry
        )
        assert resp.status == 200
        assert resp.retries.total == 1
        # URLFetch use absolute urls.
        assert resp.retries.history == (
            urllib3.util.retry.RequestHistory(
                "GET", self.pool._absolute_url("/successful_retry"), None, 418, None
            ),
        )

    # test_max_retry = None
    # test_disabled_retry = None
    # We don't need these tests because URLFetch resolves its own redirects.
    test_retry_redirect_history = None
    test_multi_redirect_history = None


@pytest.mark.usefixtures("testbed")
class TestGAERetryAfter(test_connectionpool.TestRetryAfter):
    def setup_method(self, method):
        # Disable urlfetch which doesn't respect Retry-After header.
        self.manager = appengine.AppEngineManager(urlfetch_retries=False)
        self.pool = MockPool(self.host, self.port, self.manager)


def test_gae_environ():
    assert not appengine.is_appengine()
    assert not appengine.is_appengine_sandbox()
    assert not appengine.is_local_appengine()
    assert not appengine.is_prod_appengine()
    assert not appengine.is_prod_appengine_mvms()
