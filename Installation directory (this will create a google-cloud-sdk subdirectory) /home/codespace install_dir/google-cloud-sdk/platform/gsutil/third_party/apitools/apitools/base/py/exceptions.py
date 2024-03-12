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

"""Exceptions for generated client libraries."""


class Error(Exception):

    """Base class for all exceptions."""


class TypecheckError(Error, TypeError):

    """An object of an incorrect type is provided."""


class NotFoundError(Error):

    """A specified resource could not be found."""


class UserError(Error):

    """Base class for errors related to user input."""


class InvalidDataError(Error):

    """Base class for any invalid data error."""


class CommunicationError(Error):

    """Any communication error talking to an API server."""


class HttpError(CommunicationError):

    """Error making a request. Soon to be HttpError."""

    def __init__(self, response, content, url,
                 method_config=None, request=None):
        error_message = HttpError._build_message(response, content, url)
        super(HttpError, self).__init__(error_message)
        self.response = response
        self.content = content
        self.url = url
        self.method_config = method_config
        self.request = request

    def __str__(self):
        return HttpError._build_message(self.response, self.content, self.url)

    @staticmethod
    def _build_message(response, content, url):
        if isinstance(content, bytes):
            content = content.decode('ascii', 'replace')
        return 'HttpError accessing <%s>: response: <%s>, content <%s>' % (
            url, response, content)

    @property
    def status_code(self):
        # TODO(craigcitro): Turn this into something better than a
        # KeyError if there is no status.
        return int(self.response['status'])

    @classmethod
    def FromResponse(cls, http_response, **kwargs):
        try:
            status_code = int(http_response.info.get('status'))
            error_cls = _HTTP_ERRORS.get(status_code, cls)
        except ValueError:
            error_cls = cls
        return error_cls(http_response.info, http_response.content,
                         http_response.request_url, **kwargs)


class HttpBadRequestError(HttpError):
    """HTTP 400 Bad Request."""


class HttpUnauthorizedError(HttpError):
    """HTTP 401 Unauthorized."""


class HttpForbiddenError(HttpError):
    """HTTP 403 Forbidden."""


class HttpNotFoundError(HttpError):
    """HTTP 404 Not Found."""


class HttpConflictError(HttpError):
    """HTTP 409 Conflict."""


_HTTP_ERRORS = {
    400: HttpBadRequestError,
    401: HttpUnauthorizedError,
    403: HttpForbiddenError,
    404: HttpNotFoundError,
    409: HttpConflictError,
}


class InvalidUserInputError(InvalidDataError):

    """User-provided input is invalid."""


class InvalidDataFromServerError(InvalidDataError, CommunicationError):

    """Data received from the server is malformed."""


class BatchError(Error):

    """Error generated while constructing a batch request."""


class ConfigurationError(Error):

    """Base class for configuration errors."""


class GeneratedClientError(Error):

    """The generated client configuration is invalid."""


class ConfigurationValueError(UserError):

    """Some part of the user-specified client configuration is invalid."""


class ResourceUnavailableError(Error):

    """User requested an unavailable resource."""


class CredentialsError(Error):

    """Errors related to invalid credentials."""


class TransferError(CommunicationError):

    """Errors related to transfers."""


class TransferRetryError(TransferError):

    """Retryable errors related to transfers."""


class TransferInvalidError(TransferError):

    """The given transfer is invalid."""


class RequestError(CommunicationError):

    """The request was not successful."""


class RetryAfterError(HttpError):

    """The response contained a retry-after header."""

    def __init__(self, response, content, url, retry_after, **kwargs):
        super(RetryAfterError, self).__init__(response, content, url, **kwargs)
        self.retry_after = int(retry_after)

    @classmethod
    def FromResponse(cls, http_response, **kwargs):
        return cls(http_response.info, http_response.content,
                   http_response.request_url, http_response.retry_after,
                   **kwargs)


class BadStatusCodeError(HttpError):

    """The request completed but returned a bad status code."""


class NotYetImplementedError(GeneratedClientError):

    """This functionality is not yet implemented."""


class StreamExhausted(Error):

    """Attempted to read more bytes from a stream than were available."""
