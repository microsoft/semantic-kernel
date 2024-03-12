from __future__ import absolute_import

import ssl
from socket import error as SocketError
from ssl import SSLError as BaseSSLError
from test import SHORT_TIMEOUT

import pytest
from mock import Mock

from dummyserver.server import DEFAULT_CA
from urllib3._collections import HTTPHeaderDict
from urllib3.connectionpool import (
    HTTPConnection,
    HTTPConnectionPool,
    HTTPSConnectionPool,
    connection_from_url,
)
from urllib3.exceptions import (
    ClosedPoolError,
    EmptyPoolError,
    HostChangedError,
    LocationValueError,
    MaxRetryError,
    ProtocolError,
    SSLError,
    TimeoutError,
)
from urllib3.packages.six.moves import http_client as httplib
from urllib3.packages.six.moves.http_client import HTTPException
from urllib3.packages.six.moves.queue import Empty
from urllib3.response import HTTPResponse
from urllib3.util.ssl_match_hostname import CertificateError
from urllib3.util.timeout import Timeout

from .test_response import MockChunkedEncodingResponse, MockSock


class HTTPUnixConnection(HTTPConnection):
    def __init__(self, host, timeout=60, **kwargs):
        super(HTTPUnixConnection, self).__init__("localhost")
        self.unix_socket = host
        self.timeout = timeout
        self.sock = None


class HTTPUnixConnectionPool(HTTPConnectionPool):
    scheme = "http+unix"
    ConnectionCls = HTTPUnixConnection


class TestConnectionPool(object):
    """
    Tests in this suite should exercise the ConnectionPool functionality
    without actually making any network requests or connections.
    """

    @pytest.mark.parametrize(
        "a, b",
        [
            ("http://google.com/", "/"),
            ("http://google.com/", "http://google.com/"),
            ("http://google.com/", "http://google.com"),
            ("http://google.com/", "http://google.com/abra/cadabra"),
            ("http://google.com:42/", "http://google.com:42/abracadabra"),
            # Test comparison using default ports
            ("http://google.com:80/", "http://google.com/abracadabra"),
            ("http://google.com/", "http://google.com:80/abracadabra"),
            ("https://google.com:443/", "https://google.com/abracadabra"),
            ("https://google.com/", "https://google.com:443/abracadabra"),
            (
                "http://[2607:f8b0:4005:805::200e%25eth0]/",
                "http://[2607:f8b0:4005:805::200e%eth0]/",
            ),
            (
                "https://[2607:f8b0:4005:805::200e%25eth0]:443/",
                "https://[2607:f8b0:4005:805::200e%eth0]:443/",
            ),
            ("http://[::1]/", "http://[::1]"),
            (
                "http://[2001:558:fc00:200:f816:3eff:fef9:b954%lo]/",
                "http://[2001:558:fc00:200:f816:3eff:fef9:b954%25lo]",
            ),
        ],
    )
    def test_same_host(self, a, b):
        with connection_from_url(a) as c:
            assert c.is_same_host(b)

    @pytest.mark.parametrize(
        "a, b",
        [
            ("https://google.com/", "http://google.com/"),
            ("http://google.com/", "https://google.com/"),
            ("http://yahoo.com/", "http://google.com/"),
            ("http://google.com:42", "https://google.com/abracadabra"),
            ("http://google.com", "https://google.net/"),
            # Test comparison with default ports
            ("http://google.com:42", "http://google.com"),
            ("https://google.com:42", "https://google.com"),
            ("http://google.com:443", "http://google.com"),
            ("https://google.com:80", "https://google.com"),
            ("http://google.com:443", "https://google.com"),
            ("https://google.com:80", "http://google.com"),
            ("https://google.com:443", "http://google.com"),
            ("http://google.com:80", "https://google.com"),
            # Zone identifiers are unique connection end points and should
            # never be equivalent.
            ("http://[dead::beef]", "https://[dead::beef%en5]/"),
        ],
    )
    def test_not_same_host(self, a, b):
        with connection_from_url(a) as c:
            assert not c.is_same_host(b)

        with connection_from_url(b) as c:
            assert not c.is_same_host(a)

    @pytest.mark.parametrize(
        "a, b",
        [
            ("google.com", "/"),
            ("google.com", "http://google.com/"),
            ("google.com", "http://google.com"),
            ("google.com", "http://google.com/abra/cadabra"),
            # Test comparison using default ports
            ("google.com", "http://google.com:80/abracadabra"),
        ],
    )
    def test_same_host_no_port_http(self, a, b):
        # This test was introduced in #801 to deal with the fact that urllib3
        # never initializes ConnectionPool objects with port=None.
        with HTTPConnectionPool(a) as c:
            assert c.is_same_host(b)

    @pytest.mark.parametrize(
        "a, b",
        [
            ("google.com", "/"),
            ("google.com", "https://google.com/"),
            ("google.com", "https://google.com"),
            ("google.com", "https://google.com/abra/cadabra"),
            # Test comparison using default ports
            ("google.com", "https://google.com:443/abracadabra"),
        ],
    )
    def test_same_host_no_port_https(self, a, b):
        # This test was introduced in #801 to deal with the fact that urllib3
        # never initializes ConnectionPool objects with port=None.
        with HTTPSConnectionPool(a) as c:
            assert c.is_same_host(b)

    @pytest.mark.parametrize(
        "a, b",
        [
            ("google.com", "https://google.com/"),
            ("yahoo.com", "http://google.com/"),
            ("google.com", "https://google.net/"),
            ("google.com", "http://google.com./"),
        ],
    )
    def test_not_same_host_no_port_http(self, a, b):
        with HTTPConnectionPool(a) as c:
            assert not c.is_same_host(b)

        with HTTPConnectionPool(b) as c:
            assert not c.is_same_host(a)

    @pytest.mark.parametrize(
        "a, b",
        [
            ("google.com", "http://google.com/"),
            ("yahoo.com", "https://google.com/"),
            ("google.com", "https://google.net/"),
            ("google.com", "https://google.com./"),
        ],
    )
    def test_not_same_host_no_port_https(self, a, b):
        with HTTPSConnectionPool(a) as c:
            assert not c.is_same_host(b)

        with HTTPSConnectionPool(b) as c:
            assert not c.is_same_host(a)

    @pytest.mark.parametrize(
        "a, b",
        [
            ("%2Fvar%2Frun%2Fdocker.sock", "http+unix://%2Fvar%2Frun%2Fdocker.sock"),
            ("%2Fvar%2Frun%2Fdocker.sock", "http+unix://%2Fvar%2Frun%2Fdocker.sock/"),
            (
                "%2Fvar%2Frun%2Fdocker.sock",
                "http+unix://%2Fvar%2Frun%2Fdocker.sock/abracadabra",
            ),
            ("%2Ftmp%2FTEST.sock", "http+unix://%2Ftmp%2FTEST.sock"),
            ("%2Ftmp%2FTEST.sock", "http+unix://%2Ftmp%2FTEST.sock/"),
            ("%2Ftmp%2FTEST.sock", "http+unix://%2Ftmp%2FTEST.sock/abracadabra"),
        ],
    )
    def test_same_host_custom_protocol(self, a, b):
        with HTTPUnixConnectionPool(a) as c:
            assert c.is_same_host(b)

    @pytest.mark.parametrize(
        "a, b",
        [
            ("%2Ftmp%2Ftest.sock", "http+unix://%2Ftmp%2FTEST.sock"),
            ("%2Ftmp%2Ftest.sock", "http+unix://%2Ftmp%2FTEST.sock/"),
            ("%2Ftmp%2Ftest.sock", "http+unix://%2Ftmp%2FTEST.sock/abracadabra"),
            ("%2Fvar%2Frun%2Fdocker.sock", "http+unix://%2Ftmp%2FTEST.sock"),
        ],
    )
    def test_not_same_host_custom_protocol(self, a, b):
        with HTTPUnixConnectionPool(a) as c:
            assert not c.is_same_host(b)

    def test_max_connections(self):
        with HTTPConnectionPool(host="localhost", maxsize=1, block=True) as pool:
            pool._get_conn(timeout=SHORT_TIMEOUT)

            with pytest.raises(EmptyPoolError):
                pool._get_conn(timeout=SHORT_TIMEOUT)

            with pytest.raises(EmptyPoolError):
                pool.request("GET", "/", pool_timeout=SHORT_TIMEOUT)

            assert pool.num_connections == 1

    def test_pool_edgecases(self, caplog):
        with HTTPConnectionPool(host="localhost", maxsize=1, block=False) as pool:
            conn1 = pool._get_conn()
            conn2 = pool._get_conn()  # New because block=False

            pool._put_conn(conn1)
            pool._put_conn(conn2)  # Should be discarded

            assert conn1 == pool._get_conn()
            assert conn2 != pool._get_conn()

            assert pool.num_connections == 3
            assert "Connection pool is full, discarding connection" in caplog.text
            assert "Connection pool size: 1" in caplog.text

    def test_exception_str(self):
        assert (
            str(EmptyPoolError(HTTPConnectionPool(host="localhost"), "Test."))
            == "HTTPConnectionPool(host='localhost', port=None): Test."
        )

    def test_retry_exception_str(self):
        assert (
            str(MaxRetryError(HTTPConnectionPool(host="localhost"), "Test.", None))
            == "HTTPConnectionPool(host='localhost', port=None): "
            "Max retries exceeded with url: Test. (Caused by None)"
        )

        err = SocketError("Test")

        # using err.__class__ here, as socket.error is an alias for OSError
        # since Py3.3 and gets printed as this
        assert (
            str(MaxRetryError(HTTPConnectionPool(host="localhost"), "Test.", err))
            == "HTTPConnectionPool(host='localhost', port=None): "
            "Max retries exceeded with url: Test. "
            "(Caused by %r)" % err
        )

    def test_pool_size(self):
        POOL_SIZE = 1
        with HTTPConnectionPool(
            host="localhost", maxsize=POOL_SIZE, block=True
        ) as pool:

            def _raise(ex):
                raise ex()

            def _test(exception, expect, reason=None):
                pool._make_request = lambda *args, **kwargs: _raise(exception)
                with pytest.raises(expect) as excinfo:
                    pool.request("GET", "/")
                if reason is not None:
                    assert isinstance(excinfo.value.reason, reason)
                assert pool.pool.qsize() == POOL_SIZE

            # Make sure that all of the exceptions return the connection
            # to the pool
            _test(BaseSSLError, MaxRetryError, SSLError)
            _test(CertificateError, MaxRetryError, SSLError)

            # The pool should never be empty, and with these two exceptions
            # being raised, a retry will be triggered, but that retry will
            # fail, eventually raising MaxRetryError, not EmptyPoolError
            # See: https://github.com/urllib3/urllib3/issues/76
            pool._make_request = lambda *args, **kwargs: _raise(HTTPException)
            with pytest.raises(MaxRetryError):
                pool.request("GET", "/", retries=1, pool_timeout=SHORT_TIMEOUT)
            assert pool.pool.qsize() == POOL_SIZE

    def test_empty_does_not_put_conn(self):
        """Do not put None back in the pool if the pool was empty"""

        with HTTPConnectionPool(host="localhost", maxsize=1, block=True) as pool:
            pool._get_conn = Mock(side_effect=EmptyPoolError(pool, "Pool is empty"))
            pool._put_conn = Mock(side_effect=AssertionError("Unexpected _put_conn"))
            with pytest.raises(EmptyPoolError):
                pool.request("GET", "/")

    def test_assert_same_host(self):
        with connection_from_url("http://google.com:80") as c:
            with pytest.raises(HostChangedError):
                c.request("GET", "http://yahoo.com:80", assert_same_host=True)

    def test_pool_close(self):
        pool = connection_from_url("http://google.com:80")

        # Populate with some connections
        conn1 = pool._get_conn()
        conn2 = pool._get_conn()
        conn3 = pool._get_conn()
        pool._put_conn(conn1)
        pool._put_conn(conn2)

        old_pool_queue = pool.pool

        pool.close()
        assert pool.pool is None

        with pytest.raises(ClosedPoolError):
            pool._get_conn()

        pool._put_conn(conn3)

        with pytest.raises(ClosedPoolError):
            pool._get_conn()

        with pytest.raises(Empty):
            old_pool_queue.get(block=False)

    def test_pool_close_twice(self):
        pool = connection_from_url("http://google.com:80")

        # Populate with some connections
        conn1 = pool._get_conn()
        conn2 = pool._get_conn()
        pool._put_conn(conn1)
        pool._put_conn(conn2)

        pool.close()
        assert pool.pool is None

        try:
            pool.close()
        except AttributeError:
            pytest.fail("Pool of the ConnectionPool is None and has no attribute get.")

    def test_pool_timeouts(self):
        with HTTPConnectionPool(host="localhost") as pool:
            conn = pool._new_conn()
            assert conn.__class__ == HTTPConnection
            assert pool.timeout.__class__ == Timeout
            assert pool.timeout._read == Timeout.DEFAULT_TIMEOUT
            assert pool.timeout._connect == Timeout.DEFAULT_TIMEOUT
            assert pool.timeout.total is None

            pool = HTTPConnectionPool(host="localhost", timeout=SHORT_TIMEOUT)
            assert pool.timeout._read == SHORT_TIMEOUT
            assert pool.timeout._connect == SHORT_TIMEOUT
            assert pool.timeout.total is None

    def test_no_host(self):
        with pytest.raises(LocationValueError):
            HTTPConnectionPool(None)

    def test_contextmanager(self):
        with connection_from_url("http://google.com:80") as pool:
            # Populate with some connections
            conn1 = pool._get_conn()
            conn2 = pool._get_conn()
            conn3 = pool._get_conn()
            pool._put_conn(conn1)
            pool._put_conn(conn2)

            old_pool_queue = pool.pool

        assert pool.pool is None
        with pytest.raises(ClosedPoolError):
            pool._get_conn()

        pool._put_conn(conn3)
        with pytest.raises(ClosedPoolError):
            pool._get_conn()
        with pytest.raises(Empty):
            old_pool_queue.get(block=False)

    def test_absolute_url(self):
        with connection_from_url("http://google.com:80") as c:
            assert "http://google.com:80/path?query=foo" == c._absolute_url(
                "path?query=foo"
            )

    def test_ca_certs_default_cert_required(self):
        with connection_from_url("https://google.com:80", ca_certs=DEFAULT_CA) as pool:
            conn = pool._get_conn()
            assert conn.cert_reqs == ssl.CERT_REQUIRED

    def test_cleanup_on_extreme_connection_error(self):
        """
        This test validates that we clean up properly even on exceptions that
        we'd not otherwise catch, i.e. those that inherit from BaseException
        like KeyboardInterrupt or gevent.Timeout. See #805 for more details.
        """

        class RealBad(BaseException):
            pass

        def kaboom(*args, **kwargs):
            raise RealBad()

        with connection_from_url("http://localhost:80") as c:
            c._make_request = kaboom

            initial_pool_size = c.pool.qsize()

            try:
                # We need to release_conn this way or we'd put it away
                # regardless.
                c.urlopen("GET", "/", release_conn=False)
            except RealBad:
                pass

            new_pool_size = c.pool.qsize()
            assert initial_pool_size == new_pool_size

    def test_release_conn_param_is_respected_after_http_error_retry(self):
        """For successful ```urlopen(release_conn=False)```,
        the connection isn't released, even after a retry.

        This is a regression test for issue #651 [1], where the connection
        would be released if the initial request failed, even if a retry
        succeeded.

        [1] <https://github.com/urllib3/urllib3/issues/651>
        """

        class _raise_once_make_request_function(object):
            """Callable that can mimic `_make_request()`.

            Raises the given exception on its first call, but returns a
            successful response on subsequent calls.
            """

            def __init__(self, ex):
                super(_raise_once_make_request_function, self).__init__()
                self._ex = ex

            def __call__(self, *args, **kwargs):
                if self._ex:
                    ex, self._ex = self._ex, None
                    raise ex()
                response = httplib.HTTPResponse(MockSock)
                response.fp = MockChunkedEncodingResponse([b"f", b"o", b"o"])
                response.headers = response.msg = HTTPHeaderDict()
                return response

        def _test(exception):
            with HTTPConnectionPool(host="localhost", maxsize=1, block=True) as pool:
                # Verify that the request succeeds after two attempts, and that the
                # connection is left on the response object, instead of being
                # released back into the pool.
                pool._make_request = _raise_once_make_request_function(exception)
                response = pool.urlopen(
                    "GET",
                    "/",
                    retries=1,
                    release_conn=False,
                    preload_content=False,
                    chunked=True,
                )
                assert pool.pool.qsize() == 0
                assert pool.num_connections == 2
                assert response.connection is not None

                response.release_conn()
                assert pool.pool.qsize() == 1
                assert response.connection is None

        # Run the test case for all the retriable exceptions.
        _test(TimeoutError)
        _test(HTTPException)
        _test(SocketError)
        _test(ProtocolError)

    def test_custom_http_response_class(self):
        class CustomHTTPResponse(HTTPResponse):
            pass

        class CustomConnectionPool(HTTPConnectionPool):
            ResponseCls = CustomHTTPResponse

            def _make_request(self, *args, **kwargs):
                httplib_response = httplib.HTTPResponse(MockSock)
                httplib_response.fp = MockChunkedEncodingResponse([b"f", b"o", b"o"])
                httplib_response.headers = httplib_response.msg = HTTPHeaderDict()
                return httplib_response

        with CustomConnectionPool(host="localhost", maxsize=1, block=True) as pool:
            response = pool.request(
                "GET", "/", retries=False, chunked=True, preload_content=False
            )
            assert isinstance(response, CustomHTTPResponse)
