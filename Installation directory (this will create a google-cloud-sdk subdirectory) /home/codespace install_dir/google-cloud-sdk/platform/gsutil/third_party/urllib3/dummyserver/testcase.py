import threading
from contextlib import contextmanager

import pytest
from tornado import ioloop, web

from dummyserver.handlers import TestingApp
from dummyserver.proxy import ProxyHandler
from dummyserver.server import (
    DEFAULT_CERTS,
    HAS_IPV6,
    SocketServerThread,
    run_loop_in_thread,
    run_tornado_app,
)
from urllib3.connection import HTTPConnection


def consume_socket(sock, chunks=65536):
    consumed = bytearray()
    while True:
        b = sock.recv(chunks)
        consumed += b
        if b.endswith(b"\r\n\r\n"):
            break
    return consumed


class SocketDummyServerTestCase(object):
    """
    A simple socket-based server is created for this class that is good for
    exactly one request.
    """

    scheme = "http"
    host = "localhost"

    @classmethod
    def _start_server(cls, socket_handler):
        ready_event = threading.Event()
        cls.server_thread = SocketServerThread(
            socket_handler=socket_handler, ready_event=ready_event, host=cls.host
        )
        cls.server_thread.start()
        ready_event.wait(5)
        if not ready_event.is_set():
            raise Exception("most likely failed to start server")
        cls.port = cls.server_thread.port

    @classmethod
    def start_response_handler(cls, response, num=1, block_send=None):
        ready_event = threading.Event()

        def socket_handler(listener):
            for _ in range(num):
                ready_event.set()

                sock = listener.accept()[0]
                consume_socket(sock)
                if block_send:
                    block_send.wait()
                    block_send.clear()
                sock.send(response)
                sock.close()

        cls._start_server(socket_handler)
        return ready_event

    @classmethod
    def start_basic_handler(cls, **kw):
        return cls.start_response_handler(
            b"HTTP/1.1 200 OK\r\n" b"Content-Length: 0\r\n" b"\r\n", **kw
        )

    @classmethod
    def teardown_class(cls):
        if hasattr(cls, "server_thread"):
            cls.server_thread.join(0.1)

    def assert_header_received(
        self, received_headers, header_name, expected_value=None
    ):
        header_name = header_name.encode("ascii")
        if expected_value is not None:
            expected_value = expected_value.encode("ascii")
        header_titles = []
        for header in received_headers:
            key, value = header.split(b": ")
            header_titles.append(key)
            if key == header_name and expected_value is not None:
                assert value == expected_value
        assert header_name in header_titles


class IPV4SocketDummyServerTestCase(SocketDummyServerTestCase):
    @classmethod
    def _start_server(cls, socket_handler):
        ready_event = threading.Event()
        cls.server_thread = SocketServerThread(
            socket_handler=socket_handler, ready_event=ready_event, host=cls.host
        )
        cls.server_thread.USE_IPV6 = False
        cls.server_thread.start()
        ready_event.wait(5)
        if not ready_event.is_set():
            raise Exception("most likely failed to start server")
        cls.port = cls.server_thread.port


class HTTPDummyServerTestCase(object):
    """A simple HTTP server that runs when your test class runs

    Have your test class inherit from this one, and then a simple server
    will start when your tests run, and automatically shut down when they
    complete. For examples of what test requests you can send to the server,
    see the TestingApp in dummyserver/handlers.py.
    """

    scheme = "http"
    host = "localhost"
    host_alt = "127.0.0.1"  # Some tests need two hosts
    certs = DEFAULT_CERTS

    @classmethod
    def _start_server(cls):
        cls.io_loop = ioloop.IOLoop.current()
        app = web.Application([(r".*", TestingApp)])
        cls.server, cls.port = run_tornado_app(
            app, cls.io_loop, cls.certs, cls.scheme, cls.host
        )
        cls.server_thread = run_loop_in_thread(cls.io_loop)

    @classmethod
    def _stop_server(cls):
        cls.io_loop.add_callback(cls.server.stop)
        cls.io_loop.add_callback(cls.io_loop.stop)
        cls.server_thread.join()

    @classmethod
    def setup_class(cls):
        cls._start_server()

    @classmethod
    def teardown_class(cls):
        cls._stop_server()


class HTTPSDummyServerTestCase(HTTPDummyServerTestCase):
    scheme = "https"
    host = "localhost"
    certs = DEFAULT_CERTS


class HTTPDummyProxyTestCase(object):

    http_host = "localhost"
    http_host_alt = "127.0.0.1"

    https_host = "localhost"
    https_host_alt = "127.0.0.1"
    https_certs = DEFAULT_CERTS

    proxy_host = "localhost"
    proxy_host_alt = "127.0.0.1"

    @classmethod
    def setup_class(cls):
        cls.io_loop = ioloop.IOLoop.current()

        app = web.Application([(r".*", TestingApp)])
        cls.http_server, cls.http_port = run_tornado_app(
            app, cls.io_loop, None, "http", cls.http_host
        )

        app = web.Application([(r".*", TestingApp)])
        cls.https_server, cls.https_port = run_tornado_app(
            app, cls.io_loop, cls.https_certs, "https", cls.http_host
        )

        app = web.Application([(r".*", ProxyHandler)])
        cls.proxy_server, cls.proxy_port = run_tornado_app(
            app, cls.io_loop, None, "http", cls.proxy_host
        )

        upstream_ca_certs = cls.https_certs.get("ca_certs", None)
        app = web.Application(
            [(r".*", ProxyHandler)], upstream_ca_certs=upstream_ca_certs
        )
        cls.https_proxy_server, cls.https_proxy_port = run_tornado_app(
            app, cls.io_loop, cls.https_certs, "https", cls.proxy_host
        )

        cls.server_thread = run_loop_in_thread(cls.io_loop)

    @classmethod
    def teardown_class(cls):
        cls.io_loop.add_callback(cls.http_server.stop)
        cls.io_loop.add_callback(cls.https_server.stop)
        cls.io_loop.add_callback(cls.proxy_server.stop)
        cls.io_loop.add_callback(cls.https_proxy_server.stop)
        cls.io_loop.add_callback(cls.io_loop.stop)
        cls.server_thread.join()


@pytest.mark.skipif(not HAS_IPV6, reason="IPv6 not available")
class IPv6HTTPDummyServerTestCase(HTTPDummyServerTestCase):
    host = "::1"


@pytest.mark.skipif(not HAS_IPV6, reason="IPv6 not available")
class IPv6HTTPDummyProxyTestCase(HTTPDummyProxyTestCase):

    http_host = "localhost"
    http_host_alt = "127.0.0.1"

    https_host = "localhost"
    https_host_alt = "127.0.0.1"
    https_certs = DEFAULT_CERTS

    proxy_host = "::1"
    proxy_host_alt = "127.0.0.1"


class ConnectionMarker(object):
    """
    Marks an HTTP(S)Connection's socket after a request was made.

    Helps a test server understand when a client finished a request,
    without implementing a complete HTTP server.
    """

    MARK_FORMAT = b"$#MARK%04x*!"

    @classmethod
    @contextmanager
    def mark(cls, monkeypatch):
        """
        Mark connections under in that context.
        """

        orig_request = HTTPConnection.request
        orig_request_chunked = HTTPConnection.request_chunked

        def call_and_mark(target):
            def part(self, *args, **kwargs):
                result = target(self, *args, **kwargs)
                self.sock.sendall(cls._get_socket_mark(self.sock, False))
                return result

            return part

        with monkeypatch.context() as m:
            m.setattr(HTTPConnection, "request", call_and_mark(orig_request))
            m.setattr(
                HTTPConnection, "request_chunked", call_and_mark(orig_request_chunked)
            )
            yield

    @classmethod
    def consume_request(cls, sock, chunks=65536):
        """
        Consume a socket until after the HTTP request is sent.
        """
        consumed = bytearray()
        mark = cls._get_socket_mark(sock, True)
        while True:
            b = sock.recv(chunks)
            if not b:
                break
            consumed += b
            if consumed.endswith(mark):
                break
        return consumed

    @classmethod
    def _get_socket_mark(cls, sock, server):
        if server:
            port = sock.getpeername()[1]
        else:
            port = sock.getsockname()[1]
        return cls.MARK_FORMAT % (port,)
