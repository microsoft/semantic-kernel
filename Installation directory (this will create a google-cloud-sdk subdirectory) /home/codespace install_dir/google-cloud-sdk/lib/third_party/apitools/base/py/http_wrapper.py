#!/usr/bin/env python
#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""HTTP wrapper for apitools.

This library wraps the underlying http library we use, which is
currently httplib2.
"""

import collections
import contextlib
import logging
import socket
import time

import httplib2
import six
from six.moves import http_client
from six.moves.urllib import parse

from apitools.base.py import exceptions
from apitools.base.py import util

# pylint: disable=ungrouped-imports
try:
    from oauth2client.client import HttpAccessTokenRefreshError as TokenRefreshError  # noqa
except ImportError:
    from oauth2client.client import AccessTokenRefreshError as TokenRefreshError  # noqa

__all__ = [
    'CheckResponse',
    'GetHttp',
    'HandleExceptionsAndRebuildHttpConnections',
    'MakeRequest',
    'RebuildHttpConnections',
    'Request',
    'Response',
    'RethrowExceptionHandler',
]


# 308 and 429 don't have names in httplib.
RESUME_INCOMPLETE = 308
TOO_MANY_REQUESTS = 429
_REDIRECT_STATUS_CODES = (
    http_client.MOVED_PERMANENTLY,
    http_client.FOUND,
    http_client.SEE_OTHER,
    http_client.TEMPORARY_REDIRECT,
    RESUME_INCOMPLETE,
)

# http: An httplib2.Http instance.
# http_request: A http_wrapper.Request.
# exc: Exception being raised.
# num_retries: Number of retries consumed; used for exponential backoff.
ExceptionRetryArgs = collections.namedtuple(
    'ExceptionRetryArgs', ['http', 'http_request', 'exc', 'num_retries',
                           'max_retry_wait', 'total_wait_sec'])


@contextlib.contextmanager
def _Httplib2Debuglevel(http_request, level, http=None):
    """Temporarily change the value of httplib2.debuglevel, if necessary.

    If http_request has a `loggable_body` distinct from `body`, then we
    need to prevent httplib2 from logging the full body. This sets
    httplib2.debuglevel for the duration of the `with` block; however,
    that alone won't change the value of existing HTTP connections. If
    an httplib2.Http object is provided, we'll also change the level on
    any cached connections attached to it.

    Args:
      http_request: a Request we're logging.
      level: (int) the debuglevel for logging.
      http: (optional) an httplib2.Http whose connections we should
        set the debuglevel on.

    Yields:
      None.
    """
    if http_request.loggable_body is None:
        yield
        return
    old_level = httplib2.debuglevel
    http_levels = {}
    httplib2.debuglevel = level
    if http is not None:
        for connection_key, connection in http.connections.items():
            # httplib2 stores two kinds of values in this dict, connection
            # classes and instances. Since the connection types are all
            # old-style classes, we can't easily distinguish by connection
            # type -- so instead we use the key pattern.
            if ':' not in connection_key:
                continue
            http_levels[connection_key] = connection.debuglevel
            connection.set_debuglevel(level)
    yield
    httplib2.debuglevel = old_level
    if http is not None:
        for connection_key, old_level in http_levels.items():
            if connection_key in http.connections:
                http.connections[connection_key].set_debuglevel(old_level)


class Request(object):

    """Class encapsulating the data for an HTTP request."""

    def __init__(self, url='', http_method='GET', headers=None, body=''):
        self.url = url
        self.http_method = http_method
        self.headers = headers or {}
        self.__body = None
        self.__loggable_body = None
        self.body = body

    @property
    def loggable_body(self):
        return self.__loggable_body

    @loggable_body.setter
    def loggable_body(self, value):
        if self.body is None:
            raise exceptions.RequestError(
                'Cannot set loggable body on request with no body')
        self.__loggable_body = value

    @property
    def body(self):
        return self.__body

    @body.setter
    def body(self, value):
        """Sets the request body; handles logging and length measurement."""
        self.__body = value
        if value is not None:
            # Avoid calling len() which cannot exceed 4GiB in 32-bit python.
            body_length = getattr(
                self.__body, 'length', None) or len(self.__body)
            self.headers['content-length'] = str(body_length)
        else:
            self.headers.pop('content-length', None)
        # This line ensures we don't try to print large requests.
        if not isinstance(value, (type(None), six.string_types)):
            self.loggable_body = '<media body>'


# Note: currently the order of fields here is important, since we want
# to be able to pass in the result from httplib2.request.
class Response(collections.namedtuple(
        'HttpResponse', ['info', 'content', 'request_url'])):

    """Class encapsulating data for an HTTP response."""
    __slots__ = ()

    def __len__(self):
        return self.length

    @property
    def length(self):
        """Return the length of this response.

        We expose this as an attribute since using len() directly can fail
        for responses larger than sys.maxint.

        Returns:
          Response length (as int or long)
        """
        def ProcessContentRange(content_range):
            _, _, range_spec = content_range.partition(' ')
            byte_range, _, _ = range_spec.partition('/')
            start, _, end = byte_range.partition('-')
            return int(end) - int(start) + 1

        if '-content-encoding' in self.info and 'content-range' in self.info:
            # httplib2 rewrites content-length in the case of a compressed
            # transfer; we can't trust the content-length header in that
            # case, but we *can* trust content-range, if it's present.
            return ProcessContentRange(self.info['content-range'])
        elif 'content-length' in self.info:
            return int(self.info.get('content-length'))
        elif 'content-range' in self.info:
            return ProcessContentRange(self.info['content-range'])
        return len(self.content)

    @property
    def status_code(self):
        return int(self.info['status'])

    @property
    def retry_after(self):
        if 'retry-after' in self.info:
            return int(self.info['retry-after'])

    @property
    def is_redirect(self):
        return (self.status_code in _REDIRECT_STATUS_CODES and
                'location' in self.info)


def CheckResponse(response):
    if response is None:
        # Caller shouldn't call us if the response is None, but handle anyway.
        raise exceptions.RequestError(
            'Request to url %s did not return a response.' %
            response.request_url)
    elif (response.status_code >= 500 or
          response.status_code == TOO_MANY_REQUESTS):
        raise exceptions.BadStatusCodeError.FromResponse(response)
    elif response.retry_after:
        raise exceptions.RetryAfterError.FromResponse(response)


def RebuildHttpConnections(http):
    """Rebuilds all http connections in the httplib2.Http instance.

    httplib2 overloads the map in http.connections to contain two different
    types of values:
    { scheme string:  connection class } and
    { scheme + authority string : actual http connection }
    Here we remove all of the entries for actual connections so that on the
    next request httplib2 will rebuild them from the connection types.

    Args:
      http: An httplib2.Http instance.
    """
    if getattr(http, 'connections', None):
        for conn_key in list(http.connections.keys()):
            if ':' in conn_key:
                del http.connections[conn_key]


def RethrowExceptionHandler(*unused_args):
    # pylint: disable=misplaced-bare-raise
    raise


def HandleExceptionsAndRebuildHttpConnections(retry_args):
    """Exception handler for http failures.

    This catches known failures and rebuilds the underlying HTTP connections.

    Args:
      retry_args: An ExceptionRetryArgs tuple.
    """
    # If the server indicates how long to wait, use that value.  Otherwise,
    # calculate the wait time on our own.
    retry_after = None

    # Transport failures
    if isinstance(retry_args.exc, (http_client.BadStatusLine,
                                   http_client.IncompleteRead,
                                   http_client.ResponseNotReady)):
        logging.debug('Caught HTTP error %s, retrying: %s',
                      type(retry_args.exc).__name__, retry_args.exc)
    elif isinstance(retry_args.exc, socket.error):
        logging.debug('Caught socket error, retrying: %s', retry_args.exc)
    elif isinstance(retry_args.exc, socket.gaierror):
        logging.debug(
            'Caught socket address error, retrying: %s', retry_args.exc)
    elif isinstance(retry_args.exc, socket.timeout):
        logging.debug(
            'Caught socket timeout error, retrying: %s', retry_args.exc)
    elif isinstance(retry_args.exc, httplib2.ServerNotFoundError):
        logging.debug(
            'Caught server not found error, retrying: %s', retry_args.exc)
    elif isinstance(retry_args.exc, ValueError):
        # oauth2client tries to JSON-decode the response, which can result
        # in a ValueError if the response was invalid. Until that is fixed in
        # oauth2client, need to handle it here.
        logging.debug('Response content was invalid (%s), retrying',
                      retry_args.exc)
    elif (isinstance(retry_args.exc, TokenRefreshError) and
          hasattr(retry_args.exc, 'status') and
          (retry_args.exc.status == TOO_MANY_REQUESTS or
           retry_args.exc.status >= 500)):
        logging.debug(
            'Caught transient credential refresh error (%s), retrying',
            retry_args.exc)
    elif isinstance(retry_args.exc, exceptions.RequestError):
        logging.debug('Request returned no response, retrying')
    # API-level failures
    elif isinstance(retry_args.exc, exceptions.BadStatusCodeError):
        logging.debug('Response returned status %s, retrying',
                      retry_args.exc.status_code)
    elif isinstance(retry_args.exc, exceptions.RetryAfterError):
        logging.debug('Response returned a retry-after header, retrying')
        retry_after = retry_args.exc.retry_after
    else:
        raise retry_args.exc
    RebuildHttpConnections(retry_args.http)
    logging.debug('Retrying request to url %s after exception %s',
                  retry_args.http_request.url, retry_args.exc)
    time.sleep(
        retry_after or util.CalculateWaitForRetry(
            retry_args.num_retries, max_wait=retry_args.max_retry_wait))


def MakeRequest(http, http_request, retries=7, max_retry_wait=60,
                redirections=5,
                retry_func=HandleExceptionsAndRebuildHttpConnections,
                check_response_func=CheckResponse):
    """Send http_request via the given http, performing error/retry handling.

    Args:
      http: An httplib2.Http instance, or a http multiplexer that delegates to
          an underlying http, for example, HTTPMultiplexer.
      http_request: A Request to send.
      retries: (int, default 7) Number of retries to attempt on retryable
          replies (such as 429 or 5XX).
      max_retry_wait: (int, default 60) Maximum number of seconds to wait
          when retrying.
      redirections: (int, default 5) Number of redirects to follow.
      retry_func: Function to handle retries on exceptions. Argument is an
          ExceptionRetryArgs tuple.
      check_response_func: Function to validate the HTTP response.
          Arguments are (Response, response content, url).

    Raises:
      InvalidDataFromServerError: if there is no response after retries.

    Returns:
      A Response object.

    """
    retry = 0
    first_req_time = time.time()
    # Provide compatibility for breaking change in httplib2 0.16.0+:
    # https://github.com/googleapis/google-api-python-client/issues/803
    if hasattr(http, 'redirect_codes'):
        http.redirect_codes = set(http.redirect_codes) - {308}
    while True:
        try:
            return _MakeRequestNoRetry(
                http, http_request, redirections=redirections,
                check_response_func=check_response_func)
        # retry_func will consume the exception types it handles and raise.
        # pylint: disable=broad-except
        except Exception as e:
            retry += 1
            if retry >= retries:
                raise
            else:
                total_wait_sec = time.time() - first_req_time
                retry_func(ExceptionRetryArgs(http, http_request, e, retry,
                                              max_retry_wait, total_wait_sec))


def _MakeRequestNoRetry(http, http_request, redirections=5,
                        check_response_func=CheckResponse):
    """Send http_request via the given http.

    This wrapper exists to handle translation between the plain httplib2
    request/response types and the Request and Response types above.

    Args:
      http: An httplib2.Http instance, or a http multiplexer that delegates to
          an underlying http, for example, HTTPMultiplexer.
      http_request: A Request to send.
      redirections: (int, default 5) Number of redirects to follow.
      check_response_func: Function to validate the HTTP response.
          Arguments are (Response, response content, url).

    Returns:
      A Response object.

    Raises:
      RequestError if no response could be parsed.

    """
    connection_type = None
    # Handle overrides for connection types.  This is used if the caller
    # wants control over the underlying connection for managing callbacks
    # or hash digestion.
    if getattr(http, 'connections', None):
        url_scheme = parse.urlsplit(http_request.url).scheme
        if url_scheme and url_scheme in http.connections:
            connection_type = http.connections[url_scheme]

    # Custom printing only at debuglevel 4
    new_debuglevel = 4 if httplib2.debuglevel == 4 else 0
    with _Httplib2Debuglevel(http_request, new_debuglevel, http=http):
        info, content = http.request(
            str(http_request.url), method=str(http_request.http_method),
            body=http_request.body, headers=http_request.headers,
            redirections=redirections, connection_type=connection_type)

    if info is None:
        raise exceptions.RequestError()

    response = Response(info, content, http_request.url)
    check_response_func(response)
    return response


_HTTP_FACTORIES = []


def _RegisterHttpFactory(factory):
    _HTTP_FACTORIES.append(factory)


def GetHttp(**kwds):
    for factory in _HTTP_FACTORIES:
        http = factory(**kwds)
        if http is not None:
            return http
    return httplib2.Http(**kwds)
