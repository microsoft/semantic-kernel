# -*- coding: utf-8 -*-

import contextlib
import re
import socket
import ssl
import zlib
from base64 import b64decode
from io import BufferedReader, BytesIO, TextIOWrapper
from test import onlyBrotlipy

import mock
import pytest
import six

from urllib3.exceptions import (
    DecodeError,
    IncompleteRead,
    InvalidChunkLength,
    InvalidHeader,
    ProtocolError,
    ResponseNotChunked,
    SSLError,
    httplib_IncompleteRead,
)
from urllib3.packages.six.moves import http_client as httplib
from urllib3.response import HTTPResponse, brotli
from urllib3.util.response import is_fp_closed
from urllib3.util.retry import RequestHistory, Retry

# A known random (i.e, not-too-compressible) payload generated with:
#    "".join(random.choice(string.printable) for i in xrange(512))
#    .encode("zlib").encode("base64")
# Randomness in tests == bad, and fixing a seed may not be sufficient.
ZLIB_PAYLOAD = b64decode(
    b"""\
eJwFweuaoQAAANDfineQhiKLUiaiCzvuTEmNNlJGiL5QhnGpZ99z8luQfe1AHoMioB+QSWHQu/L+
lzd7W5CipqYmeVTBjdgSATdg4l4Z2zhikbuF+EKn69Q0DTpdmNJz8S33odfJoVEexw/l2SS9nFdi
pis7KOwXzfSqarSo9uJYgbDGrs1VNnQpT9f8zAorhYCEZronZQF9DuDFfNK3Hecc+WHLnZLQptwk
nufw8S9I43sEwxsT71BiqedHo0QeIrFE01F/4atVFXuJs2yxIOak3bvtXjUKAA6OKnQJ/nNvDGKZ
Khe5TF36JbnKVjdcL1EUNpwrWVfQpFYJ/WWm2b74qNeSZeQv5/xBhRdOmKTJFYgO96PwrHBlsnLn
a3l0LwJsloWpMbzByU5WLbRE6X5INFqjQOtIwYz5BAlhkn+kVqJvWM5vBlfrwP42ifonM5yF4ciJ
auHVks62997mNGOsM7WXNG3P98dBHPo2NhbTvHleL0BI5dus2JY81MUOnK3SGWLH8HeWPa1t5KcW
S5moAj5HexY/g/F8TctpxwsvyZp38dXeLDjSQvEQIkF7XR3YXbeZgKk3V34KGCPOAeeuQDIgyVhV
nP4HF2uWHA=="""
)


@pytest.fixture
def sock():
    s = socket.socket()
    yield s
    s.close()


class TestLegacyResponse(object):
    def test_getheaders(self):
        headers = {"host": "example.com"}
        r = HTTPResponse(headers=headers)
        assert r.getheaders() == headers

    def test_getheader(self):
        headers = {"host": "example.com"}
        r = HTTPResponse(headers=headers)
        assert r.getheader("host") == "example.com"


class TestResponse(object):
    def test_cache_content(self):
        r = HTTPResponse("foo")
        assert r.data == "foo"
        assert r._body == "foo"

    def test_default(self):
        r = HTTPResponse()
        assert r.data is None

    def test_none(self):
        r = HTTPResponse(None)
        assert r.data is None

    def test_preload(self):
        fp = BytesIO(b"foo")

        r = HTTPResponse(fp, preload_content=True)

        assert fp.tell() == len(b"foo")
        assert r.data == b"foo"

    def test_no_preload(self):
        fp = BytesIO(b"foo")

        r = HTTPResponse(fp, preload_content=False)

        assert fp.tell() == 0
        assert r.data == b"foo"
        assert fp.tell() == len(b"foo")

    def test_decode_bad_data(self):
        fp = BytesIO(b"\x00" * 10)
        with pytest.raises(DecodeError):
            HTTPResponse(fp, headers={"content-encoding": "deflate"})

    def test_reference_read(self):
        fp = BytesIO(b"foo")
        r = HTTPResponse(fp, preload_content=False)

        assert r.read(1) == b"f"
        assert r.read(2) == b"oo"
        assert r.read() == b""
        assert r.read() == b""

    def test_decode_deflate(self):
        data = zlib.compress(b"foo")

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={"content-encoding": "deflate"})

        assert r.data == b"foo"

    def test_decode_deflate_case_insensitve(self):
        data = zlib.compress(b"foo")

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={"content-encoding": "DeFlAtE"})

        assert r.data == b"foo"

    def test_chunked_decoding_deflate(self):
        data = zlib.compress(b"foo")

        fp = BytesIO(data)
        r = HTTPResponse(
            fp, headers={"content-encoding": "deflate"}, preload_content=False
        )

        assert r.read(3) == b""
        # Buffer in case we need to switch to the raw stream
        assert r._decoder._data is not None
        assert r.read(1) == b"f"
        # Now that we've decoded data, we just stream through the decoder
        assert r._decoder._data is None
        assert r.read(2) == b"oo"
        assert r.read() == b""
        assert r.read() == b""

    def test_chunked_decoding_deflate2(self):
        compress = zlib.compressobj(6, zlib.DEFLATED, -zlib.MAX_WBITS)
        data = compress.compress(b"foo")
        data += compress.flush()

        fp = BytesIO(data)
        r = HTTPResponse(
            fp, headers={"content-encoding": "deflate"}, preload_content=False
        )

        assert r.read(1) == b""
        assert r.read(1) == b"f"
        # Once we've decoded data, we just stream to the decoder; no buffering
        assert r._decoder._data is None
        assert r.read(2) == b"oo"
        assert r.read() == b""
        assert r.read() == b""

    def test_chunked_decoding_gzip(self):
        compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        data = compress.compress(b"foo")
        data += compress.flush()

        fp = BytesIO(data)
        r = HTTPResponse(
            fp, headers={"content-encoding": "gzip"}, preload_content=False
        )

        assert r.read(11) == b""
        assert r.read(1) == b"f"
        assert r.read(2) == b"oo"
        assert r.read() == b""
        assert r.read() == b""

    def test_decode_gzip_multi_member(self):
        compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        data = compress.compress(b"foo")
        data += compress.flush()
        data = data * 3

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={"content-encoding": "gzip"})

        assert r.data == b"foofoofoo"

    def test_decode_gzip_error(self):
        fp = BytesIO(b"foo")
        with pytest.raises(DecodeError):
            HTTPResponse(fp, headers={"content-encoding": "gzip"})

    def test_decode_gzip_swallow_garbage(self):
        # When data comes from multiple calls to read(), data after
        # the first zlib error (here triggered by garbage) should be
        # ignored.
        compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        data = compress.compress(b"foo")
        data += compress.flush()
        data = data * 3 + b"foo"

        fp = BytesIO(data)
        r = HTTPResponse(
            fp, headers={"content-encoding": "gzip"}, preload_content=False
        )
        ret = b""
        for _ in range(100):
            ret += r.read(1)
            if r.closed:
                break

        assert ret == b"foofoofoo"

    def test_chunked_decoding_gzip_swallow_garbage(self):
        compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        data = compress.compress(b"foo")
        data += compress.flush()
        data = data * 3 + b"foo"

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={"content-encoding": "gzip"})

        assert r.data == b"foofoofoo"

    @onlyBrotlipy()
    def test_decode_brotli(self):
        data = brotli.compress(b"foo")

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={"content-encoding": "br"})
        assert r.data == b"foo"

    @onlyBrotlipy()
    def test_chunked_decoding_brotli(self):
        data = brotli.compress(b"foobarbaz")

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={"content-encoding": "br"}, preload_content=False)

        ret = b""
        for _ in range(100):
            ret += r.read(1)
            if r.closed:
                break
        assert ret == b"foobarbaz"

    @onlyBrotlipy()
    def test_decode_brotli_error(self):
        fp = BytesIO(b"foo")
        with pytest.raises(DecodeError):
            HTTPResponse(fp, headers={"content-encoding": "br"})

    def test_multi_decoding_deflate_deflate(self):
        data = zlib.compress(zlib.compress(b"foo"))

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={"content-encoding": "deflate, deflate"})

        assert r.data == b"foo"

    def test_multi_decoding_deflate_gzip(self):
        compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        data = compress.compress(zlib.compress(b"foo"))
        data += compress.flush()

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={"content-encoding": "deflate, gzip"})

        assert r.data == b"foo"

    def test_multi_decoding_gzip_gzip(self):
        compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        data = compress.compress(b"foo")
        data += compress.flush()

        compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        data = compress.compress(data)
        data += compress.flush()

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={"content-encoding": "gzip, gzip"})

        assert r.data == b"foo"

    def test_body_blob(self):
        resp = HTTPResponse(b"foo")
        assert resp.data == b"foo"
        assert resp.closed

    def test_io(self, sock):
        fp = BytesIO(b"foo")
        resp = HTTPResponse(fp, preload_content=False)

        assert not resp.closed
        assert resp.readable()
        assert not resp.writable()
        with pytest.raises(IOError):
            resp.fileno()

        resp.close()
        assert resp.closed

        # Try closing with an `httplib.HTTPResponse`, because it has an
        # `isclosed` method.
        try:
            hlr = httplib.HTTPResponse(sock)
            resp2 = HTTPResponse(hlr, preload_content=False)
            assert not resp2.closed
            resp2.close()
            assert resp2.closed
        finally:
            hlr.close()

        # also try when only data is present.
        resp3 = HTTPResponse("foodata")
        with pytest.raises(IOError):
            resp3.fileno()

        resp3._fp = 2
        # A corner case where _fp is present but doesn't have `closed`,
        # `isclosed`, or `fileno`.  Unlikely, but possible.
        assert resp3.closed
        with pytest.raises(IOError):
            resp3.fileno()

    def test_io_closed_consistently(self, sock):
        try:
            hlr = httplib.HTTPResponse(sock)
            hlr.fp = BytesIO(b"foo")
            hlr.chunked = 0
            hlr.length = 3
            with HTTPResponse(hlr, preload_content=False) as resp:
                assert not resp.closed
                assert not resp._fp.isclosed()
                assert not is_fp_closed(resp._fp)
                assert not resp.isclosed()
                resp.read()
                assert resp.closed
                assert resp._fp.isclosed()
                assert is_fp_closed(resp._fp)
                assert resp.isclosed()
        finally:
            hlr.close()

    def test_io_bufferedreader(self):
        fp = BytesIO(b"foo")
        resp = HTTPResponse(fp, preload_content=False)
        br = BufferedReader(resp)

        assert br.read() == b"foo"

        br.close()
        assert resp.closed

        # HTTPResponse.read() by default closes the response
        # https://github.com/urllib3/urllib3/issues/1305
        fp = BytesIO(b"hello\nworld")
        resp = HTTPResponse(fp, preload_content=False)
        with pytest.raises(ValueError) as ctx:
            list(BufferedReader(resp))
        assert str(ctx.value) == "readline of closed file"

        b = b"fooandahalf"
        fp = BytesIO(b)
        resp = HTTPResponse(fp, preload_content=False)
        br = BufferedReader(resp, 5)

        br.read(1)  # sets up the buffer, reading 5
        assert len(fp.read()) == (len(b) - 5)

        # This is necessary to make sure the "no bytes left" part of `readinto`
        # gets tested.
        while not br.closed:
            br.read(5)

    def test_io_not_autoclose_bufferedreader(self):
        fp = BytesIO(b"hello\nworld")
        resp = HTTPResponse(fp, preload_content=False, auto_close=False)
        reader = BufferedReader(resp)
        assert list(reader) == [b"hello\n", b"world"]

        assert not reader.closed
        assert not resp.closed
        with pytest.raises(StopIteration):
            next(reader)

        reader.close()
        assert reader.closed
        assert resp.closed
        with pytest.raises(ValueError) as ctx:
            next(reader)
        assert str(ctx.value) == "readline of closed file"

    def test_io_textiowrapper(self):
        fp = BytesIO(b"\xc3\xa4\xc3\xb6\xc3\xbc\xc3\x9f")
        resp = HTTPResponse(fp, preload_content=False)
        br = TextIOWrapper(resp, encoding="utf8")

        assert br.read() == u"äöüß"

        br.close()
        assert resp.closed

        # HTTPResponse.read() by default closes the response
        # https://github.com/urllib3/urllib3/issues/1305
        fp = BytesIO(
            b"\xc3\xa4\xc3\xb6\xc3\xbc\xc3\x9f\n\xce\xb1\xce\xb2\xce\xb3\xce\xb4"
        )
        resp = HTTPResponse(fp, preload_content=False)
        with pytest.raises(ValueError) as ctx:
            if six.PY2:
                # py2's implementation of TextIOWrapper requires `read1`
                # method which is provided by `BufferedReader` wrapper
                resp = BufferedReader(resp)
            list(TextIOWrapper(resp))
        assert re.match("I/O operation on closed file.?", str(ctx.value))

    def test_io_not_autoclose_textiowrapper(self):
        fp = BytesIO(
            b"\xc3\xa4\xc3\xb6\xc3\xbc\xc3\x9f\n\xce\xb1\xce\xb2\xce\xb3\xce\xb4"
        )
        resp = HTTPResponse(fp, preload_content=False, auto_close=False)
        if six.PY2:
            # py2's implementation of TextIOWrapper requires `read1`
            # method which is provided by `BufferedReader` wrapper
            resp = BufferedReader(resp)
        reader = TextIOWrapper(resp, encoding="utf8")
        assert list(reader) == [u"äöüß\n", u"αβγδ"]

        assert not reader.closed
        assert not resp.closed
        with pytest.raises(StopIteration):
            next(reader)

        reader.close()
        assert reader.closed
        assert resp.closed
        with pytest.raises(ValueError) as ctx:
            next(reader)
        assert re.match("I/O operation on closed file.?", str(ctx.value))

    def test_streaming(self):
        fp = BytesIO(b"foo")
        resp = HTTPResponse(fp, preload_content=False)
        stream = resp.stream(2, decode_content=False)

        assert next(stream) == b"fo"
        assert next(stream) == b"o"
        with pytest.raises(StopIteration):
            next(stream)

    def test_streaming_tell(self):
        fp = BytesIO(b"foo")
        resp = HTTPResponse(fp, preload_content=False)
        stream = resp.stream(2, decode_content=False)

        position = 0

        position += len(next(stream))
        assert 2 == position
        assert position == resp.tell()

        position += len(next(stream))
        assert 3 == position
        assert position == resp.tell()

        with pytest.raises(StopIteration):
            next(stream)

    def test_gzipped_streaming(self):
        compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        data = compress.compress(b"foo")
        data += compress.flush()

        fp = BytesIO(data)
        resp = HTTPResponse(
            fp, headers={"content-encoding": "gzip"}, preload_content=False
        )
        stream = resp.stream(2)

        assert next(stream) == b"f"
        assert next(stream) == b"oo"
        with pytest.raises(StopIteration):
            next(stream)

    def test_gzipped_streaming_tell(self):
        compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        uncompressed_data = b"foo"
        data = compress.compress(uncompressed_data)
        data += compress.flush()

        fp = BytesIO(data)
        resp = HTTPResponse(
            fp, headers={"content-encoding": "gzip"}, preload_content=False
        )
        stream = resp.stream()

        # Read everything
        payload = next(stream)
        assert payload == uncompressed_data

        assert len(data) == resp.tell()

        with pytest.raises(StopIteration):
            next(stream)

    def test_deflate_streaming_tell_intermediate_point(self):
        # Ensure that ``tell()`` returns the correct number of bytes when
        # part-way through streaming compressed content.
        NUMBER_OF_READS = 10

        class MockCompressedDataReading(BytesIO):
            """
            A BytesIO-like reader returning ``payload`` in ``NUMBER_OF_READS``
            calls to ``read``.
            """

            def __init__(self, payload, payload_part_size):
                self.payloads = [
                    payload[i * payload_part_size : (i + 1) * payload_part_size]
                    for i in range(NUMBER_OF_READS + 1)
                ]

                assert b"".join(self.payloads) == payload

            def read(self, _):
                # Amount is unused.
                if len(self.payloads) > 0:
                    return self.payloads.pop(0)
                return b""

        uncompressed_data = zlib.decompress(ZLIB_PAYLOAD)

        payload_part_size = len(ZLIB_PAYLOAD) // NUMBER_OF_READS
        fp = MockCompressedDataReading(ZLIB_PAYLOAD, payload_part_size)
        resp = HTTPResponse(
            fp, headers={"content-encoding": "deflate"}, preload_content=False
        )
        stream = resp.stream()

        parts_positions = [(part, resp.tell()) for part in stream]
        end_of_stream = resp.tell()

        with pytest.raises(StopIteration):
            next(stream)

        parts, positions = zip(*parts_positions)

        # Check that the payload is equal to the uncompressed data
        payload = b"".join(parts)
        assert uncompressed_data == payload

        # Check that the positions in the stream are correct
        expected = [(i + 1) * payload_part_size for i in range(NUMBER_OF_READS)]
        assert expected == list(positions)

        # Check that the end of the stream is in the correct place
        assert len(ZLIB_PAYLOAD) == end_of_stream

    def test_deflate_streaming(self):
        data = zlib.compress(b"foo")

        fp = BytesIO(data)
        resp = HTTPResponse(
            fp, headers={"content-encoding": "deflate"}, preload_content=False
        )
        stream = resp.stream(2)

        assert next(stream) == b"f"
        assert next(stream) == b"oo"
        with pytest.raises(StopIteration):
            next(stream)

    def test_deflate2_streaming(self):
        compress = zlib.compressobj(6, zlib.DEFLATED, -zlib.MAX_WBITS)
        data = compress.compress(b"foo")
        data += compress.flush()

        fp = BytesIO(data)
        resp = HTTPResponse(
            fp, headers={"content-encoding": "deflate"}, preload_content=False
        )
        stream = resp.stream(2)

        assert next(stream) == b"f"
        assert next(stream) == b"oo"
        with pytest.raises(StopIteration):
            next(stream)

    def test_empty_stream(self):
        fp = BytesIO(b"")
        resp = HTTPResponse(fp, preload_content=False)
        stream = resp.stream(2, decode_content=False)

        with pytest.raises(StopIteration):
            next(stream)

    def test_length_no_header(self):
        fp = BytesIO(b"12345")
        resp = HTTPResponse(fp, preload_content=False)
        assert resp.length_remaining is None

    def test_length_w_valid_header(self):
        headers = {"content-length": "5"}
        fp = BytesIO(b"12345")

        resp = HTTPResponse(fp, headers=headers, preload_content=False)
        assert resp.length_remaining == 5

    def test_length_w_bad_header(self):
        garbage = {"content-length": "foo"}
        fp = BytesIO(b"12345")

        resp = HTTPResponse(fp, headers=garbage, preload_content=False)
        assert resp.length_remaining is None

        garbage["content-length"] = "-10"
        resp = HTTPResponse(fp, headers=garbage, preload_content=False)
        assert resp.length_remaining is None

    def test_length_when_chunked(self):
        # This is expressly forbidden in RFC 7230 sec 3.3.2
        # We fall back to chunked in this case and try to
        # handle response ignoring content length.
        headers = {"content-length": "5", "transfer-encoding": "chunked"}
        fp = BytesIO(b"12345")

        resp = HTTPResponse(fp, headers=headers, preload_content=False)
        assert resp.length_remaining is None

    def test_length_with_multiple_content_lengths(self):
        headers = {"content-length": "5, 5, 5"}
        garbage = {"content-length": "5, 42"}
        fp = BytesIO(b"abcde")

        resp = HTTPResponse(fp, headers=headers, preload_content=False)
        assert resp.length_remaining == 5

        with pytest.raises(InvalidHeader):
            HTTPResponse(fp, headers=garbage, preload_content=False)

    def test_length_after_read(self):
        headers = {"content-length": "5"}

        # Test no defined length
        fp = BytesIO(b"12345")
        resp = HTTPResponse(fp, preload_content=False)
        resp.read()
        assert resp.length_remaining is None

        # Test our update from content-length
        fp = BytesIO(b"12345")
        resp = HTTPResponse(fp, headers=headers, preload_content=False)
        resp.read()
        assert resp.length_remaining == 0

        # Test partial read
        fp = BytesIO(b"12345")
        resp = HTTPResponse(fp, headers=headers, preload_content=False)
        data = resp.stream(2)
        next(data)
        assert resp.length_remaining == 3

    def test_mock_httpresponse_stream(self):
        # Mock out a HTTP Request that does enough to make it through urllib3's
        # read() and close() calls, and also exhausts and underlying file
        # object.
        class MockHTTPRequest(object):
            self.fp = None

            def read(self, amt):
                data = self.fp.read(amt)
                if not data:
                    self.fp = None

                return data

            def close(self):
                self.fp = None

        bio = BytesIO(b"foo")
        fp = MockHTTPRequest()
        fp.fp = bio
        resp = HTTPResponse(fp, preload_content=False)
        stream = resp.stream(2)

        assert next(stream) == b"fo"
        assert next(stream) == b"o"
        with pytest.raises(StopIteration):
            next(stream)

    def test_mock_transfer_encoding_chunked(self):
        stream = [b"fo", b"o", b"bar"]
        fp = MockChunkedEncodingResponse(stream)
        r = httplib.HTTPResponse(MockSock)
        r.fp = fp
        resp = HTTPResponse(
            r, preload_content=False, headers={"transfer-encoding": "chunked"}
        )

        for i, c in enumerate(resp.stream()):
            assert c == stream[i]

    def test_mock_gzipped_transfer_encoding_chunked_decoded(self):
        """Show that we can decode the gzipped and chunked body."""

        def stream():
            # Set up a generator to chunk the gzipped body
            compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
            data = compress.compress(b"foobar")
            data += compress.flush()
            for i in range(0, len(data), 2):
                yield data[i : i + 2]

        fp = MockChunkedEncodingResponse(list(stream()))
        r = httplib.HTTPResponse(MockSock)
        r.fp = fp
        headers = {"transfer-encoding": "chunked", "content-encoding": "gzip"}
        resp = HTTPResponse(r, preload_content=False, headers=headers)

        data = b""
        for c in resp.stream(decode_content=True):
            data += c

        assert b"foobar" == data

    def test_mock_transfer_encoding_chunked_custom_read(self):
        stream = [b"foooo", b"bbbbaaaaar"]
        fp = MockChunkedEncodingResponse(stream)
        r = httplib.HTTPResponse(MockSock)
        r.fp = fp
        r.chunked = True
        r.chunk_left = None
        resp = HTTPResponse(
            r, preload_content=False, headers={"transfer-encoding": "chunked"}
        )
        expected_response = [b"fo", b"oo", b"o", b"bb", b"bb", b"aa", b"aa", b"ar"]
        response = list(resp.read_chunked(2))
        assert expected_response == response

    def test_mock_transfer_encoding_chunked_unlmtd_read(self):
        stream = [b"foooo", b"bbbbaaaaar"]
        fp = MockChunkedEncodingResponse(stream)
        r = httplib.HTTPResponse(MockSock)
        r.fp = fp
        r.chunked = True
        r.chunk_left = None
        resp = HTTPResponse(
            r, preload_content=False, headers={"transfer-encoding": "chunked"}
        )
        assert stream == list(resp.read_chunked())

    def test_read_not_chunked_response_as_chunks(self):
        fp = BytesIO(b"foo")
        resp = HTTPResponse(fp, preload_content=False)
        r = resp.read_chunked()
        with pytest.raises(ResponseNotChunked):
            next(r)

    def test_buggy_incomplete_read(self):
        # Simulate buggy versions of Python (<2.7.4)
        # See http://bugs.python.org/issue16298
        content_length = 1337
        fp = BytesIO(b"")
        resp = HTTPResponse(
            fp,
            headers={"content-length": str(content_length)},
            preload_content=False,
            enforce_content_length=True,
        )
        with pytest.raises(ProtocolError) as ctx:
            resp.read(3)

        orig_ex = ctx.value.args[1]
        assert isinstance(orig_ex, IncompleteRead)
        assert orig_ex.partial == 0
        assert orig_ex.expected == content_length

    def test_incomplete_chunk(self):
        stream = [b"foooo", b"bbbbaaaaar"]
        fp = MockChunkedIncompleteRead(stream)
        r = httplib.HTTPResponse(MockSock)
        r.fp = fp
        r.chunked = True
        r.chunk_left = None
        resp = HTTPResponse(
            r, preload_content=False, headers={"transfer-encoding": "chunked"}
        )
        with pytest.raises(ProtocolError) as ctx:
            next(resp.read_chunked())

        orig_ex = ctx.value.args[1]
        assert isinstance(orig_ex, httplib_IncompleteRead)

    def test_invalid_chunk_length(self):
        stream = [b"foooo", b"bbbbaaaaar"]
        fp = MockChunkedInvalidChunkLength(stream)
        r = httplib.HTTPResponse(MockSock)
        r.fp = fp
        r.chunked = True
        r.chunk_left = None
        resp = HTTPResponse(
            r, preload_content=False, headers={"transfer-encoding": "chunked"}
        )
        with pytest.raises(ProtocolError) as ctx:
            next(resp.read_chunked())

        orig_ex = ctx.value.args[1]
        assert isinstance(orig_ex, InvalidChunkLength)
        assert orig_ex.length == six.b(fp.BAD_LENGTH_LINE)

    def test_chunked_response_without_crlf_on_end(self):
        stream = [b"foo", b"bar", b"baz"]
        fp = MockChunkedEncodingWithoutCRLFOnEnd(stream)
        r = httplib.HTTPResponse(MockSock)
        r.fp = fp
        r.chunked = True
        r.chunk_left = None
        resp = HTTPResponse(
            r, preload_content=False, headers={"transfer-encoding": "chunked"}
        )
        assert stream == list(resp.stream())

    def test_chunked_response_with_extensions(self):
        stream = [b"foo", b"bar"]
        fp = MockChunkedEncodingWithExtensions(stream)
        r = httplib.HTTPResponse(MockSock)
        r.fp = fp
        r.chunked = True
        r.chunk_left = None
        resp = HTTPResponse(
            r, preload_content=False, headers={"transfer-encoding": "chunked"}
        )
        assert stream == list(resp.stream())

    def test_chunked_head_response(self):
        r = httplib.HTTPResponse(MockSock, method="HEAD")
        r.chunked = True
        r.chunk_left = None
        resp = HTTPResponse(
            "",
            preload_content=False,
            headers={"transfer-encoding": "chunked"},
            original_response=r,
        )
        assert resp.chunked is True

        resp.supports_chunked_reads = lambda: True
        resp.release_conn = mock.Mock()
        for _ in resp.stream():
            continue
        resp.release_conn.assert_called_once_with()

    def test_get_case_insensitive_headers(self):
        headers = {"host": "example.com"}
        r = HTTPResponse(headers=headers)
        assert r.headers.get("host") == "example.com"
        assert r.headers.get("Host") == "example.com"

    def test_retries(self):
        fp = BytesIO(b"")
        resp = HTTPResponse(fp)
        assert resp.retries is None
        retry = Retry()
        resp = HTTPResponse(fp, retries=retry)
        assert resp.retries == retry

    def test_geturl(self):
        fp = BytesIO(b"")
        request_url = "https://example.com"
        resp = HTTPResponse(fp, request_url=request_url)
        assert resp.geturl() == request_url

    def test_geturl_retries(self):
        fp = BytesIO(b"")
        resp = HTTPResponse(fp, request_url="http://example.com")
        request_histories = [
            RequestHistory(
                method="GET",
                url="http://example.com",
                error=None,
                status=301,
                redirect_location="https://example.com/",
            ),
            RequestHistory(
                method="GET",
                url="https://example.com/",
                error=None,
                status=301,
                redirect_location="https://www.example.com",
            ),
        ]
        retry = Retry(history=request_histories)
        resp = HTTPResponse(fp, retries=retry)
        assert resp.geturl() == "https://www.example.com"

    @pytest.mark.parametrize(
        ["payload", "expected_stream"],
        [
            (b"", []),
            (b"\n", [b"\n"]),
            (b"\n\n\n", [b"\n", b"\n", b"\n"]),
            (b"abc\ndef", [b"abc\n", b"def"]),
            (b"Hello\nworld\n\n\n!", [b"Hello\n", b"world\n", b"\n", b"\n", b"!"]),
        ],
    )
    def test__iter__(self, payload, expected_stream):
        actual_stream = []
        for chunk in HTTPResponse(BytesIO(payload), preload_content=False):
            actual_stream.append(chunk)

        assert actual_stream == expected_stream

    def test__iter__decode_content(self):
        def stream():
            # Set up a generator to chunk the gzipped body
            compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
            data = compress.compress(b"foo\nbar")
            data += compress.flush()
            for i in range(0, len(data), 2):
                yield data[i : i + 2]

        fp = MockChunkedEncodingResponse(list(stream()))
        r = httplib.HTTPResponse(MockSock)
        r.fp = fp
        headers = {"transfer-encoding": "chunked", "content-encoding": "gzip"}
        resp = HTTPResponse(r, preload_content=False, headers=headers)

        data = b""
        for c in resp:
            data += c

        assert b"foo\nbar" == data

    def test_non_timeout_ssl_error_on_read(self):
        mac_error = ssl.SSLError(
            "SSL routines", "ssl3_get_record", "decryption failed or bad record mac"
        )

        @contextlib.contextmanager
        def make_bad_mac_fp():
            fp = BytesIO(b"")
            with mock.patch.object(fp, "read") as fp_read:
                # mac/decryption error
                fp_read.side_effect = mac_error
                yield fp

        with make_bad_mac_fp() as fp:
            with pytest.raises(SSLError) as e:
                HTTPResponse(fp)
            assert e.value.args[0] == mac_error

        with make_bad_mac_fp() as fp:
            resp = HTTPResponse(fp, preload_content=False)
            with pytest.raises(SSLError) as e:
                resp.read()
            assert e.value.args[0] == mac_error


class MockChunkedEncodingResponse(object):
    def __init__(self, content):
        """
        content: collection of str, each str is a chunk in response
        """
        self.content = content
        self.index = 0  # This class iterates over self.content.
        self.closed = False
        self.cur_chunk = b""
        self.chunks_exhausted = False

    @staticmethod
    def _encode_chunk(chunk):
        # In the general case, we can't decode the chunk to unicode
        length = "%X\r\n" % len(chunk)
        return length.encode() + chunk + b"\r\n"

    def _pop_new_chunk(self):
        if self.chunks_exhausted:
            return b""
        try:
            chunk = self.content[self.index]
        except IndexError:
            chunk = b""
            self.chunks_exhausted = True
        else:
            self.index += 1
        chunk = self._encode_chunk(chunk)
        if not isinstance(chunk, bytes):
            chunk = chunk.encode()
        return chunk

    def pop_current_chunk(self, amt=-1, till_crlf=False):
        if amt > 0 and till_crlf:
            raise ValueError("Can't specify amt and till_crlf.")
        if len(self.cur_chunk) <= 0:
            self.cur_chunk = self._pop_new_chunk()
        if till_crlf:
            try:
                i = self.cur_chunk.index(b"\r\n")
            except ValueError:
                # No CRLF in current chunk -- probably caused by encoder.
                self.cur_chunk = b""
                return b""
            else:
                chunk_part = self.cur_chunk[: i + 2]
                self.cur_chunk = self.cur_chunk[i + 2 :]
                return chunk_part
        elif amt <= -1:
            chunk_part = self.cur_chunk
            self.cur_chunk = b""
            return chunk_part
        else:
            try:
                chunk_part = self.cur_chunk[:amt]
            except IndexError:
                chunk_part = self.cur_chunk
                self.cur_chunk = b""
            else:
                self.cur_chunk = self.cur_chunk[amt:]
            return chunk_part

    def readline(self):
        return self.pop_current_chunk(till_crlf=True)

    def read(self, amt=-1):
        return self.pop_current_chunk(amt)

    def flush(self):
        # Python 3 wants this method.
        pass

    def close(self):
        self.closed = True


class MockChunkedIncompleteRead(MockChunkedEncodingResponse):
    def _encode_chunk(self, chunk):
        return "9999\r\n%s\r\n" % chunk.decode()


class MockChunkedInvalidChunkLength(MockChunkedEncodingResponse):
    BAD_LENGTH_LINE = "ZZZ\r\n"

    def _encode_chunk(self, chunk):
        return "%s%s\r\n" % (self.BAD_LENGTH_LINE, chunk.decode())


class MockChunkedEncodingWithoutCRLFOnEnd(MockChunkedEncodingResponse):
    def _encode_chunk(self, chunk):
        return "%X\r\n%s%s" % (
            len(chunk),
            chunk.decode(),
            "\r\n" if len(chunk) > 0 else "",
        )


class MockChunkedEncodingWithExtensions(MockChunkedEncodingResponse):
    def _encode_chunk(self, chunk):
        return "%X;asd=qwe\r\n%s\r\n" % (len(chunk), chunk.decode())


class MockSock(object):
    @classmethod
    def makefile(cls, *args, **kwargs):
        return
