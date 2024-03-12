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

"""Library for handling batch HTTP requests for apitools."""

import collections
import email.generator as generator
import email.mime.multipart as mime_multipart
import email.mime.nonmultipart as mime_nonmultipart
import email.parser as email_parser
import itertools
import time
import uuid

import six
from six.moves import http_client
from six.moves import urllib_parse
from six.moves import range  # pylint: disable=redefined-builtin

from apitools.base.py import exceptions
from apitools.base.py import http_wrapper

__all__ = [
    'BatchApiRequest',
]


class RequestResponseAndHandler(collections.namedtuple(
        'RequestResponseAndHandler', ['request', 'response', 'handler'])):

    """Container for data related to completing an HTTP request.

    This contains an HTTP request, its response, and a callback for handling
    the response from the server.

    Attributes:
      request: An http_wrapper.Request object representing the HTTP request.
      response: The http_wrapper.Response object returned from the server.
      handler: A callback function accepting two arguments, response
        and exception. Response is an http_wrapper.Response object, and
        exception is an apiclient.errors.HttpError object if an error
        occurred, or otherwise None.
    """


class BatchApiRequest(object):
    """Batches multiple api requests into a single request."""

    class ApiCall(object):

        """Holds request and response information for each request.

        ApiCalls are ultimately exposed to the client once the HTTP
        batch request has been completed.

        Attributes:
          http_request: A client-supplied http_wrapper.Request to be
              submitted to the server.
          response: A http_wrapper.Response object given by the server as a
              response to the user request, or None if an error occurred.
          exception: An apiclient.errors.HttpError object if an error
              occurred, or None.

        """

        def __init__(self, request, retryable_codes, service, method_config):
            """Initialize an individual API request.

            Args:
              request: An http_wrapper.Request object.
              retryable_codes: A list of integer HTTP codes that can
                  be retried.
              service: A service inheriting from base_api.BaseApiService.
              method_config: Method config for the desired API request.

            """
            self.__retryable_codes = list(
                set(retryable_codes + [http_client.UNAUTHORIZED]))
            self.__http_response = None
            self.__service = service
            self.__method_config = method_config

            self.http_request = request
            # TODO(user): Add some validation to these fields.
            self.__response = None
            self.__exception = None

        @property
        def is_error(self):
            return self.exception is not None

        @property
        def response(self):
            return self.__response

        @property
        def exception(self):
            return self.__exception

        @property
        def authorization_failed(self):
            return (self.__http_response and (
                self.__http_response.status_code == http_client.UNAUTHORIZED))

        @property
        def terminal_state(self):
            if self.__http_response is None:
                return False
            response_code = self.__http_response.status_code
            return response_code not in self.__retryable_codes

        def HandleResponse(self, http_response, exception):
            """Handles incoming http response to the request in http_request.

            This is intended to be used as a callback function for
            BatchHttpRequest.Add.

            Args:
              http_response: Deserialized http_wrapper.Response object.
              exception: apiclient.errors.HttpError object if an error
                  occurred.

            """
            self.__http_response = http_response
            self.__exception = exception
            if self.terminal_state and not self.__exception:
                self.__response = self.__service.ProcessHttpResponse(
                    self.__method_config, self.__http_response)

    def __init__(self, batch_url=None, retryable_codes=None,
                 response_encoding=None):
        """Initialize a batch API request object.

        Args:
          batch_url: Base URL for batch API calls.
          retryable_codes: A list of integer HTTP codes that can be retried.
          response_encoding: The encoding type of response content.
        """
        self.api_requests = []
        self.retryable_codes = retryable_codes or []
        self.batch_url = batch_url or 'https://www.googleapis.com/batch'
        self.response_encoding = response_encoding

    def Add(self, service, method, request, global_params=None):
        """Add a request to the batch.

        Args:
          service: A class inheriting base_api.BaseApiService.
          method: A string indicated desired method from the service. See
              the example in the class docstring.
          request: An input message appropriate for the specified
              service.method.
          global_params: Optional additional parameters to pass into
              method.PrepareHttpRequest.

        Returns:
          None

        """
        # Retrieve the configs for the desired method and service.
        method_config = service.GetMethodConfig(method)
        upload_config = service.GetUploadConfig(method)

        # Prepare the HTTP Request.
        http_request = service.PrepareHttpRequest(
            method_config, request, global_params=global_params,
            upload_config=upload_config)

        # Create the request and add it to our master list.
        api_request = self.ApiCall(
            http_request, self.retryable_codes, service, method_config)
        self.api_requests.append(api_request)

    def Execute(self, http, sleep_between_polls=5, max_retries=5,
                max_batch_size=None, batch_request_callback=None):
        """Execute all of the requests in the batch.

        Args:
          http: httplib2.Http object for use in the request.
          sleep_between_polls: Integer number of seconds to sleep between
              polls.
          max_retries: Max retries. Any requests that have not succeeded by
              this number of retries simply report the last response or
              exception, whatever it happened to be.
          max_batch_size: int, if specified requests will be split in batches
              of given size.
          batch_request_callback: function of (http_response, exception) passed
              to BatchHttpRequest which will be run on any given results.

        Returns:
          List of ApiCalls.
        """
        requests = [request for request in self.api_requests
                    if not request.terminal_state]
        batch_size = max_batch_size or len(requests)

        for attempt in range(max_retries):
            if attempt:
                time.sleep(sleep_between_polls)

            for i in range(0, len(requests), batch_size):
                # Create a batch_http_request object and populate it with
                # incomplete requests.
                batch_http_request = BatchHttpRequest(
                    batch_url=self.batch_url,
                    callback=batch_request_callback,
                    response_encoding=self.response_encoding
                )
                for request in itertools.islice(requests,
                                                i, i + batch_size):
                    batch_http_request.Add(
                        request.http_request, request.HandleResponse)
                batch_http_request.Execute(http)

                if hasattr(http.request, 'credentials'):
                    if any(request.authorization_failed
                           for request in itertools.islice(requests,
                                                           i, i + batch_size)):
                        http.request.credentials.refresh(http)

            # Collect retryable requests.
            requests = [request for request in self.api_requests if not
                        request.terminal_state]
            if not requests:
                break

        return self.api_requests


class BatchHttpRequest(object):

    """Batches multiple http_wrapper.Request objects into a single request."""

    def __init__(self, batch_url, callback=None, response_encoding=None):
        """Constructor for a BatchHttpRequest.

        Args:
          batch_url: URL to send batch requests to.
          callback: A callback to be called for each response, of the
              form callback(response, exception). The first parameter is
              the deserialized Response object. The second is an
              apiclient.errors.HttpError exception object if an HTTP error
              occurred while processing the request, or None if no error
              occurred.
          response_encoding: The encoding type of response content.
        """
        # Endpoint to which these requests are sent.
        self.__batch_url = batch_url

        # Global callback to be called for each individual response in the
        # batch.
        self.__callback = callback

        # Response content will be decoded if this is provided.
        self.__response_encoding = response_encoding

        # List of requests, responses and handlers.
        self.__request_response_handlers = {}

        # The last auto generated id.
        self.__last_auto_id = itertools.count()

        # Unique ID on which to base the Content-ID headers.
        self.__base_id = uuid.uuid4()

    def _ConvertIdToHeader(self, request_id):
        """Convert an id to a Content-ID header value.

        Args:
          request_id: String identifier for a individual request.

        Returns:
          A Content-ID header with the id_ encoded into it. A UUID is
          prepended to the value because Content-ID headers are
          supposed to be universally unique.

        """
        return '<%s+%s>' % (self.__base_id, urllib_parse.quote(request_id))

    @staticmethod
    def _ConvertHeaderToId(header):
        """Convert a Content-ID header value to an id.

        Presumes the Content-ID header conforms to the format that
        _ConvertIdToHeader() returns.

        Args:
          header: A string indicating the Content-ID header value.

        Returns:
          The extracted id value.

        Raises:
          BatchError if the header is not in the expected format.
        """
        if not (header.startswith('<') or header.endswith('>')):
            raise exceptions.BatchError(
                'Invalid value for Content-ID: %s' % header)
        if '+' not in header:
            raise exceptions.BatchError(
                'Invalid value for Content-ID: %s' % header)
        _, request_id = header[1:-1].rsplit('+', 1)

        return urllib_parse.unquote(request_id)

    def _SerializeRequest(self, request):
        """Convert a http_wrapper.Request object into a string.

        Args:
          request: A http_wrapper.Request to serialize.

        Returns:
          The request as a string in application/http format.
        """
        # Construct status line
        parsed = urllib_parse.urlsplit(request.url)
        request_line = urllib_parse.urlunsplit(
            ('', '', parsed.path, parsed.query, ''))
        if not isinstance(request_line, six.text_type):
            request_line = request_line.decode('utf-8')
        status_line = u' '.join((
            request.http_method,
            request_line,
            u'HTTP/1.1\n'
        ))
        major, minor = request.headers.get(
            'content-type', 'application/json').split('/')
        msg = mime_nonmultipart.MIMENonMultipart(major, minor)

        # MIMENonMultipart adds its own Content-Type header.
        # Keep all of the other headers in `request.headers`.
        for key, value in request.headers.items():
            if key == 'content-type':
                continue
            msg[key] = value

        msg['Host'] = parsed.netloc
        msg.set_unixfrom(None)

        if request.body is not None:
            msg.set_payload(request.body)

        # Serialize the mime message.
        str_io = six.StringIO()
        # maxheaderlen=0 means don't line wrap headers.
        gen = generator.Generator(str_io, maxheaderlen=0)
        gen.flatten(msg, unixfrom=False)
        body = str_io.getvalue()

        return status_line + body

    def _DeserializeResponse(self, payload):
        """Convert string into Response and content.

        Args:
          payload: Header and body string to be deserialized.

        Returns:
          A Response object
        """
        # Strip off the status line.
        status_line, payload = payload.split('\n', 1)
        _, status, _ = status_line.split(' ', 2)

        # Parse the rest of the response.
        parser = email_parser.Parser()
        msg = parser.parsestr(payload)

        # Get the headers.
        info = dict(msg)
        info['status'] = status

        # Create Response from the parsed headers.
        content = msg.get_payload()

        return http_wrapper.Response(info, content, self.__batch_url)

    def _NewId(self):
        """Create a new id.

        Auto incrementing number that avoids conflicts with ids already used.

        Returns:
           A new unique id string.
        """
        return str(next(self.__last_auto_id))

    def Add(self, request, callback=None):
        """Add a new request.

        Args:
          request: A http_wrapper.Request to add to the batch.
          callback: A callback to be called for this response, of the
              form callback(response, exception). The first parameter is the
              deserialized response object. The second is an
              apiclient.errors.HttpError exception object if an HTTP error
              occurred while processing the request, or None if no errors
              occurred.

        Returns:
          None
        """
        handler = RequestResponseAndHandler(request, None, callback)
        self.__request_response_handlers[self._NewId()] = handler

    def _Execute(self, http):
        """Serialize batch request, send to server, process response.

        Args:
          http: A httplib2.Http object to be used to make the request with.

        Raises:
          httplib2.HttpLib2Error if a transport error has occured.
          apiclient.errors.BatchError if the response is the wrong format.
        """
        message = mime_multipart.MIMEMultipart('mixed')
        # Message should not write out its own headers.
        setattr(message, '_write_headers', lambda self: None)

        # Add all the individual requests.
        for key in self.__request_response_handlers:
            msg = mime_nonmultipart.MIMENonMultipart('application', 'http')
            msg['Content-Transfer-Encoding'] = 'binary'
            msg['Content-ID'] = self._ConvertIdToHeader(key)

            body = self._SerializeRequest(
                self.__request_response_handlers[key].request)
            msg.set_payload(body)
            message.attach(msg)

        request = http_wrapper.Request(self.__batch_url, 'POST')
        request.body = message.as_string()
        request.headers['content-type'] = (
            'multipart/mixed; boundary="%s"') % message.get_boundary()

        response = http_wrapper.MakeRequest(http, request)

        if response.status_code >= 300:
            raise exceptions.HttpError.FromResponse(response)

        # Prepend with a content-type header so Parser can handle it.
        header = 'content-type: %s\r\n\r\n' % response.info['content-type']

        content = response.content
        if isinstance(content, bytes) and self.__response_encoding:
            content = response.content.decode(self.__response_encoding)

        parser = email_parser.Parser()
        mime_response = parser.parsestr(header + content)

        if not mime_response.is_multipart():
            raise exceptions.BatchError(
                'Response not in multipart/mixed format.')

        for part in mime_response.get_payload():
            request_id = self._ConvertHeaderToId(part['Content-ID'])
            response = self._DeserializeResponse(part.get_payload())

            # Disable protected access because namedtuple._replace(...)
            # is not actually meant to be protected.
            # pylint: disable=protected-access
            self.__request_response_handlers[request_id] = (
                self.__request_response_handlers[request_id]._replace(
                    response=response))

    def Execute(self, http):
        """Execute all the requests as a single batched HTTP request.

        Args:
          http: A httplib2.Http object to be used with the request.

        Returns:
          None

        Raises:
          BatchError if the response is the wrong format.
        """

        self._Execute(http)

        for key in self.__request_response_handlers:
            response = self.__request_response_handlers[key].response
            callback = self.__request_response_handlers[key].handler

            exception = None

            if response.status_code >= 300:
                exception = exceptions.HttpError.FromResponse(response)

            if callback is not None:
                callback(response, exception)
            if self.__callback is not None:
                self.__callback(response, exception)
