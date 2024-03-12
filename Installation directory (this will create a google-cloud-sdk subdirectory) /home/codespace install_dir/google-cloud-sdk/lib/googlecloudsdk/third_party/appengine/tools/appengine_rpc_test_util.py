# Copyright 2016 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for testing code that uses appengine_rpc's *RpcServer."""

from __future__ import absolute_import


import io
import logging

from googlecloudsdk.third_party.appengine.tools.appengine_rpc import AbstractRpcServer
from googlecloudsdk.third_party.appengine.tools.appengine_rpc import HttpRpcServer
from googlecloudsdk.third_party.appengine._internal import six_subset

# pylint:disable=g-import-not-at-top
# pylint:disable=invalid-name
# Inline these directly rather than placing in six_subset since importing
# urllib into six_subset seems to mess with the overridden version of
# urllib/httplib that the NaCl runtime sandbox inserts for SSL purposes.
if six_subset.PY3:
  import urllib.error
  HTTPError = urllib.error.HTTPError
else:
  import urllib2
  HTTPError = urllib2.HTTPError
# pylint:disable=g-import-not-at-top
# pylint:disable=invalid-name


class TestRpcServerMixin(object):
  """Provides a mocked-out version of HttpRpcServer for testing purposes."""

  def set_strict(self, strict=True):
    """Enables strict mode."""
    self.opener.set_strict(strict)

  def set_save_request_data(self, save_request_data=True):
    """Enables saving request data for every request."""
    self.opener.set_save_request_data(save_request_data)

  def _GetOpener(self):
    """Returns a MockOpener.

    Returns:
      A MockOpener object.
    """
    return TestRpcServerMixin.MockOpener()

  class MockResponse(object):
    """A mocked out response object for testing purposes."""

    def __init__(self, body, code=200, headers=None):
      """Creates a new MockResponse.

      Args:
        body: The text of the body to return.
        code: The response code (default 200).
        headers: An optional header dictionary.
      """
      self.fp = io.BytesIO(body)
      self.code = code
      self.headers = headers
      self.msg = ""

      if self.headers is None:
        self.headers = {}

    def info(self):
      return self.headers

    def read(self, length=-1):
      """Reads from the response body.

      Args:
        length: The number of bytes to read.

      Returns:
        The body of the response.
      """
      return self.fp.read(length)

    def readline(self):
      """Reads a line from the response body.

      Returns:
        A line of text from the response body.
      """
      return self.fp.readline()

    def close(self):
      """Closes the response stream."""
      self.fp.close()

  class MockOpener(object):
    """A mocked-out OpenerDirector for testing purposes."""

    def __init__(self):
      """Creates a new MockOpener."""
      self.request_data = []
      self.requests = []
      self.responses = {}
      self.ordered_responses = {}
      self.cookie = None
      self.strict = False
      self.save_request_data = False

    def set_strict(self, strict=True):
      """Enables strict mode."""
      self.strict = strict

    def set_save_request_data(self, save_request_data=True):
      """Enables saving request data for every request."""
      self.save_request_data = save_request_data

    def open(self, request):
      """Logs the request and returns a MockResponse object."""
      full_url = request.get_full_url()
      if "?" in full_url:
        url = full_url[:full_url.find("?")]
      else:
        url = full_url
      if (url != "https://www.google.com/accounts/ClientLogin"
          and not url.endswith("_ah/login")):
        assert "X-appcfg-api-version" in request.headers
        assert "User-agent" in request.headers
      request_data = (full_url, bool(request.data))
      self.requests.append(request_data)
      if self.save_request_data:
        self.request_data.append((full_url, request.data))

      if self.cookie:
        request.headers["Cookie"] = self.cookie
        response = self.responses[url](request)

      # Use ordered responses in preference to specific response to generic 200.
      if url in self.ordered_responses:
        logging.debug("Using ordered pre-canned response for: %s" % full_url)
        response = self.ordered_responses[url].pop(0)(request)
        if not self.ordered_responses[url]:
          self.ordered_responses.pop(url)
      elif url in self.responses:
        logging.debug("Using pre-canned response for: %s" % full_url)
        response = self.responses[url](request)
      elif self.strict:
        raise Exception('No response found for url: %s (%s)' % (url, full_url))
      else:
        logging.debug("Using generic blank response for: %s" % full_url)
        response = TestRpcServerMixin.MockResponse(b"")
      if "Set-Cookie" in response.headers:
        self.cookie = response.headers["Set-Cookie"]

      # Handle error status codes in the same way as the appengine_rpc openers.
      # urllib2 will raise HTTPError for non-2XX status codes, per RFC 2616.
      if not (200 <= response.code < 300):
        code, msg, hdrs = response.code, response.msg, response.info()
        fp = io.BytesIO(response.read())
        raise HTTPError(url=url, code=code, msg=None, hdrs=hdrs, fp=fp)
      return response

    def AddResponse(self, url, response_func):
      """Calls the provided function when the provided URL is requested.

      The provided function should accept a request object and return a
      response object.

      Args:
        url: The URL to trigger on.
        response_func: The function to call when the url is requested.
      """
      self.responses[url] = response_func

    def AddOrderedResponse(self, url, response_func):
      """Calls the provided function when the provided URL is requested.

      The provided functions should accept a request object and return a
      response object.  This response will be added after previously given
      responses if they exist.

      Args:
        url: The URL to trigger on.
        response_func: The function to call when the url is requested.
      """
      if url not in self.ordered_responses:
        self.ordered_responses[url] = []
      self.ordered_responses[url].append(response_func)

    def AddOrderedResponses(self, url, response_funcs):
      """Calls the provided function when the provided URL is requested.

      The provided functions should accept a request object and return a
      response object. Each response will be called once.

      Args:
        url: The URL to trigger on.
        response_funcs: A list of response functions.
      """
      self.ordered_responses[url] = response_funcs


class TestRpcServer(TestRpcServerMixin, AbstractRpcServer):
  pass


class TestHttpRpcServer(TestRpcServerMixin, HttpRpcServer):
  pass


class UrlLibRequestResponseStub(object):
  def __init__(self, headers=None):
    self.headers = {}
    if headers:
      self.headers = headers

  def add_header(self, header, value):
    # Note that this does not preserve header order.
    # If that's a problem for your tests, add some functionality :)
    self.headers[header] = value


class UrlLibRequestStub(UrlLibRequestResponseStub):
  pass


class UrlLibResponseStub(UrlLibRequestResponseStub, io.BytesIO):
  def __init__(self, body, headers, url, code, msg):
    UrlLibRequestResponseStub.__init__(self, headers)
    if body:
      io.BytesIO.__init__(self, body)
    else:
      io.BytesIO.__init__(self, b"")
    self.url = url
    self.code = code
    self.msg = msg
