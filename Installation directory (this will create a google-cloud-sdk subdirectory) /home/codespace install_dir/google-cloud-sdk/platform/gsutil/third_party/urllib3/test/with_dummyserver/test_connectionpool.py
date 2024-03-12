# -*- coding: utf-8 -*-

import io
import json
import logging
import os
import platform
import socket
import sys
import time
import warnings
from test import LONG_TIMEOUT, SHORT_TIMEOUT, onlyPy2
from threading import Event

import mock
import pytest
import six

from dummyserver.server import HAS_IPV6_AND_DNS, NoIPv6Warning
from dummyserver.testcase import HTTPDummyServerTestCase, SocketDummyServerTestCase
from urllib3 import HTTPConnectionPool, encode_multipart_formdata
from urllib3._collections import HTTPHeaderDict
from urllib3.connection import _get_default_user_agent
from urllib3.exceptions import (
    ConnectTimeoutError,
    DecodeError,
    EmptyPoolError,
    MaxRetryError,
    NewConnectionError,
    ReadTimeoutError,
    UnrewindableBodyError,
)
from urllib3.packages.six import b, u
from urllib3.packages.six.moves.urllib.parse import urlencode
from urllib3.util import SKIP_HEADER, SKIPPABLE_HEADERS
from urllib3.util.retry import RequestHistory, Retry
from urllib3.util.timeout import Timeout

from .. import INVALID_SOURCE_ADDRESSES, TARPIT_HOST, VALID_SOURCE_ADDRESSES
from ..port_helpers import find_unused_port

pytestmark = pytest.mark.flaky

log = logging.getLogger("urllib3.connectionpool")
log.setLevel(logging.NOTSET)
log.addHandler(logging.StreamHandler(sys.stdout))


def wait_for_socket(ready_event):
    ready_event.wait()
    ready_event.clear()


class TestConnectionPoolTimeouts(SocketDummyServerTestCase):
    def test_timeout_float(self):
        block_event = Event()
        ready_event = self.start_basic_handler(block_send=block_event, num=2)

        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            wait_for_socket(ready_event)
            with pytest.raises(ReadTimeoutError):
                pool.request("GET", "/", timeout=SHORT_TIMEOUT)
            block_event.set()  # Release block

            # Shouldn't raise this time
            wait_for_socket(ready_event)
            block_event.set()  # Pre-release block
            pool.request("GET", "/", timeout=LONG_TIMEOUT)

    def test_conn_closed(self):
        block_event = Event()
        self.start_basic_handler(block_send=block_event, num=1)

        with HTTPConnectionPool(
            self.host, self.port, timeout=SHORT_TIMEOUT, retries=False
        ) as pool:
            conn = pool._get_conn()
            pool._put_conn(conn)
            try:
                with pytest.raises(ReadTimeoutError):
                    pool.urlopen("GET", "/")
                if conn.sock:
                    with pytest.raises(socket.error):
                        conn.sock.recv(1024)
            finally:
                pool._put_conn(conn)

            block_event.set()

    def test_timeout(self):
        # Requests should time out when expected
        block_event = Event()
        ready_event = self.start_basic_handler(block_send=block_event, num=3)

        # Pool-global timeout
        short_timeout = Timeout(read=SHORT_TIMEOUT)
        with HTTPConnectionPool(
            self.host, self.port, timeout=short_timeout, retries=False
        ) as pool:
            wait_for_socket(ready_event)
            block_event.clear()
            with pytest.raises(ReadTimeoutError):
                pool.request("GET", "/")
            block_event.set()  # Release request

        # Request-specific timeouts should raise errors
        with HTTPConnectionPool(
            self.host, self.port, timeout=short_timeout, retries=False
        ) as pool:
            wait_for_socket(ready_event)
            now = time.time()
            with pytest.raises(ReadTimeoutError):
                pool.request("GET", "/", timeout=LONG_TIMEOUT)
            delta = time.time() - now

            message = "timeout was pool-level SHORT_TIMEOUT rather than request-level LONG_TIMEOUT"
            assert delta >= LONG_TIMEOUT, message
            block_event.set()  # Release request

            # Timeout passed directly to request should raise a request timeout
            wait_for_socket(ready_event)
            with pytest.raises(ReadTimeoutError):
                pool.request("GET", "/", timeout=SHORT_TIMEOUT)
            block_event.set()  # Release request

    def test_connect_timeout(self):
        url = "/"
        host, port = TARPIT_HOST, 80
        timeout = Timeout(connect=SHORT_TIMEOUT)

        # Pool-global timeout
        with HTTPConnectionPool(host, port, timeout=timeout) as pool:
            conn = pool._get_conn()
            with pytest.raises(ConnectTimeoutError):
                pool._make_request(conn, "GET", url)

            # Retries
            retries = Retry(connect=0)
            with pytest.raises(MaxRetryError):
                pool.request("GET", url, retries=retries)

        # Request-specific connection timeouts
        big_timeout = Timeout(read=LONG_TIMEOUT, connect=LONG_TIMEOUT)
        with HTTPConnectionPool(host, port, timeout=big_timeout, retries=False) as pool:
            conn = pool._get_conn()
            with pytest.raises(ConnectTimeoutError):
                pool._make_request(conn, "GET", url, timeout=timeout)

            pool._put_conn(conn)
            with pytest.raises(ConnectTimeoutError):
                pool.request("GET", url, timeout=timeout)

    def test_total_applies_connect(self):
        host, port = TARPIT_HOST, 80

        timeout = Timeout(total=None, connect=SHORT_TIMEOUT)
        with HTTPConnectionPool(host, port, timeout=timeout) as pool:
            conn = pool._get_conn()
            try:
                with pytest.raises(ConnectTimeoutError):
                    pool._make_request(conn, "GET", "/")
            finally:
                conn.close()

        timeout = Timeout(connect=3, read=5, total=SHORT_TIMEOUT)
        with HTTPConnectionPool(host, port, timeout=timeout) as pool:
            conn = pool._get_conn()
            try:
                with pytest.raises(ConnectTimeoutError):
                    pool._make_request(conn, "GET", "/")
            finally:
                conn.close()

    def test_total_timeout(self):
        block_event = Event()
        ready_event = self.start_basic_handler(block_send=block_event, num=2)

        wait_for_socket(ready_event)
        # This will get the socket to raise an EAGAIN on the read
        timeout = Timeout(connect=3, read=SHORT_TIMEOUT)
        with HTTPConnectionPool(
            self.host, self.port, timeout=timeout, retries=False
        ) as pool:
            with pytest.raises(ReadTimeoutError):
                pool.request("GET", "/")

            block_event.set()
            wait_for_socket(ready_event)
            block_event.clear()

        # The connect should succeed and this should hit the read timeout
        timeout = Timeout(connect=3, read=5, total=SHORT_TIMEOUT)
        with HTTPConnectionPool(
            self.host, self.port, timeout=timeout, retries=False
        ) as pool:
            with pytest.raises(ReadTimeoutError):
                pool.request("GET", "/")

    def test_create_connection_timeout(self):
        self.start_basic_handler(block_send=Event(), num=0)  # needed for self.port

        timeout = Timeout(connect=SHORT_TIMEOUT, total=LONG_TIMEOUT)
        with HTTPConnectionPool(
            TARPIT_HOST, self.port, timeout=timeout, retries=False
        ) as pool:
            conn = pool._new_conn()
            with pytest.raises(ConnectTimeoutError):
                conn.connect()


class TestConnectionPool(HTTPDummyServerTestCase):
    def test_get(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("GET", "/specific_method", fields={"method": "GET"})
            assert r.status == 200, r.data

    def test_post_url(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("POST", "/specific_method", fields={"method": "POST"})
            assert r.status == 200, r.data

    def test_urlopen_put(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.urlopen("PUT", "/specific_method?method=PUT")
            assert r.status == 200, r.data

    def test_wrong_specific_method(self):
        # To make sure the dummy server is actually returning failed responses
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("GET", "/specific_method", fields={"method": "POST"})
            assert r.status == 400, r.data

        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("POST", "/specific_method", fields={"method": "GET"})
            assert r.status == 400, r.data

    def test_upload(self):
        data = "I'm in ur multipart form-data, hazing a cheezburgr"
        fields = {
            "upload_param": "filefield",
            "upload_filename": "lolcat.txt",
            "upload_size": len(data),
            "filefield": ("lolcat.txt", data),
        }

        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("POST", "/upload", fields=fields)
            assert r.status == 200, r.data

    def test_one_name_multiple_values(self):
        fields = [("foo", "a"), ("foo", "b")]

        with HTTPConnectionPool(self.host, self.port) as pool:
            # urlencode
            r = pool.request("GET", "/echo", fields=fields)
            assert r.data == b"foo=a&foo=b"

            # multipart
            r = pool.request("POST", "/echo", fields=fields)
            assert r.data.count(b'name="foo"') == 2

    def test_request_method_body(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            body = b"hi"
            r = pool.request("POST", "/echo", body=body)
            assert r.data == body

            fields = [("hi", "hello")]
            with pytest.raises(TypeError):
                pool.request("POST", "/echo", body=body, fields=fields)

    def test_unicode_upload(self):
        fieldname = u("myfile")
        filename = u("\xe2\x99\xa5.txt")
        data = u("\xe2\x99\xa5").encode("utf8")
        size = len(data)

        fields = {
            u("upload_param"): fieldname,
            u("upload_filename"): filename,
            u("upload_size"): size,
            fieldname: (filename, data),
        }
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("POST", "/upload", fields=fields)
            assert r.status == 200, r.data

    def test_nagle(self):
        """Test that connections have TCP_NODELAY turned on"""
        # This test needs to be here in order to be run. socket.create_connection actually tries
        # to connect to the host provided so we need a dummyserver to be running.
        with HTTPConnectionPool(self.host, self.port) as pool:
            conn = pool._get_conn()
            try:
                pool._make_request(conn, "GET", "/")
                tcp_nodelay_setting = conn.sock.getsockopt(
                    socket.IPPROTO_TCP, socket.TCP_NODELAY
                )
                assert tcp_nodelay_setting
            finally:
                conn.close()

    def test_socket_options(self):
        """Test that connections accept socket options."""
        # This test needs to be here in order to be run. socket.create_connection actually tries to
        # connect to the host provided so we need a dummyserver to be running.
        with HTTPConnectionPool(
            self.host,
            self.port,
            socket_options=[(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)],
        ) as pool:
            s = pool._new_conn()._new_conn()  # Get the socket
            try:
                using_keepalive = (
                    s.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE) > 0
                )
                assert using_keepalive
            finally:
                s.close()

    def test_disable_default_socket_options(self):
        """Test that passing None disables all socket options."""
        # This test needs to be here in order to be run. socket.create_connection actually tries
        # to connect to the host provided so we need a dummyserver to be running.
        with HTTPConnectionPool(self.host, self.port, socket_options=None) as pool:
            s = pool._new_conn()._new_conn()
            try:
                using_nagle = s.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY) == 0
                assert using_nagle
            finally:
                s.close()

    def test_defaults_are_applied(self):
        """Test that modifying the default socket options works."""
        # This test needs to be here in order to be run. socket.create_connection actually tries
        # to connect to the host provided so we need a dummyserver to be running.
        with HTTPConnectionPool(self.host, self.port) as pool:
            # Get the HTTPConnection instance
            conn = pool._new_conn()
            try:
                # Update the default socket options
                conn.default_socket_options += [
                    (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                ]
                s = conn._new_conn()
                nagle_disabled = (
                    s.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY) > 0
                )
                using_keepalive = (
                    s.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE) > 0
                )
                assert nagle_disabled
                assert using_keepalive
            finally:
                conn.close()
                s.close()

    def test_connection_error_retries(self):
        """ECONNREFUSED error should raise a connection error, with retries"""
        port = find_unused_port()
        with HTTPConnectionPool(self.host, port) as pool:
            with pytest.raises(MaxRetryError) as e:
                pool.request("GET", "/", retries=Retry(connect=3))
            assert type(e.value.reason) == NewConnectionError

    def test_timeout_success(self):
        timeout = Timeout(connect=3, read=5, total=None)
        with HTTPConnectionPool(self.host, self.port, timeout=timeout) as pool:
            pool.request("GET", "/")
            # This should not raise a "Timeout already started" error
            pool.request("GET", "/")

        with HTTPConnectionPool(self.host, self.port, timeout=timeout) as pool:
            # This should also not raise a "Timeout already started" error
            pool.request("GET", "/")

        timeout = Timeout(total=None)
        with HTTPConnectionPool(self.host, self.port, timeout=timeout) as pool:
            pool.request("GET", "/")

    def test_tunnel(self):
        # note the actual httplib.py has no tests for this functionality
        timeout = Timeout(total=None)
        with HTTPConnectionPool(self.host, self.port, timeout=timeout) as pool:
            conn = pool._get_conn()
            try:
                conn.set_tunnel(self.host, self.port)
                conn._tunnel = mock.Mock(return_value=None)
                pool._make_request(conn, "GET", "/")
                conn._tunnel.assert_called_once_with()
            finally:
                conn.close()

        # test that it's not called when tunnel is not set
        timeout = Timeout(total=None)
        with HTTPConnectionPool(self.host, self.port, timeout=timeout) as pool:
            conn = pool._get_conn()
            try:
                conn._tunnel = mock.Mock(return_value=None)
                pool._make_request(conn, "GET", "/")
                assert not conn._tunnel.called
            finally:
                conn.close()

    def test_redirect(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("GET", "/redirect", fields={"target": "/"}, redirect=False)
            assert r.status == 303

            r = pool.request("GET", "/redirect", fields={"target": "/"})
            assert r.status == 200
            assert r.data == b"Dummy server!"

    def test_bad_connect(self):
        with HTTPConnectionPool("badhost.invalid", self.port) as pool:
            with pytest.raises(MaxRetryError) as e:
                pool.request("GET", "/", retries=5)
            assert type(e.value.reason) == NewConnectionError

    def test_keepalive(self):
        with HTTPConnectionPool(self.host, self.port, block=True, maxsize=1) as pool:
            r = pool.request("GET", "/keepalive?close=0")
            r = pool.request("GET", "/keepalive?close=0")

            assert r.status == 200
            assert pool.num_connections == 1
            assert pool.num_requests == 2

    def test_keepalive_close(self):
        with HTTPConnectionPool(
            self.host, self.port, block=True, maxsize=1, timeout=2
        ) as pool:
            r = pool.request(
                "GET", "/keepalive?close=1", retries=0, headers={"Connection": "close"}
            )

            assert pool.num_connections == 1

            # The dummyserver will have responded with Connection:close,
            # and httplib will properly cleanup the socket.

            # We grab the HTTPConnection object straight from the Queue,
            # because _get_conn() is where the check & reset occurs
            # pylint: disable-msg=W0212
            conn = pool.pool.get()
            assert conn.sock is None
            pool._put_conn(conn)

            # Now with keep-alive
            r = pool.request(
                "GET",
                "/keepalive?close=0",
                retries=0,
                headers={"Connection": "keep-alive"},
            )

            # The dummyserver responded with Connection:keep-alive, the connection
            # persists.
            conn = pool.pool.get()
            assert conn.sock is not None
            pool._put_conn(conn)

            # Another request asking the server to close the connection. This one
            # should get cleaned up for the next request.
            r = pool.request(
                "GET", "/keepalive?close=1", retries=0, headers={"Connection": "close"}
            )

            assert r.status == 200

            conn = pool.pool.get()
            assert conn.sock is None
            pool._put_conn(conn)

            # Next request
            r = pool.request("GET", "/keepalive?close=0")

    def test_post_with_urlencode(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            data = {"banana": "hammock", "lol": "cat"}
            r = pool.request("POST", "/echo", fields=data, encode_multipart=False)
            assert r.data.decode("utf-8") == urlencode(data)

    def test_post_with_multipart(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            data = {"banana": "hammock", "lol": "cat"}
            r = pool.request("POST", "/echo", fields=data, encode_multipart=True)
            body = r.data.split(b"\r\n")

            encoded_data = encode_multipart_formdata(data)[0]
            expected_body = encoded_data.split(b"\r\n")

            # TODO: Get rid of extra parsing stuff when you can specify
            # a custom boundary to encode_multipart_formdata
            """
            We need to loop the return lines because a timestamp is attached
            from within encode_multipart_formdata. When the server echos back
            the data, it has the timestamp from when the data was encoded, which
            is not equivalent to when we run encode_multipart_formdata on
            the data again.
            """
            for i, line in enumerate(body):
                if line.startswith(b"--"):
                    continue

                assert body[i] == expected_body[i]

    def test_post_with_multipart__iter__(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            data = {"hello": "world"}
            r = pool.request(
                "POST",
                "/echo",
                fields=data,
                preload_content=False,
                multipart_boundary="boundary",
                encode_multipart=True,
            )

            chunks = [chunk for chunk in r]
            assert chunks == [
                b"--boundary\r\n",
                b'Content-Disposition: form-data; name="hello"\r\n',
                b"\r\n",
                b"world\r\n",
                b"--boundary--\r\n",
            ]

    def test_check_gzip(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request(
                "GET", "/encodingrequest", headers={"accept-encoding": "gzip"}
            )
            assert r.headers.get("content-encoding") == "gzip"
            assert r.data == b"hello, world!"

    def test_check_deflate(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request(
                "GET", "/encodingrequest", headers={"accept-encoding": "deflate"}
            )
            assert r.headers.get("content-encoding") == "deflate"
            assert r.data == b"hello, world!"

    def test_bad_decode(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            with pytest.raises(DecodeError):
                pool.request(
                    "GET",
                    "/encodingrequest",
                    headers={"accept-encoding": "garbage-deflate"},
                )

            with pytest.raises(DecodeError):
                pool.request(
                    "GET",
                    "/encodingrequest",
                    headers={"accept-encoding": "garbage-gzip"},
                )

    def test_connection_count(self):
        with HTTPConnectionPool(self.host, self.port, maxsize=1) as pool:
            pool.request("GET", "/")
            pool.request("GET", "/")
            pool.request("GET", "/")

            assert pool.num_connections == 1
            assert pool.num_requests == 3

    def test_connection_count_bigpool(self):
        with HTTPConnectionPool(self.host, self.port, maxsize=16) as http_pool:
            http_pool.request("GET", "/")
            http_pool.request("GET", "/")
            http_pool.request("GET", "/")

            assert http_pool.num_connections == 1
            assert http_pool.num_requests == 3

    def test_partial_response(self):
        with HTTPConnectionPool(self.host, self.port, maxsize=1) as pool:
            req_data = {"lol": "cat"}
            resp_data = urlencode(req_data).encode("utf-8")

            r = pool.request("GET", "/echo", fields=req_data, preload_content=False)

            assert r.read(5) == resp_data[:5]
            assert r.read() == resp_data[5:]

    def test_lazy_load_twice(self):
        # This test is sad and confusing. Need to figure out what's
        # going on with partial reads and socket reuse.

        with HTTPConnectionPool(
            self.host, self.port, block=True, maxsize=1, timeout=2
        ) as pool:
            payload_size = 1024 * 2
            first_chunk = 512

            boundary = "foo"

            req_data = {"count": "a" * payload_size}
            resp_data = encode_multipart_formdata(req_data, boundary=boundary)[0]

            req2_data = {"count": "b" * payload_size}
            resp2_data = encode_multipart_formdata(req2_data, boundary=boundary)[0]

            r1 = pool.request(
                "POST",
                "/echo",
                fields=req_data,
                multipart_boundary=boundary,
                preload_content=False,
            )

            assert r1.read(first_chunk) == resp_data[:first_chunk]

            try:
                r2 = pool.request(
                    "POST",
                    "/echo",
                    fields=req2_data,
                    multipart_boundary=boundary,
                    preload_content=False,
                    pool_timeout=0.001,
                )

                # This branch should generally bail here, but maybe someday it will
                # work? Perhaps by some sort of magic. Consider it a TODO.

                assert r2.read(first_chunk) == resp2_data[:first_chunk]

                assert r1.read() == resp_data[first_chunk:]
                assert r2.read() == resp2_data[first_chunk:]
                assert pool.num_requests == 2

            except EmptyPoolError:
                assert r1.read() == resp_data[first_chunk:]
                assert pool.num_requests == 1

            assert pool.num_connections == 1

    def test_for_double_release(self):
        MAXSIZE = 5

        # Check default state
        with HTTPConnectionPool(self.host, self.port, maxsize=MAXSIZE) as pool:
            assert pool.num_connections == 0
            assert pool.pool.qsize() == MAXSIZE

            # Make an empty slot for testing
            pool.pool.get()
            assert pool.pool.qsize() == MAXSIZE - 1

            # Check state after simple request
            pool.urlopen("GET", "/")
            assert pool.pool.qsize() == MAXSIZE - 1

            # Check state without release
            pool.urlopen("GET", "/", preload_content=False)
            assert pool.pool.qsize() == MAXSIZE - 2

            pool.urlopen("GET", "/")
            assert pool.pool.qsize() == MAXSIZE - 2

            # Check state after read
            pool.urlopen("GET", "/").data
            assert pool.pool.qsize() == MAXSIZE - 2

            pool.urlopen("GET", "/")
            assert pool.pool.qsize() == MAXSIZE - 2

    def test_release_conn_parameter(self):
        MAXSIZE = 5
        with HTTPConnectionPool(self.host, self.port, maxsize=MAXSIZE) as pool:
            assert pool.pool.qsize() == MAXSIZE

            # Make request without releasing connection
            pool.request("GET", "/", release_conn=False, preload_content=False)
            assert pool.pool.qsize() == MAXSIZE - 1

    def test_dns_error(self):
        with HTTPConnectionPool(
            "thishostdoesnotexist.invalid", self.port, timeout=0.001
        ) as pool:
            with pytest.raises(MaxRetryError):
                pool.request("GET", "/test", retries=2)

    @pytest.mark.parametrize("char", [" ", "\r", "\n", "\x00"])
    def test_invalid_method_not_allowed(self, char):
        with pytest.raises(ValueError):
            with HTTPConnectionPool(self.host, self.port) as pool:
                pool.request("GET" + char, "/")

    def test_percent_encode_invalid_target_chars(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("GET", "/echo_params?q=\r&k=\n \n")
            assert r.data == b"[('k', '\\n \\n'), ('q', '\\r')]"

    @pytest.mark.skipif(
        six.PY2
        and platform.system() == "Darwin"
        and os.environ.get("GITHUB_ACTIONS") == "true",
        reason="fails on macOS 2.7 in GitHub Actions for an unknown reason",
    )
    def test_source_address(self):
        for addr, is_ipv6 in VALID_SOURCE_ADDRESSES:
            if is_ipv6 and not HAS_IPV6_AND_DNS:
                warnings.warn("No IPv6 support: skipping.", NoIPv6Warning)
                continue
            with HTTPConnectionPool(
                self.host, self.port, source_address=addr, retries=False
            ) as pool:
                r = pool.request("GET", "/source_address")
                assert r.data == b(addr[0])

    @pytest.mark.skipif(
        six.PY2
        and platform.system() == "Darwin"
        and os.environ.get("GITHUB_ACTIONS") == "true",
        reason="fails on macOS 2.7 in GitHub Actions for an unknown reason",
    )
    def test_source_address_error(self):
        for addr in INVALID_SOURCE_ADDRESSES:
            with HTTPConnectionPool(
                self.host, self.port, source_address=addr, retries=False
            ) as pool:
                with pytest.raises(NewConnectionError):
                    pool.request("GET", "/source_address?{0}".format(addr))

    def test_stream_keepalive(self):
        x = 2

        with HTTPConnectionPool(self.host, self.port) as pool:
            for _ in range(x):
                response = pool.request(
                    "GET",
                    "/chunked",
                    headers={"Connection": "keep-alive"},
                    preload_content=False,
                    retries=False,
                )
                for chunk in response.stream():
                    assert chunk == b"123"

            assert pool.num_connections == 1
            assert pool.num_requests == x

    def test_read_chunked_short_circuit(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            response = pool.request("GET", "/chunked", preload_content=False)
            response.read()
            with pytest.raises(StopIteration):
                next(response.read_chunked())

    def test_read_chunked_on_closed_response(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            response = pool.request("GET", "/chunked", preload_content=False)
            response.close()
            with pytest.raises(StopIteration):
                next(response.read_chunked())

    def test_chunked_gzip(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            response = pool.request(
                "GET", "/chunked_gzip", preload_content=False, decode_content=True
            )

            assert b"123" * 4 == response.read()

    def test_cleanup_on_connection_error(self):
        """
        Test that connections are recycled to the pool on
        connection errors where no http response is received.
        """
        poolsize = 3
        with HTTPConnectionPool(
            self.host, self.port, maxsize=poolsize, block=True
        ) as http:
            assert http.pool.qsize() == poolsize

            # force a connection error by supplying a non-existent
            # url. We won't get a response for this  and so the
            # conn won't be implicitly returned to the pool.
            with pytest.raises(MaxRetryError):
                http.request(
                    "GET",
                    "/redirect",
                    fields={"target": "/"},
                    release_conn=False,
                    retries=0,
                )

            r = http.request(
                "GET",
                "/redirect",
                fields={"target": "/"},
                release_conn=False,
                retries=1,
            )
            r.release_conn()

            # the pool should still contain poolsize elements
            assert http.pool.qsize() == http.pool.maxsize

    def test_mixed_case_hostname(self):
        with HTTPConnectionPool("LoCaLhOsT", self.port) as pool:
            response = pool.request("GET", "http://LoCaLhOsT:%d/" % self.port)
            assert response.status == 200

    def test_preserves_path_dot_segments(self):
        """ConnectionPool preserves dot segments in the URI"""
        with HTTPConnectionPool(self.host, self.port) as pool:
            response = pool.request("GET", "/echo_uri/seg0/../seg2")
            assert response.data == b"/echo_uri/seg0/../seg2"

    def test_default_user_agent_header(self):
        """ConnectionPool has a default user agent"""
        default_ua = _get_default_user_agent()
        custom_ua = "I'm not a web scraper, what are you talking about?"
        custom_ua2 = "Yet Another User Agent"
        with HTTPConnectionPool(self.host, self.port) as pool:
            # Use default user agent if no user agent was specified.
            r = pool.request("GET", "/headers")
            request_headers = json.loads(r.data.decode("utf8"))
            assert request_headers.get("User-Agent") == _get_default_user_agent()

            # Prefer the request user agent over the default.
            headers = {"UsEr-AGENt": custom_ua}
            r = pool.request("GET", "/headers", headers=headers)
            request_headers = json.loads(r.data.decode("utf8"))
            assert request_headers.get("User-Agent") == custom_ua

            # Do not modify pool headers when using the default user agent.
            pool_headers = {"foo": "bar"}
            pool.headers = pool_headers
            r = pool.request("GET", "/headers")
            request_headers = json.loads(r.data.decode("utf8"))
            assert request_headers.get("User-Agent") == default_ua
            assert "User-Agent" not in pool_headers

            pool.headers.update({"User-Agent": custom_ua2})
            r = pool.request("GET", "/headers")
            request_headers = json.loads(r.data.decode("utf8"))
            assert request_headers.get("User-Agent") == custom_ua2

    @pytest.mark.parametrize(
        "headers",
        [
            None,
            {},
            {"User-Agent": "key"},
            {"user-agent": "key"},
            {b"uSeR-AgEnT": b"key"},
            {b"user-agent": "key"},
        ],
    )
    @pytest.mark.parametrize("chunked", [True, False])
    def test_user_agent_header_not_sent_twice(self, headers, chunked):
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("GET", "/headers", headers=headers, chunked=chunked)
            request_headers = json.loads(r.data.decode("utf8"))

            if not headers:
                assert request_headers["User-Agent"].startswith("python-urllib3/")
                assert "key" not in request_headers["User-Agent"]
            else:
                assert request_headers["User-Agent"] == "key"

    def test_no_user_agent_header(self):
        """ConnectionPool can suppress sending a user agent header"""
        custom_ua = "I'm not a web scraper, what are you talking about?"
        with HTTPConnectionPool(self.host, self.port) as pool:
            # Suppress user agent in the request headers.
            no_ua_headers = {"User-Agent": SKIP_HEADER}
            r = pool.request("GET", "/headers", headers=no_ua_headers)
            request_headers = json.loads(r.data.decode("utf8"))
            assert "User-Agent" not in request_headers
            assert no_ua_headers["User-Agent"] == SKIP_HEADER

            # Suppress user agent in the pool headers.
            pool.headers = no_ua_headers
            r = pool.request("GET", "/headers")
            request_headers = json.loads(r.data.decode("utf8"))
            assert "User-Agent" not in request_headers
            assert no_ua_headers["User-Agent"] == SKIP_HEADER

            # Request headers override pool headers.
            pool_headers = {"User-Agent": custom_ua}
            pool.headers = pool_headers
            r = pool.request("GET", "/headers", headers=no_ua_headers)
            request_headers = json.loads(r.data.decode("utf8"))
            assert "User-Agent" not in request_headers
            assert no_ua_headers["User-Agent"] == SKIP_HEADER
            assert pool_headers.get("User-Agent") == custom_ua

    @pytest.mark.parametrize(
        "accept_encoding",
        [
            "Accept-Encoding",
            "accept-encoding",
            b"Accept-Encoding",
            b"accept-encoding",
            None,
        ],
    )
    @pytest.mark.parametrize("host", ["Host", "host", b"Host", b"host", None])
    @pytest.mark.parametrize(
        "user_agent", ["User-Agent", "user-agent", b"User-Agent", b"user-agent", None]
    )
    @pytest.mark.parametrize("chunked", [True, False])
    def test_skip_header(self, accept_encoding, host, user_agent, chunked):
        headers = {}

        if accept_encoding is not None:
            headers[accept_encoding] = SKIP_HEADER
        if host is not None:
            headers[host] = SKIP_HEADER
        if user_agent is not None:
            headers[user_agent] = SKIP_HEADER

        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("GET", "/headers", headers=headers, chunked=chunked)
        request_headers = json.loads(r.data.decode("utf8"))

        if accept_encoding is None:
            assert "Accept-Encoding" in request_headers
        else:
            assert accept_encoding not in request_headers
        if host is None:
            assert "Host" in request_headers
        else:
            assert host not in request_headers
        if user_agent is None:
            assert "User-Agent" in request_headers
        else:
            assert user_agent not in request_headers

    @pytest.mark.parametrize("header", ["Content-Length", "content-length"])
    @pytest.mark.parametrize("chunked", [True, False])
    def test_skip_header_non_supported(self, header, chunked):
        with HTTPConnectionPool(self.host, self.port) as pool:
            with pytest.raises(ValueError) as e:
                pool.request(
                    "GET", "/headers", headers={header: SKIP_HEADER}, chunked=chunked
                )
            assert (
                str(e.value)
                == "urllib3.util.SKIP_HEADER only supports 'Accept-Encoding', 'Host', 'User-Agent'"
            )

            # Ensure that the error message stays up to date with 'SKIP_HEADER_SUPPORTED_HEADERS'
            assert all(
                ("'" + header.title() + "'") in str(e.value)
                for header in SKIPPABLE_HEADERS
            )

    @pytest.mark.parametrize("chunked", [True, False])
    @pytest.mark.parametrize("pool_request", [True, False])
    @pytest.mark.parametrize("header_type", [dict, HTTPHeaderDict])
    def test_headers_not_modified_by_request(self, chunked, pool_request, header_type):
        # Test that the .request*() methods of ConnectionPool and HTTPConnection
        # don't modify the given 'headers' structure, instead they should
        # make their own internal copies at request time.
        headers = header_type()
        headers["key"] = "val"

        with HTTPConnectionPool(self.host, self.port) as pool:
            pool.headers = headers
            if pool_request:
                pool.request("GET", "/headers", chunked=chunked)
            else:
                conn = pool._get_conn()
                if chunked:
                    conn.request_chunked("GET", "/headers")
                else:
                    conn.request("GET", "/headers")

            assert pool.headers == {"key": "val"}
            assert isinstance(pool.headers, header_type)

        with HTTPConnectionPool(self.host, self.port) as pool:
            if pool_request:
                pool.request("GET", "/headers", headers=headers, chunked=chunked)
            else:
                conn = pool._get_conn()
                if chunked:
                    conn.request_chunked("GET", "/headers", headers=headers)
                else:
                    conn.request("GET", "/headers", headers=headers)

            assert headers == {"key": "val"}

    def test_bytes_header(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            headers = {"User-Agent": b"test header"}
            r = pool.request("GET", "/headers", headers=headers)
            request_headers = json.loads(r.data.decode("utf8"))
            assert "User-Agent" in request_headers
            assert request_headers["User-Agent"] == "test header"

    @pytest.mark.parametrize(
        "user_agent", [u"Schönefeld/1.18.0", u"Schönefeld/1.18.0".encode("iso-8859-1")]
    )
    def test_user_agent_non_ascii_user_agent(self, user_agent):
        if six.PY2 and not isinstance(user_agent, str):
            pytest.skip(
                "Python 2 raises UnicodeEncodeError when passed a unicode header"
            )

        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            r = pool.urlopen(
                "GET",
                "/headers",
                headers={"User-Agent": user_agent},
            )
            request_headers = json.loads(r.data.decode("utf8"))
            assert "User-Agent" in request_headers
            assert request_headers["User-Agent"] == u"Schönefeld/1.18.0"

    @onlyPy2
    def test_user_agent_non_ascii_fails_on_python_2(self):
        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            with pytest.raises(UnicodeEncodeError) as e:
                pool.urlopen(
                    "GET",
                    "/headers",
                    headers={"User-Agent": u"Schönefeld/1.18.0"},
                )
            assert str(e.value) == (
                "'ascii' codec can't encode character u'\\xf6' in "
                "position 3: ordinal not in range(128)"
            )


class TestRetry(HTTPDummyServerTestCase):
    def test_max_retry(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            with pytest.raises(MaxRetryError):
                pool.request("GET", "/redirect", fields={"target": "/"}, retries=0)

    def test_disabled_retry(self):
        """Disabled retries should disable redirect handling."""
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("GET", "/redirect", fields={"target": "/"}, retries=False)
            assert r.status == 303

            r = pool.request(
                "GET",
                "/redirect",
                fields={"target": "/"},
                retries=Retry(redirect=False),
            )
            assert r.status == 303

        with HTTPConnectionPool(
            "thishostdoesnotexist.invalid", self.port, timeout=0.001
        ) as pool:
            with pytest.raises(NewConnectionError):
                pool.request("GET", "/test", retries=False)

    def test_read_retries(self):
        """Should retry for status codes in the whitelist"""
        with HTTPConnectionPool(self.host, self.port) as pool:
            retry = Retry(read=1, status_forcelist=[418])
            resp = pool.request(
                "GET",
                "/successful_retry",
                headers={"test-name": "test_read_retries"},
                retries=retry,
            )
            assert resp.status == 200

    def test_read_total_retries(self):
        """HTTP response w/ status code in the whitelist should be retried"""
        with HTTPConnectionPool(self.host, self.port) as pool:
            headers = {"test-name": "test_read_total_retries"}
            retry = Retry(total=1, status_forcelist=[418])
            resp = pool.request(
                "GET", "/successful_retry", headers=headers, retries=retry
            )
            assert resp.status == 200

    def test_retries_wrong_whitelist(self):
        """HTTP response w/ status code not in whitelist shouldn't be retried"""
        with HTTPConnectionPool(self.host, self.port) as pool:
            retry = Retry(total=1, status_forcelist=[202])
            resp = pool.request(
                "GET",
                "/successful_retry",
                headers={"test-name": "test_wrong_whitelist"},
                retries=retry,
            )
            assert resp.status == 418

    def test_default_method_whitelist_retried(self):
        """urllib3 should retry methods in the default method whitelist"""
        with HTTPConnectionPool(self.host, self.port) as pool:
            retry = Retry(total=1, status_forcelist=[418])
            resp = pool.request(
                "OPTIONS",
                "/successful_retry",
                headers={"test-name": "test_default_whitelist"},
                retries=retry,
            )
            assert resp.status == 200

    def test_retries_wrong_method_list(self):
        """Method not in our whitelist should not be retried, even if code matches"""
        with HTTPConnectionPool(self.host, self.port) as pool:
            headers = {"test-name": "test_wrong_method_whitelist"}
            retry = Retry(total=1, status_forcelist=[418], method_whitelist=["POST"])
            resp = pool.request(
                "GET", "/successful_retry", headers=headers, retries=retry
            )
            assert resp.status == 418

    def test_read_retries_unsuccessful(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            headers = {"test-name": "test_read_retries_unsuccessful"}
            resp = pool.request("GET", "/successful_retry", headers=headers, retries=1)
            assert resp.status == 418

    def test_retry_reuse_safe(self):
        """It should be possible to reuse a Retry object across requests"""
        with HTTPConnectionPool(self.host, self.port) as pool:
            headers = {"test-name": "test_retry_safe"}
            retry = Retry(total=1, status_forcelist=[418])
            resp = pool.request(
                "GET", "/successful_retry", headers=headers, retries=retry
            )
            assert resp.status == 200

        with HTTPConnectionPool(self.host, self.port) as pool:
            resp = pool.request(
                "GET", "/successful_retry", headers=headers, retries=retry
            )
            assert resp.status == 200

    def test_retry_return_in_response(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            headers = {"test-name": "test_retry_return_in_response"}
            retry = Retry(total=2, status_forcelist=[418])
            resp = pool.request(
                "GET", "/successful_retry", headers=headers, retries=retry
            )
            assert resp.status == 200
            assert resp.retries.total == 1
            assert resp.retries.history == (
                RequestHistory("GET", "/successful_retry", None, 418, None),
            )

    def test_retry_redirect_history(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            resp = pool.request("GET", "/redirect", fields={"target": "/"})
            assert resp.status == 200
            assert resp.retries.history == (
                RequestHistory("GET", "/redirect?target=%2F", None, 303, "/"),
            )

    def test_multi_redirect_history(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request(
                "GET",
                "/multi_redirect",
                fields={"redirect_codes": "303,302,200"},
                redirect=False,
            )
            assert r.status == 303
            assert r.retries.history == tuple()

        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request(
                "GET",
                "/multi_redirect",
                retries=10,
                fields={"redirect_codes": "303,302,301,307,302,200"},
            )
            assert r.status == 200
            assert r.data == b"Done redirecting"

            expected = [
                (303, "/multi_redirect?redirect_codes=302,301,307,302,200"),
                (302, "/multi_redirect?redirect_codes=301,307,302,200"),
                (301, "/multi_redirect?redirect_codes=307,302,200"),
                (307, "/multi_redirect?redirect_codes=302,200"),
                (302, "/multi_redirect?redirect_codes=200"),
            ]
            actual = [
                (history.status, history.redirect_location)
                for history in r.retries.history
            ]
            assert actual == expected


class TestRetryAfter(HTTPDummyServerTestCase):
    def test_retry_after(self):
        # Request twice in a second to get a 429 response.
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request(
                "GET",
                "/retry_after",
                fields={"status": "429 Too Many Requests"},
                retries=False,
            )
            r = pool.request(
                "GET",
                "/retry_after",
                fields={"status": "429 Too Many Requests"},
                retries=False,
            )
            assert r.status == 429

            r = pool.request(
                "GET",
                "/retry_after",
                fields={"status": "429 Too Many Requests"},
                retries=True,
            )
            assert r.status == 200

            # Request twice in a second to get a 503 response.
            r = pool.request(
                "GET",
                "/retry_after",
                fields={"status": "503 Service Unavailable"},
                retries=False,
            )
            r = pool.request(
                "GET",
                "/retry_after",
                fields={"status": "503 Service Unavailable"},
                retries=False,
            )
            assert r.status == 503

            r = pool.request(
                "GET",
                "/retry_after",
                fields={"status": "503 Service Unavailable"},
                retries=True,
            )
            assert r.status == 200

            # Ignore Retry-After header on status which is not defined in
            # Retry.RETRY_AFTER_STATUS_CODES.
            r = pool.request(
                "GET",
                "/retry_after",
                fields={"status": "418 I'm a teapot"},
                retries=True,
            )
            assert r.status == 418

    def test_redirect_after(self):
        with HTTPConnectionPool(self.host, self.port) as pool:
            r = pool.request("GET", "/redirect_after", retries=False)
            assert r.status == 303

            t = time.time()
            r = pool.request("GET", "/redirect_after")
            assert r.status == 200
            delta = time.time() - t
            assert delta >= 1

            t = time.time()
            timestamp = t + 2
            r = pool.request("GET", "/redirect_after?date=" + str(timestamp))
            assert r.status == 200
            delta = time.time() - t
            assert delta >= 1

            # Retry-After is past
            t = time.time()
            timestamp = t - 1
            r = pool.request("GET", "/redirect_after?date=" + str(timestamp))
            delta = time.time() - t
            assert r.status == 200
            assert delta < 1


class TestFileBodiesOnRetryOrRedirect(HTTPDummyServerTestCase):
    def test_retries_put_filehandle(self):
        """HTTP PUT retry with a file-like object should not timeout"""
        with HTTPConnectionPool(self.host, self.port, timeout=0.1) as pool:
            retry = Retry(total=3, status_forcelist=[418])
            # httplib reads in 8k chunks; use a larger content length
            content_length = 65535
            data = b"A" * content_length
            uploaded_file = io.BytesIO(data)
            headers = {
                "test-name": "test_retries_put_filehandle",
                "Content-Length": str(content_length),
            }
            resp = pool.urlopen(
                "PUT",
                "/successful_retry",
                headers=headers,
                retries=retry,
                body=uploaded_file,
                assert_same_host=False,
                redirect=False,
            )
            assert resp.status == 200

    def test_redirect_put_file(self):
        """PUT with file object should work with a redirection response"""
        with HTTPConnectionPool(self.host, self.port, timeout=0.1) as pool:
            retry = Retry(total=3, status_forcelist=[418])
            # httplib reads in 8k chunks; use a larger content length
            content_length = 65535
            data = b"A" * content_length
            uploaded_file = io.BytesIO(data)
            headers = {
                "test-name": "test_redirect_put_file",
                "Content-Length": str(content_length),
            }
            url = "/redirect?target=/echo&status=307"
            resp = pool.urlopen(
                "PUT",
                url,
                headers=headers,
                retries=retry,
                body=uploaded_file,
                assert_same_host=False,
                redirect=True,
            )
            assert resp.status == 200
            assert resp.data == data

    def test_redirect_with_failed_tell(self):
        """Abort request if failed to get a position from tell()"""

        class BadTellObject(io.BytesIO):
            def tell(self):
                raise IOError

        body = BadTellObject(b"the data")
        url = "/redirect?target=/successful_retry"
        # httplib uses fileno if Content-Length isn't supplied,
        # which is unsupported by BytesIO.
        headers = {"Content-Length": "8"}
        with HTTPConnectionPool(self.host, self.port, timeout=0.1) as pool:
            with pytest.raises(UnrewindableBodyError) as e:
                pool.urlopen("PUT", url, headers=headers, body=body)
            assert "Unable to record file position for" in str(e.value)


class TestRetryPoolSize(HTTPDummyServerTestCase):
    def test_pool_size_retry(self):
        retries = Retry(total=1, raise_on_status=False, status_forcelist=[404])
        with HTTPConnectionPool(
            self.host, self.port, maxsize=10, retries=retries, block=True
        ) as pool:
            pool.urlopen("GET", "/not_found", preload_content=False)
            assert pool.num_connections == 1


class TestRedirectPoolSize(HTTPDummyServerTestCase):
    def test_pool_size_redirect(self):
        retries = Retry(
            total=1, raise_on_status=False, status_forcelist=[404], redirect=True
        )
        with HTTPConnectionPool(
            self.host, self.port, maxsize=10, retries=retries, block=True
        ) as pool:
            pool.urlopen("GET", "/redirect", preload_content=False)
            assert pool.num_connections == 1
