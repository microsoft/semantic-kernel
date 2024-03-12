# -*- coding: utf-8 -*-

import pytest

from dummyserver.testcase import (
    ConnectionMarker,
    SocketDummyServerTestCase,
    consume_socket,
)
from urllib3 import HTTPConnectionPool
from urllib3.util import SKIP_HEADER
from urllib3.util.retry import Retry

# Retry failed tests
pytestmark = pytest.mark.flaky


class TestChunkedTransfer(SocketDummyServerTestCase):
    def start_chunked_handler(self):
        self.buffer = b""

        def socket_handler(listener):
            sock = listener.accept()[0]

            while not self.buffer.endswith(b"\r\n0\r\n\r\n"):
                self.buffer += sock.recv(65536)

            sock.send(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-type: text/plain\r\n"
                b"Content-Length: 0\r\n"
                b"\r\n"
            )
            sock.close()

        self._start_server(socket_handler)

    def test_chunks(self):
        self.start_chunked_handler()
        chunks = ["foo", "bar", "", "bazzzzzzzzzzzzzzzzzzzzzz"]
        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            pool.urlopen("GET", "/", body=chunks, headers=dict(DNT="1"), chunked=True)

            assert b"Transfer-Encoding" in self.buffer
            body = self.buffer.split(b"\r\n\r\n", 1)[1]
            lines = body.split(b"\r\n")
            # Empty chunks should have been skipped, as this could not be distinguished
            # from terminating the transmission
            for i, chunk in enumerate([c for c in chunks if c]):
                assert lines[i * 2] == hex(len(chunk))[2:].encode("utf-8")
                assert lines[i * 2 + 1] == chunk.encode("utf-8")

    def _test_body(self, data):
        self.start_chunked_handler()
        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            pool.urlopen("GET", "/", data, chunked=True)
            header, body = self.buffer.split(b"\r\n\r\n", 1)

            assert b"Transfer-Encoding: chunked" in header.split(b"\r\n")
            if data:
                bdata = data if isinstance(data, bytes) else data.encode("utf-8")
                assert b"\r\n" + bdata + b"\r\n" in body
                assert body.endswith(b"\r\n0\r\n\r\n")

                len_str = body.split(b"\r\n", 1)[0]
                stated_len = int(len_str, 16)
                assert stated_len == len(bdata)
            else:
                assert body == b"0\r\n\r\n"

    def test_bytestring_body(self):
        self._test_body(b"thisshouldbeonechunk\r\nasdf")

    def test_unicode_body(self):
        self._test_body(u"thisshouldbeonechunk\r\näöüß")

    def test_empty_body(self):
        self._test_body(None)

    def test_empty_string_body(self):
        self._test_body("")

    def test_empty_iterable_body(self):
        self._test_body([])

    def _get_header_lines(self, prefix):
        header_block = self.buffer.split(b"\r\n\r\n", 1)[0].lower()
        header_lines = header_block.split(b"\r\n")[1:]
        return [x for x in header_lines if x.startswith(prefix)]

    def test_removes_duplicate_host_header(self):
        self.start_chunked_handler()
        chunks = ["foo", "bar", "", "bazzzzzzzzzzzzzzzzzzzzzz"]
        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            pool.urlopen(
                "GET", "/", body=chunks, headers={"Host": "test.org"}, chunked=True
            )

            host_headers = self._get_header_lines(b"host")
            assert len(host_headers) == 1

    def test_provides_default_host_header(self):
        self.start_chunked_handler()
        chunks = ["foo", "bar", "", "bazzzzzzzzzzzzzzzzzzzzzz"]
        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            pool.urlopen("GET", "/", body=chunks, chunked=True)

            host_headers = self._get_header_lines(b"host")
            assert len(host_headers) == 1

    def test_provides_default_user_agent_header(self):
        self.start_chunked_handler()
        chunks = ["foo", "bar", "", "bazzzzzzzzzzzzzzzzzzzzzz"]
        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            pool.urlopen("GET", "/", body=chunks, chunked=True)

            ua_headers = self._get_header_lines(b"user-agent")
            assert len(ua_headers) == 1

    def test_preserve_user_agent_header(self):
        self.start_chunked_handler()
        chunks = ["foo", "bar", "", "bazzzzzzzzzzzzzzzzzzzzzz"]
        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            pool.urlopen(
                "GET",
                "/",
                body=chunks,
                headers={"user-Agent": "test-agent"},
                chunked=True,
            )

            ua_headers = self._get_header_lines(b"user-agent")
            # Validate that there is only one User-Agent header.
            assert len(ua_headers) == 1
            # Validate that the existing User-Agent header is the one that was
            # provided.
            assert ua_headers[0] == b"user-agent: test-agent"

    def test_remove_user_agent_header(self):
        self.start_chunked_handler()
        chunks = ["foo", "bar", "", "bazzzzzzzzzzzzzzzzzzzzzz"]
        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            pool.urlopen(
                "GET",
                "/",
                body=chunks,
                headers={"User-Agent": SKIP_HEADER},
                chunked=True,
            )

            ua_headers = self._get_header_lines(b"user-agent")
            assert len(ua_headers) == 0

    def test_provides_default_transfer_encoding_header(self):
        self.start_chunked_handler()
        chunks = ["foo", "bar", "", "bazzzzzzzzzzzzzzzzzzzzzz"]
        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            pool.urlopen("GET", "/", body=chunks, chunked=True)

            te_headers = self._get_header_lines(b"transfer-encoding")
            assert len(te_headers) == 1

    def test_preserve_transfer_encoding_header(self):
        self.start_chunked_handler()
        chunks = ["foo", "bar", "", "bazzzzzzzzzzzzzzzzzzzzzz"]
        with HTTPConnectionPool(self.host, self.port, retries=False) as pool:
            pool.urlopen(
                "GET",
                "/",
                body=chunks,
                headers={"transfer-Encoding": "test-transfer-encoding"},
                chunked=True,
            )

            te_headers = self._get_header_lines(b"transfer-encoding")
            # Validate that there is only one Transfer-Encoding header.
            assert len(te_headers) == 1
            # Validate that the existing Transfer-Encoding header is the one that
            # was provided.
            assert te_headers[0] == b"transfer-encoding: test-transfer-encoding"

    def test_preserve_chunked_on_retry_after(self):
        self.chunked_requests = 0
        self.socks = []

        def socket_handler(listener):
            for _ in range(2):
                sock = listener.accept()[0]
                self.socks.append(sock)
                request = consume_socket(sock)
                if b"Transfer-Encoding: chunked" in request.split(b"\r\n"):
                    self.chunked_requests += 1

                sock.send(
                    b"HTTP/1.1 429 Too Many Requests\r\n"
                    b"Content-Type: text/plain\r\n"
                    b"Retry-After: 1\r\n"
                    b"Content-Length: 0\r\n"
                    b"Connection: close\r\n"
                    b"\r\n"
                )

        self._start_server(socket_handler)
        with HTTPConnectionPool(self.host, self.port) as pool:
            retries = Retry(total=1)
            pool.urlopen("GET", "/", chunked=True, retries=retries)
            for sock in self.socks:
                sock.close()
        assert self.chunked_requests == 2

    def test_preserve_chunked_on_redirect(self, monkeypatch):
        self.chunked_requests = 0

        def socket_handler(listener):
            for i in range(2):
                sock = listener.accept()[0]
                request = ConnectionMarker.consume_request(sock)
                if b"Transfer-Encoding: chunked" in request.split(b"\r\n"):
                    self.chunked_requests += 1

                if i == 0:
                    sock.sendall(
                        b"HTTP/1.1 301 Moved Permanently\r\n"
                        b"Location: /redirect\r\n\r\n"
                    )
                else:
                    sock.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
                sock.close()

        self._start_server(socket_handler)
        with ConnectionMarker.mark(monkeypatch):
            with HTTPConnectionPool(self.host, self.port) as pool:
                retries = Retry(redirect=1)
                pool.urlopen(
                    "GET", "/", chunked=True, preload_content=False, retries=retries
                )
        assert self.chunked_requests == 2

    def test_preserve_chunked_on_broken_connection(self, monkeypatch):
        self.chunked_requests = 0

        def socket_handler(listener):
            for i in range(2):
                sock = listener.accept()[0]
                request = ConnectionMarker.consume_request(sock)
                if b"Transfer-Encoding: chunked" in request.split(b"\r\n"):
                    self.chunked_requests += 1

                if i == 0:
                    # Bad HTTP version will trigger a connection close
                    sock.sendall(b"HTTP/0.5 200 OK\r\n\r\n")
                else:
                    sock.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
                sock.close()

        self._start_server(socket_handler)
        with ConnectionMarker.mark(monkeypatch):
            with HTTPConnectionPool(self.host, self.port) as pool:
                retries = Retry(read=1)
                pool.urlopen(
                    "GET", "/", chunked=True, preload_content=False, retries=retries
                )
            assert self.chunked_requests == 2
