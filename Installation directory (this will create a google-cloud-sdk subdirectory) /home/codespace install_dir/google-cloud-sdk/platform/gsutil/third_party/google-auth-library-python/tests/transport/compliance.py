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

import time

import flask  # type: ignore
import pytest  # type: ignore
from pytest_localserver.http import WSGIServer  # type: ignore
from six.moves import http_client

from google.auth import exceptions

# .invalid will never resolve, see https://tools.ietf.org/html/rfc2606
NXDOMAIN = "test.invalid"


class RequestResponseTests(object):
    @pytest.fixture(scope="module")
    def server(self):
        """Provides a test HTTP server.

        The test server is automatically created before
        a test and destroyed at the end. The server is serving a test
        application that can be used to verify requests.
        """
        app = flask.Flask(__name__)
        app.debug = True

        # pylint: disable=unused-variable
        # (pylint thinks the flask routes are unusued.)
        @app.route("/basic")
        def index():
            header_value = flask.request.headers.get("x-test-header", "value")
            headers = {"X-Test-Header": header_value}
            return "Basic Content", http_client.OK, headers

        @app.route("/server_error")
        def server_error():
            return "Error", http_client.INTERNAL_SERVER_ERROR

        @app.route("/wait")
        def wait():
            time.sleep(3)
            return "Waited"

        # pylint: enable=unused-variable

        server = WSGIServer(application=app.wsgi_app)
        server.start()
        yield server
        server.stop()

    def test_request_basic(self, server):
        request = self.make_request()
        response = request(url=server.url + "/basic", method="GET")

        assert response.status == http_client.OK
        assert response.headers["x-test-header"] == "value"
        assert response.data == b"Basic Content"

    def test_request_with_timeout_success(self, server):
        request = self.make_request()
        response = request(url=server.url + "/basic", method="GET", timeout=2)

        assert response.status == http_client.OK
        assert response.headers["x-test-header"] == "value"
        assert response.data == b"Basic Content"

    def test_request_with_timeout_failure(self, server):
        request = self.make_request()

        with pytest.raises(exceptions.TransportError):
            request(url=server.url + "/wait", method="GET", timeout=1)

    def test_request_headers(self, server):
        request = self.make_request()
        response = request(
            url=server.url + "/basic",
            method="GET",
            headers={"x-test-header": "hello world"},
        )

        assert response.status == http_client.OK
        assert response.headers["x-test-header"] == "hello world"
        assert response.data == b"Basic Content"

    def test_request_error(self, server):
        request = self.make_request()
        response = request(url=server.url + "/server_error", method="GET")

        assert response.status == http_client.INTERNAL_SERVER_ERROR
        assert response.data == b"Error"

    def test_connection_error(self):
        request = self.make_request()
        with pytest.raises(exceptions.TransportError):
            request(url="http://{}".format(NXDOMAIN), method="GET")
