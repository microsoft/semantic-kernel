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

"""Tests for http_wrapper."""
import socket
import unittest

import httplib2
from six.moves import http_client

from mock import patch

from apitools.base.py import exceptions
from apitools.base.py import http_wrapper

# pylint: disable=ungrouped-imports
try:
    from oauth2client.client import HttpAccessTokenRefreshError
    from oauth2client.client import AccessTokenRefreshError
    _TOKEN_REFRESH_STATUS_AVAILABLE = True
except ImportError:
    from oauth2client.client import AccessTokenRefreshError
    _TOKEN_REFRESH_STATUS_AVAILABLE = False


class _MockHttpRequest(object):

    url = None


class _MockHttpResponse(object):

    def __init__(self, status_code):
        self.response = {'status': status_code}


class RaisesExceptionOnLen(object):

    """Supports length property but raises if __len__ is used."""

    def __len__(self):
        raise Exception('len() called unnecessarily')

    def length(self):
        return 1


class HttpWrapperTest(unittest.TestCase):

    def testRequestBodyUsesLengthProperty(self):
        http_wrapper.Request(body=RaisesExceptionOnLen())

    def testRequestBodyWithLen(self):
        http_wrapper.Request(body='burrito')

    @unittest.skipIf(not _TOKEN_REFRESH_STATUS_AVAILABLE,
                     'oauth2client<1.5 lacks HttpAccessTokenRefreshError.')
    def testExceptionHandlerHttpAccessTokenError(self):
        exception_arg = HttpAccessTokenRefreshError(status=503)
        retry_args = http_wrapper.ExceptionRetryArgs(
            http={'connections': {}}, http_request=_MockHttpRequest(),
            exc=exception_arg, num_retries=0, max_retry_wait=0,
            total_wait_sec=0)

        # Disable time.sleep for this handler as it is called with
        # a minimum value of 1 second.
        with patch('time.sleep', return_value=None):
            http_wrapper.HandleExceptionsAndRebuildHttpConnections(
                retry_args)

    @unittest.skipIf(not _TOKEN_REFRESH_STATUS_AVAILABLE,
                     'oauth2client<1.5 lacks HttpAccessTokenRefreshError.')
    def testExceptionHandlerHttpAccessTokenErrorRaises(self):
        exception_arg = HttpAccessTokenRefreshError(status=200)
        retry_args = http_wrapper.ExceptionRetryArgs(
            http={'connections': {}}, http_request=_MockHttpRequest(),
            exc=exception_arg, num_retries=0, max_retry_wait=0,
            total_wait_sec=0)

        # Disable time.sleep for this handler as it is called with
        # a minimum value of 1 second.
        with self.assertRaises(HttpAccessTokenRefreshError):
            with patch('time.sleep', return_value=None):
                http_wrapper.HandleExceptionsAndRebuildHttpConnections(
                    retry_args)

    def testExceptionHandlerAccessTokenErrorRaises(self):
        exception_arg = AccessTokenRefreshError()
        retry_args = http_wrapper.ExceptionRetryArgs(
            http={'connections': {}}, http_request=_MockHttpRequest(),
            exc=exception_arg, num_retries=0, max_retry_wait=0,
            total_wait_sec=0)

        # Disable time.sleep for this handler as it is called with
        # a minimum value of 1 second.
        with self.assertRaises(AccessTokenRefreshError):
            with patch('time.sleep', return_value=None):
                http_wrapper.HandleExceptionsAndRebuildHttpConnections(
                    retry_args)

    def testDefaultExceptionHandler(self):
        """Ensures exception handles swallows (retries)"""
        mock_http_content = 'content'.encode('utf8')
        for exception_arg in (
                http_client.BadStatusLine('line'),
                http_client.IncompleteRead('partial'),
                http_client.ResponseNotReady(),
                socket.error(),
                socket.gaierror(),
                httplib2.ServerNotFoundError(),
                ValueError(),
                exceptions.RequestError(),
                exceptions.BadStatusCodeError(
                    {'status': 503}, mock_http_content, 'url'),
                exceptions.RetryAfterError(
                    {'status': 429}, mock_http_content, 'url', 0)):

            retry_args = http_wrapper.ExceptionRetryArgs(
                http={'connections': {}}, http_request=_MockHttpRequest(),
                exc=exception_arg, num_retries=0, max_retry_wait=0,
                total_wait_sec=0)

            # Disable time.sleep for this handler as it is called with
            # a minimum value of 1 second.
            with patch('time.sleep', return_value=None):
                http_wrapper.HandleExceptionsAndRebuildHttpConnections(
                    retry_args)
