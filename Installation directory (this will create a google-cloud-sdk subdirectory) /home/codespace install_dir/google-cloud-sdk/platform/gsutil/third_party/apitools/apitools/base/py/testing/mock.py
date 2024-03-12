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

"""The mock module allows easy mocking of apitools clients.

This module allows you to mock out the constructor of a particular apitools
client, for a specific API and version. Then, when the client is created, it
will be run against an expected session that you define. This way code that is
not aware of the testing framework can construct new clients as normal, as long
as it's all done within the context of a mock.
"""

import difflib
import sys

import six

from apitools.base.protorpclite import messages
from apitools.base.py import base_api
from apitools.base.py import encoding
from apitools.base.py import exceptions


class Error(Exception):

    """Exceptions for this module."""


def _MessagesEqual(msg1, msg2):
    """Compare two protorpc messages for equality.

    Using python's == operator does not work in all cases, specifically when
    there is a list involved.

    Args:
      msg1: protorpc.messages.Message or [protorpc.messages.Message] or number
          or string, One of the messages to compare.
      msg2: protorpc.messages.Message or [protorpc.messages.Message] or number
          or string, One of the messages to compare.

    Returns:
      If the messages are isomorphic.
    """
    if isinstance(msg1, list) and isinstance(msg2, list):
        if len(msg1) != len(msg2):
            return False
        return all(_MessagesEqual(x, y) for x, y in zip(msg1, msg2))

    if (not isinstance(msg1, messages.Message) or
            not isinstance(msg2, messages.Message)):
        return msg1 == msg2
    for field in msg1.all_fields():
        field1 = getattr(msg1, field.name)
        field2 = getattr(msg2, field.name)
        if not _MessagesEqual(field1, field2):
            return False
    return True


class UnexpectedRequestException(Error):

    def __init__(self, received_call, expected_call):
        expected_key, expected_request = expected_call
        received_key, received_request = received_call

        expected_repr = encoding.MessageToRepr(
            expected_request, multiline=True)
        received_repr = encoding.MessageToRepr(
            received_request, multiline=True)

        expected_lines = expected_repr.splitlines()
        received_lines = received_repr.splitlines()

        diff_lines = difflib.unified_diff(expected_lines, received_lines)
        diff = '\n'.join(diff_lines)

        if expected_key != received_key:
            msg = '\n'.join((
                'expected: {expected_key}({expected_request})',
                'received: {received_key}({received_request})',
                '',
            )).format(
                expected_key=expected_key,
                expected_request=expected_repr,
                received_key=received_key,
                received_request=received_repr)
            super(UnexpectedRequestException, self).__init__(msg)
        else:
            msg = '\n'.join((
                'for request to {key},',
                'expected: {expected_request}',
                'received: {received_request}',
                'diff: {diff}',
                '',
            )).format(
                key=expected_key,
                expected_request=expected_repr,
                received_request=received_repr,
                diff=diff)
            super(UnexpectedRequestException, self).__init__(msg)


class ExpectedRequestsException(Error):

    def __init__(self, expected_calls):
        msg = 'expected:\n'
        for (key, request) in expected_calls:
            msg += '{key}({request})\n'.format(
                key=key,
                request=encoding.MessageToRepr(request, multiline=True))
        super(ExpectedRequestsException, self).__init__(msg)


class _ExpectedRequestResponse(object):

    """Encapsulation of an expected request and corresponding response."""

    def __init__(self, key, request, response=None, exception=None):
        self.__key = key
        self.__request = request

        if response and exception:
            raise exceptions.ConfigurationValueError(
                'Should specify at most one of response and exception')
        if response and isinstance(response, exceptions.Error):
            raise exceptions.ConfigurationValueError(
                'Responses should not be an instance of Error')
        if exception and not isinstance(exception, exceptions.Error):
            raise exceptions.ConfigurationValueError(
                'Exceptions must be instances of Error')

        self.__response = response
        self.__exception = exception

    @property
    def key(self):
        return self.__key

    @property
    def request(self):
        return self.__request

    def ValidateAndRespond(self, key, request):
        """Validate that key and request match expectations, and respond if so.

        Args:
          key: str, Actual key to compare against expectations.
          request: protorpc.messages.Message or [protorpc.messages.Message]
            or number or string, Actual request to compare againt expectations

        Raises:
          UnexpectedRequestException: If key or request dont match
              expectations.
          apitools_base.Error: If a non-None exception is specified to
              be thrown.

        Returns:
          The response that was specified to be returned.

        """
        if key != self.__key or not (self.__request == request or
                                     _MessagesEqual(request, self.__request)):
            raise UnexpectedRequestException((key, request),
                                             (self.__key, self.__request))

        if self.__exception:
            # Can only throw apitools_base.Error.
            raise self.__exception  # pylint: disable=raising-bad-type

        return self.__response


class _MockedMethod(object):

    """A mocked API service method."""

    def __init__(self, key, mocked_client, real_method):
        self.__name__ = real_method.__name__
        self.__key = key
        self.__mocked_client = mocked_client
        self.__real_method = real_method
        self.method_config = real_method.method_config
        config = self.method_config()
        self.__request_type = getattr(self.__mocked_client.MESSAGES_MODULE,
                                      config.request_type_name)
        self.__response_type = getattr(self.__mocked_client.MESSAGES_MODULE,
                                       config.response_type_name)

    def _TypeCheck(self, msg, is_request):
        """Ensure the given message is of the expected type of this method.

        Args:
          msg: The message instance to check.
          is_request: True to validate against the expected request type,
             False to validate against the expected response type.

        Raises:
          exceptions.ConfigurationValueError: If the type of the message was
             not correct.
        """
        if is_request:
            mode = 'request'
            real_type = self.__request_type
        else:
            mode = 'response'
            real_type = self.__response_type

        if not isinstance(msg, real_type):
            raise exceptions.ConfigurationValueError(
                'Expected {} is not of the correct type for method [{}].\n'
                '   Required: [{}]\n'
                '   Given:    [{}]'.format(
                    mode, self.__key, real_type, type(msg)))

    def Expect(self, request, response=None, exception=None,
               enable_type_checking=True, **unused_kwargs):
        """Add an expectation on the mocked method.

        Exactly one of response and exception should be specified.

        Args:
          request: The request that should be expected
          response: The response that should be returned or None if
              exception is provided.
          exception: An exception that should be thrown, or None.
          enable_type_checking: When true, the message type of the request
              and response (if provided) will be checked against the types
              required by this method.
        """
        # TODO(jasmuth): the unused_kwargs provides a placeholder for
        # future things that can be passed to Expect(), like special
        # params to the method call.

        # Ensure that the registered request and response mocks actually
        # match what this method accepts and returns.
        if enable_type_checking:
            self._TypeCheck(request, is_request=True)
            if response:
                self._TypeCheck(response, is_request=False)

        # pylint: disable=protected-access
        # Class in same module.
        self.__mocked_client._request_responses.append(
            _ExpectedRequestResponse(self.__key,
                                     request,
                                     response=response,
                                     exception=exception))
        # pylint: enable=protected-access

    def __call__(self, request, **unused_kwargs):
        # TODO(jasmuth): allow the testing code to expect certain
        # values in these currently unused_kwargs, especially the
        # upload parameter used by media-heavy services like bigquery
        # or bigstore.

        # pylint: disable=protected-access
        # Class in same module.
        if self.__mocked_client._request_responses:
            request_response = self.__mocked_client._request_responses.pop(0)
        else:
            raise UnexpectedRequestException(
                (self.__key, request), (None, None))
        # pylint: enable=protected-access

        response = request_response.ValidateAndRespond(self.__key, request)

        if response is None and self.__real_method:
            response = self.__real_method(request)
            print(encoding.MessageToRepr(
                response, multiline=True, shortstrings=True))
            return response

        return response


def _MakeMockedService(api_name, collection_name,
                       mock_client, service, real_service):
    class MockedService(base_api.BaseApiService):
        pass

    for method in service.GetMethodsList():
        real_method = None
        if real_service:
            real_method = getattr(real_service, method)
        setattr(MockedService,
                method,
                _MockedMethod(api_name + '.' + collection_name + '.' + method,
                              mock_client,
                              real_method))
    return MockedService


class Client(object):

    """Mock an apitools client."""

    def __init__(self, client_class, real_client=None):
        """Mock an apitools API, given its class.

        Args:
          client_class: The class for the API. eg, if you
                from apis.sqladmin import v1beta3
              then you can pass v1beta3.SqladminV1beta3 to this class
              and anything within its context will use your mocked
              version.
          real_client: apitools Client, The client to make requests
              against when the expected response is None.

        """

        if not real_client:
            real_client = client_class(get_credentials=False)

        self.__orig_class = self.__class__
        self.__client_class = client_class
        self.__real_service_classes = {}
        self.__real_client = real_client

        self._request_responses = []
        self.__real_include_fields = None

    def __enter__(self):
        return self.Mock()

    def Mock(self):
        """Stub out the client class with mocked services."""
        client = self.__real_client or self.__client_class(
            get_credentials=False)

        class Patched(self.__class__, self.__client_class):
            pass
        self.__class__ = Patched

        for name in dir(self.__client_class):
            service_class = getattr(self.__client_class, name)
            if not isinstance(service_class, type):
                continue
            if not issubclass(service_class, base_api.BaseApiService):
                continue
            self.__real_service_classes[name] = service_class
            # pylint: disable=protected-access
            collection_name = service_class._NAME
            # pylint: enable=protected-access
            api_name = '%s_%s' % (self.__client_class._PACKAGE,
                                  self.__client_class._URL_VERSION)
            mocked_service_class = _MakeMockedService(
                api_name, collection_name, self,
                service_class,
                service_class(client) if self.__real_client else None)

            setattr(self.__client_class, name, mocked_service_class)

            setattr(self, collection_name, mocked_service_class(self))

        self.__real_include_fields = self.__client_class.IncludeFields
        self.__client_class.IncludeFields = self.IncludeFields

        # pylint: disable=attribute-defined-outside-init
        self._url = client._url
        self._http = client._http

        return self

    def __exit__(self, exc_type, value, traceback):
        is_active_exception = value is not None
        self.Unmock(suppress=is_active_exception)
        if is_active_exception:
            six.reraise(exc_type, value, traceback)
        return True

    def Unmock(self, suppress=False):
        self.__class__ = self.__orig_class
        for name, service_class in self.__real_service_classes.items():
            setattr(self.__client_class, name, service_class)
            delattr(self, service_class._NAME)
        self.__real_service_classes = {}
        del self._url
        del self._http

        self.__client_class.IncludeFields = self.__real_include_fields
        self.__real_include_fields = None

        requests = [(rq_rs.key, rq_rs.request)
                    for rq_rs in self._request_responses]
        self._request_responses = []

        if requests and not suppress and sys.exc_info()[1] is None:
            raise ExpectedRequestsException(requests)

    def IncludeFields(self, include_fields):
        if self.__real_client:
            return self.__real_include_fields(self.__real_client,
                                              include_fields)
