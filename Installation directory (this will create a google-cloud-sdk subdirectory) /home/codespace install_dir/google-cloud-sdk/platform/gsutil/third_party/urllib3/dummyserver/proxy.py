#!/usr/bin/env python
#
# Simple asynchronous HTTP proxy with tunnelling (CONNECT).
#
# GET/POST proxying based on
# http://groups.google.com/group/python-tornado/msg/7bea08e7a049cf26
#
# Copyright (C) 2012 Senko Rasic <senko.rasic@dobarkod.hr>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import socket
import ssl
import sys

import tornado.gen
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web

__all__ = ["ProxyHandler", "run_proxy"]


class ProxyHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ["GET", "POST", "CONNECT"]

    @tornado.gen.coroutine
    def get(self):
        def handle_response(response):
            if response.error and not isinstance(
                response.error, tornado.httpclient.HTTPError
            ):
                self.set_status(500)
                self.write("Internal server error:\n" + str(response.error))
                self.finish()
            else:
                self.set_status(response.code)
                for header in (
                    "Date",
                    "Cache-Control",
                    "Server",
                    "Content-Type",
                    "Location",
                ):
                    v = response.headers.get(header)
                    if v:
                        self.set_header(header, v)
                if response.body:
                    self.write(response.body)
                self.finish()

        upstream_ca_certs = self.application.settings.get("upstream_ca_certs", None)
        ssl_options = None

        if upstream_ca_certs:
            ssl_options = ssl.create_default_context(cafile=upstream_ca_certs)

        req = tornado.httpclient.HTTPRequest(
            url=self.request.uri,
            method=self.request.method,
            body=self.request.body,
            headers=self.request.headers,
            follow_redirects=False,
            allow_nonstandard_methods=True,
            ssl_options=ssl_options,
        )

        client = tornado.httpclient.AsyncHTTPClient()
        try:
            response = yield client.fetch(req)
            yield handle_response(response)
        except tornado.httpclient.HTTPError as e:
            if hasattr(e, "response") and e.response:
                yield handle_response(e.response)
            else:
                self.set_status(500)
                self.write("Internal server error:\n" + str(e))
                self.finish()

    @tornado.gen.coroutine
    def post(self):
        yield self.get()

    @tornado.gen.coroutine
    def connect(self):
        host, port = self.request.uri.split(":")
        client = self.request.connection.stream

        @tornado.gen.coroutine
        def start_forward(reader, writer):
            while True:
                try:
                    data = yield reader.read_bytes(4096, partial=True)
                except tornado.iostream.StreamClosedError:
                    break
                if not data:
                    break
                writer.write(data)
            writer.close()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        upstream = tornado.iostream.IOStream(s)
        yield upstream.connect((host, int(port)))

        client.write(b"HTTP/1.0 200 Connection established\r\n\r\n")
        fu1 = start_forward(client, upstream)
        fu2 = start_forward(upstream, client)
        yield [fu1, fu2]


def run_proxy(port, start_ioloop=True):
    """
    Run proxy on the specified port. If start_ioloop is True (default),
    the tornado IOLoop will be started immediately.
    """
    app = tornado.web.Application([(r".*", ProxyHandler)])
    app.listen(port)
    ioloop = tornado.ioloop.IOLoop.instance()
    if start_ioloop:
        ioloop.start()


if __name__ == "__main__":
    port = 8888
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print("Starting HTTP proxy on port %d" % port)
    run_proxy(port)
