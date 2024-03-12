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

import base64
import datetime
import sys
import contextlib
import unittest

import six
from six.moves import http_client
from six.moves import urllib_parse

from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.py import base_api
from apitools.base.py import encoding
from apitools.base.py import exceptions
from apitools.base.py import http_wrapper


@contextlib.contextmanager
def mock(module, fn_name, patch):
    unpatch = getattr(module, fn_name)
    setattr(module, fn_name, patch)
    try:
        yield
    finally:
        setattr(module, fn_name, unpatch)


class SimpleMessage(messages.Message):
    field = messages.StringField(1)
    bytes_field = messages.BytesField(2)


class MessageWithTime(messages.Message):
    timestamp = message_types.DateTimeField(1)


class MessageWithRemappings(messages.Message):

    class AnEnum(messages.Enum):
        value_one = 1
        value_two = 2

    str_field = messages.StringField(1)
    enum_field = messages.EnumField('AnEnum', 2)


encoding.AddCustomJsonFieldMapping(
    MessageWithRemappings, 'str_field', 'remapped_field')
encoding.AddCustomJsonEnumMapping(
    MessageWithRemappings.AnEnum, 'value_one', 'ONE/TWO')


class StandardQueryParameters(messages.Message):
    field = messages.StringField(1)
    prettyPrint = messages.BooleanField(
        5, default=True)  # pylint: disable=invalid-name
    pp = messages.BooleanField(6, default=True)
    nextPageToken = messages.BytesField(7)  # pylint:disable=invalid-name


class FakeCredentials(object):

    def authorize(self, _):  # pylint: disable=invalid-name
        return None


class FakeClient(base_api.BaseApiClient):
    MESSAGES_MODULE = sys.modules[__name__]
    _PACKAGE = 'package'
    _SCOPES = ['scope1']
    _CLIENT_ID = 'client_id'
    _CLIENT_SECRET = 'client_secret'


class FakeService(base_api.BaseApiService):

    def __init__(self, client=None):
        client = client or FakeClient(
            'http://www.example.com/', credentials=FakeCredentials())
        super(FakeService, self).__init__(client)


class BaseApiTest(unittest.TestCase):

    def __GetFakeClient(self):
        return FakeClient('', credentials=FakeCredentials())

    def testUrlNormalization(self):
        client = FakeClient('http://www.googleapis.com', get_credentials=False)
        self.assertTrue(client.url.endswith('/'))

    def testNoCredentials(self):
        client = FakeClient('', get_credentials=False)
        self.assertIsNotNone(client)
        self.assertIsNone(client._credentials)

    def testIncludeEmptyFieldsClient(self):
        msg = SimpleMessage()
        client = self.__GetFakeClient()
        self.assertEqual('{}', client.SerializeMessage(msg))
        with client.IncludeFields(('field',)):
            self.assertEqual('{"field": null}', client.SerializeMessage(msg))

    def testJsonResponse(self):
        method_config = base_api.ApiMethodInfo(
            response_type_name='SimpleMessage')
        service = FakeService()
        http_response = http_wrapper.Response(
            info={'status': '200'}, content='{"field": "abc"}',
            request_url='http://www.google.com')
        response_message = SimpleMessage(field='abc')
        self.assertEqual(response_message, service.ProcessHttpResponse(
            method_config, http_response))
        with service.client.JsonResponseModel():
            self.assertEqual(
                http_response.content,
                service.ProcessHttpResponse(method_config, http_response))

    def testJsonResponseEncoding(self):
        # On Python 3, httplib2 always returns bytes, so we need to check that
        # we can correctly decode the message content using the given encoding.
        method_config = base_api.ApiMethodInfo(
            response_type_name='SimpleMessage')
        service = FakeService(FakeClient(
            'http://www.example.com/', credentials=FakeCredentials(),
            response_encoding='utf8'))
        http_response = http_wrapper.Response(
            info={'status': '200'}, content=b'{"field": "abc"}',
            request_url='http://www.google.com')
        response_message = SimpleMessage(field=u'abc')
        self.assertEqual(response_message, service.ProcessHttpResponse(
            method_config, http_response))
        with service.client.JsonResponseModel():
            self.assertEqual(
                http_response.content.decode('utf8'),
                service.ProcessHttpResponse(method_config, http_response))

    def testAdditionalHeaders(self):
        additional_headers = {'Request-Is-Awesome': '1'}
        client = self.__GetFakeClient()

        # No headers to start
        http_request = http_wrapper.Request('http://www.example.com')
        new_request = client.ProcessHttpRequest(http_request)
        self.assertFalse('Request-Is-Awesome' in new_request.headers)

        # Add a new header and ensure it's added to the request.
        client.additional_http_headers = additional_headers
        http_request = http_wrapper.Request('http://www.example.com')
        new_request = client.ProcessHttpRequest(http_request)
        self.assertTrue('Request-Is-Awesome' in new_request.headers)

    def testCustomCheckResponse(self):
        def check_response():
            pass

        def fakeMakeRequest(*_, **kwargs):
            self.assertEqual(check_response, kwargs['check_response_func'])
            return http_wrapper.Response(
                info={'status': '200'}, content='{"field": "abc"}',
                request_url='http://www.google.com')
        method_config = base_api.ApiMethodInfo(
            request_type_name='SimpleMessage',
            response_type_name='SimpleMessage')
        client = self.__GetFakeClient()
        client.check_response_func = check_response
        service = FakeService(client=client)
        request = SimpleMessage()
        with mock(base_api.http_wrapper, 'MakeRequest', fakeMakeRequest):
            service._RunMethod(method_config, request)

    def testCustomRetryFunc(self):
        def retry_func():
            pass

        def fakeMakeRequest(*_, **kwargs):
            self.assertEqual(retry_func, kwargs['retry_func'])
            return http_wrapper.Response(
                info={'status': '200'}, content='{"field": "abc"}',
                request_url='http://www.google.com')
        method_config = base_api.ApiMethodInfo(
            request_type_name='SimpleMessage',
            response_type_name='SimpleMessage')
        client = self.__GetFakeClient()
        client.retry_func = retry_func
        service = FakeService(client=client)
        request = SimpleMessage()
        with mock(base_api.http_wrapper, 'MakeRequest', fakeMakeRequest):
            service._RunMethod(method_config, request)

    def testHttpError(self):
        def fakeMakeRequest(*unused_args, **unused_kwargs):
            return http_wrapper.Response(
                info={'status': http_client.BAD_REQUEST},
                content='{"field": "abc"}',
                request_url='http://www.google.com')
        method_config = base_api.ApiMethodInfo(
            request_type_name='SimpleMessage',
            response_type_name='SimpleMessage')
        client = self.__GetFakeClient()
        service = FakeService(client=client)
        request = SimpleMessage()
        with mock(base_api.http_wrapper, 'MakeRequest', fakeMakeRequest):
            with self.assertRaises(exceptions.HttpBadRequestError) as err:
                service._RunMethod(method_config, request)
        http_error = err.exception
        self.assertEquals('http://www.google.com', http_error.url)
        self.assertEquals('{"field": "abc"}', http_error.content)
        self.assertEquals(method_config, http_error.method_config)
        self.assertEquals(request, http_error.request)

    def testQueryEncoding(self):
        method_config = base_api.ApiMethodInfo(
            request_type_name='MessageWithTime', query_params=['timestamp'])
        service = FakeService()
        request = MessageWithTime(
            timestamp=datetime.datetime(2014, 10, 0o7, 12, 53, 13))
        http_request = service.PrepareHttpRequest(method_config, request)

        url_timestamp = urllib_parse.quote(request.timestamp.isoformat())
        self.assertTrue(http_request.url.endswith(url_timestamp))

    def testPrettyPrintEncoding(self):
        method_config = base_api.ApiMethodInfo(
            request_type_name='MessageWithTime', query_params=['timestamp'])
        service = FakeService()
        request = MessageWithTime(
            timestamp=datetime.datetime(2014, 10, 0o7, 12, 53, 13))

        global_params = StandardQueryParameters()
        http_request = service.PrepareHttpRequest(method_config, request,
                                                  global_params=global_params)
        self.assertFalse('prettyPrint' in http_request.url)
        self.assertFalse('pp' in http_request.url)

        global_params.prettyPrint = False  # pylint: disable=invalid-name
        global_params.pp = False

        http_request = service.PrepareHttpRequest(method_config, request,
                                                  global_params=global_params)
        self.assertTrue('prettyPrint=0' in http_request.url)
        self.assertTrue('pp=0' in http_request.url)

    def testQueryBytesRequest(self):
        method_config = base_api.ApiMethodInfo(
            request_type_name='SimpleMessage', query_params=['bytes_field'])
        service = FakeService()
        non_unicode_message = b''.join((six.int2byte(100),
                                        six.int2byte(200)))
        request = SimpleMessage(bytes_field=non_unicode_message)
        global_params = StandardQueryParameters()
        http_request = service.PrepareHttpRequest(method_config, request,
                                                  global_params=global_params)
        want = urllib_parse.urlencode({
            'bytes_field': base64.urlsafe_b64encode(non_unicode_message),
        })
        self.assertIn(want, http_request.url)

    def testQueryBytesGlobalParams(self):
        method_config = base_api.ApiMethodInfo(
            request_type_name='SimpleMessage', query_params=['bytes_field'])
        service = FakeService()
        non_unicode_message = b''.join((six.int2byte(100),
                                        six.int2byte(200)))
        request = SimpleMessage()
        global_params = StandardQueryParameters(
            nextPageToken=non_unicode_message)
        http_request = service.PrepareHttpRequest(method_config, request,
                                                  global_params=global_params)
        want = urllib_parse.urlencode({
            'nextPageToken': base64.urlsafe_b64encode(non_unicode_message),
        })
        self.assertIn(want, http_request.url)

    def testQueryRemapping(self):
        method_config = base_api.ApiMethodInfo(
            request_type_name='MessageWithRemappings',
            query_params=['remapped_field', 'enum_field'])
        request = MessageWithRemappings(
            str_field='foo', enum_field=MessageWithRemappings.AnEnum.value_one)
        http_request = FakeService().PrepareHttpRequest(method_config, request)
        result_params = urllib_parse.parse_qs(
            urllib_parse.urlparse(http_request.url).query)
        expected_params = {'enum_field': 'ONE%2FTWO', 'remapped_field': 'foo'}
        self.assertTrue(expected_params, result_params)

    def testPathRemapping(self):
        method_config = base_api.ApiMethodInfo(
            relative_path='parameters/{remapped_field}/remap/{enum_field}',
            request_type_name='MessageWithRemappings',
            path_params=['remapped_field', 'enum_field'])
        request = MessageWithRemappings(
            str_field='gonna',
            enum_field=MessageWithRemappings.AnEnum.value_one)
        service = FakeService()
        expected_url = service.client.url + 'parameters/gonna/remap/ONE%2FTWO'
        http_request = service.PrepareHttpRequest(method_config, request)
        self.assertEqual(expected_url, http_request.url)

        method_config.relative_path = (
            'parameters/{+remapped_field}/remap/{+enum_field}')
        expected_url = service.client.url + 'parameters/gonna/remap/ONE/TWO'
        http_request = service.PrepareHttpRequest(method_config, request)
        self.assertEqual(expected_url, http_request.url)

    def testColonInRelativePath(self):
        method_config = base_api.ApiMethodInfo(
            relative_path='path:withJustColon',
            request_type_name='SimpleMessage')
        service = FakeService()
        request = SimpleMessage()
        http_request = service.PrepareHttpRequest(method_config, request)
        self.assertEqual('http://www.example.com/path:withJustColon',
                         http_request.url)

    def testOverwritesTransferUrlBase(self):
        client = self.__GetFakeClient()
        client.overwrite_transfer_urls_with_client_base = True
        client._url = 'http://custom.p.googleapis.com/'
        observed = client.FinalizeTransferUrl(
            'http://normal.googleapis.com/path')
        expected = 'http://custom.p.googleapis.com/path'
        self.assertEqual(observed, expected)


if __name__ == '__main__':
    unittest.main()
