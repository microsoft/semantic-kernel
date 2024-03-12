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

"""Tests for apitools.base.py.testing.mock."""

import unittest

import httplib2
import six

from apitools.base.protorpclite import messages

from apitools.base.py import base_api
from apitools.base.py import exceptions
from apitools.base.py.testing import mock
from samples.fusiontables_sample.fusiontables_v1 import \
    fusiontables_v1_client as fusiontables
from samples.fusiontables_sample.fusiontables_v1 import \
    fusiontables_v1_messages as fusiontables_messages


def _GetApiServices(api_client_class):
    return dict(
        (name, potential_service)
        for name, potential_service in six.iteritems(api_client_class.__dict__)
        if (isinstance(potential_service, type) and
            issubclass(potential_service, base_api.BaseApiService)))


class CustomException(Exception):
    pass


class MockTest(unittest.TestCase):

    def testMockFusionBasic(self):
        with mock.Client(fusiontables.FusiontablesV1) as client_class:
            client_class.column.List.Expect(
                request=1, response=2, enable_type_checking=False)
            client = fusiontables.FusiontablesV1(get_credentials=False)
            self.assertEqual(client.column.List(1), 2)
            with self.assertRaises(mock.UnexpectedRequestException):
                client.column.List(3)

    def testMockFusionException(self):
        with mock.Client(fusiontables.FusiontablesV1) as client_class:
            client_class.column.List.Expect(
                request=1,
                exception=exceptions.HttpError({'status': 404}, '', ''),
                enable_type_checking=False)
            client = fusiontables.FusiontablesV1(get_credentials=False)
            with self.assertRaises(exceptions.HttpError):
                client.column.List(1)

    def testMockFusionTypeChecking(self):
        with mock.Client(fusiontables.FusiontablesV1) as client_class:
            messages = client_class.MESSAGES_MODULE
            client_class.column.List.Expect(
                messages.FusiontablesColumnListRequest(tableId='foo'),
                messages.ColumnList(items=[], totalItems=0))
            client = fusiontables.FusiontablesV1(get_credentials=False)
            self.assertEqual(
                client.column.List(
                    messages.FusiontablesColumnListRequest(tableId='foo')),
                messages.ColumnList(items=[], totalItems=0))

    def testMockFusionTypeCheckingErrors(self):
        with mock.Client(fusiontables.FusiontablesV1) as client_class:
            messages = client_class.MESSAGES_MODULE
            # Wrong request type.
            with self.assertRaises(exceptions.ConfigurationValueError):
                client_class.column.List.Expect(
                    messages.FusiontablesColumnInsertRequest(),
                    messages.ColumnList(items=[], totalItems=0))
            # Wrong response type.
            with self.assertRaises(exceptions.ConfigurationValueError):
                client_class.column.List.Expect(
                    messages.FusiontablesColumnListRequest(tableId='foo'),
                    messages.Column())
            # No error if checking is disabled.
            client_class.column.List.Expect(
                messages.FusiontablesColumnInsertRequest(),
                messages.Column(),
                enable_type_checking=False)
            client_class.column.List(
                messages.FusiontablesColumnInsertRequest())

    def testMockIfAnotherException(self):
        with self.assertRaises(CustomException):
            with mock.Client(fusiontables.FusiontablesV1) as client_class:
                client_class.column.List.Expect(
                    request=1, response=2, enable_type_checking=False)
                raise CustomException('Something when wrong')

    def testMockFusionOrder(self):
        with mock.Client(fusiontables.FusiontablesV1) as client_class:
            client_class.column.List.Expect(
                request=1, response=2, enable_type_checking=False)
            client_class.column.List.Expect(
                request=2, response=1, enable_type_checking=False)
            client = fusiontables.FusiontablesV1(get_credentials=False)
            self.assertEqual(client.column.List(1), 2)
            self.assertEqual(client.column.List(2), 1)

    def testMockFusionWrongOrder(self):
        with mock.Client(fusiontables.FusiontablesV1) as client_class:
            client_class.column.List.Expect(
                request=1, response=2, enable_type_checking=False)
            client_class.column.List.Expect(
                request=2, response=1, enable_type_checking=False)
            client = fusiontables.FusiontablesV1(get_credentials=False)
            with self.assertRaises(mock.UnexpectedRequestException):
                self.assertEqual(client.column.List(2), 1)
            with self.assertRaises(mock.UnexpectedRequestException):
                self.assertEqual(client.column.List(1), 2)

    def testMockFusionTooMany(self):
        with mock.Client(fusiontables.FusiontablesV1) as client_class:
            client_class.column.List.Expect(
                request=1, response=2, enable_type_checking=False)
            client = fusiontables.FusiontablesV1(get_credentials=False)
            self.assertEqual(client.column.List(1), 2)
            with self.assertRaises(mock.UnexpectedRequestException):
                self.assertEqual(client.column.List(2), 1)

    def testMockFusionTooFew(self):
        with self.assertRaises(mock.ExpectedRequestsException):
            with mock.Client(fusiontables.FusiontablesV1) as client_class:
                client_class.column.List.Expect(
                    request=1, response=2, enable_type_checking=False)
                client_class.column.List.Expect(
                    request=2, response=1, enable_type_checking=False)
                client = fusiontables.FusiontablesV1(get_credentials=False)
                self.assertEqual(client.column.List(1), 2)

    def testFusionUnmock(self):
        with mock.Client(fusiontables.FusiontablesV1):
            client = fusiontables.FusiontablesV1(get_credentials=False)
            mocked_service_type = type(client.column)
        client = fusiontables.FusiontablesV1(get_credentials=False)
        self.assertNotEqual(type(client.column), mocked_service_type)

    def testRequestMacher(self):
        class Matcher(object):
            def __init__(self, eq):
                self._eq = eq

            def __eq__(self, other):
                return self._eq(other)

        with mock.Client(fusiontables.FusiontablesV1) as client_class:
            def IsEven(x):
                return x % 2 == 0

            def IsOdd(x):
                return not IsEven(x)

            client_class.column.List.Expect(
                request=Matcher(IsEven), response=1,
                enable_type_checking=False)
            client_class.column.List.Expect(
                request=Matcher(IsOdd), response=2, enable_type_checking=False)
            client_class.column.List.Expect(
                request=Matcher(IsEven), response=3,
                enable_type_checking=False)
            client_class.column.List.Expect(
                request=Matcher(IsOdd), response=4, enable_type_checking=False)

            client = fusiontables.FusiontablesV1(get_credentials=False)
            self.assertEqual(client.column.List(2), 1)
            self.assertEqual(client.column.List(1), 2)
            self.assertEqual(client.column.List(20), 3)
            self.assertEqual(client.column.List(23), 4)

    def testClientUnmock(self):
        mock_client = mock.Client(fusiontables.FusiontablesV1)
        self.assertFalse(isinstance(mock_client, fusiontables.FusiontablesV1))
        attributes = set(mock_client.__dict__.keys())
        mock_client = mock_client.Mock()
        self.assertTrue(isinstance(mock_client, fusiontables.FusiontablesV1))
        self.assertTrue(set(mock_client.__dict__.keys()) - attributes)
        mock_client.Unmock()
        self.assertFalse(isinstance(mock_client, fusiontables.FusiontablesV1))
        self.assertEqual(attributes, set(mock_client.__dict__.keys()))

    def testMockHasMessagesModule(self):
        with mock.Client(fusiontables.FusiontablesV1) as mock_client:
            self.assertEquals(fusiontables_messages,
                              mock_client.MESSAGES_MODULE)

    def testMockHasUrlProperty(self):
        with mock.Client(fusiontables.FusiontablesV1) as mock_client:
            self.assertEquals(fusiontables.FusiontablesV1.BASE_URL,
                              mock_client.url)
        self.assertFalse(hasattr(mock_client, 'url'))

    def testMockHasOverrideUrlProperty(self):
        real_client = fusiontables.FusiontablesV1(url='http://localhost:8080',
                                                  get_credentials=False)
        with mock.Client(fusiontables.FusiontablesV1,
                         real_client) as mock_client:
            self.assertEquals('http://localhost:8080/', mock_client.url)

    def testMockHasHttpProperty(self):
        with mock.Client(fusiontables.FusiontablesV1) as mock_client:
            self.assertIsInstance(mock_client.http, httplib2.Http)
        self.assertFalse(hasattr(mock_client, 'http'))

    def testMockHasOverrideHttpProperty(self):
        real_client = fusiontables.FusiontablesV1(url='http://localhost:8080',
                                                  http='SomeHttpObject',
                                                  get_credentials=False)
        with mock.Client(fusiontables.FusiontablesV1,
                         real_client) as mock_client:
            self.assertEquals('SomeHttpObject', mock_client.http)

    def testMockPreservesServiceMethods(self):
        services = _GetApiServices(fusiontables.FusiontablesV1)
        with mock.Client(fusiontables.FusiontablesV1):
            mocked_services = _GetApiServices(fusiontables.FusiontablesV1)
            self.assertEquals(services.keys(), mocked_services.keys())
            for name, service in six.iteritems(services):
                mocked_service = mocked_services[name]
                methods = service.GetMethodsList()
                for method in methods:
                    mocked_method = getattr(mocked_service, method)
                    mocked_method_config = mocked_method.method_config()
                    method_config = getattr(service, method).method_config()
                    self.assertEquals(method_config, mocked_method_config)


class _NestedMessage(messages.Message):
    nested = messages.StringField(1)


class _NestedListMessage(messages.Message):
    nested_list = messages.MessageField(_NestedMessage, 1, repeated=True)


class _NestedNestedMessage(messages.Message):
    nested = messages.MessageField(_NestedMessage, 1)


class UtilTest(unittest.TestCase):

    def testMessagesEqual(self):
        self.assertFalse(mock._MessagesEqual(
            _NestedNestedMessage(
                nested=_NestedMessage(
                    nested='foo')),
            _NestedNestedMessage(
                nested=_NestedMessage(
                    nested='bar'))))

        self.assertTrue(mock._MessagesEqual(
            _NestedNestedMessage(
                nested=_NestedMessage(
                    nested='foo')),
            _NestedNestedMessage(
                nested=_NestedMessage(
                    nested='foo'))))

    def testListedMessagesEqual(self):
        self.assertTrue(mock._MessagesEqual(
            _NestedListMessage(
                nested_list=[_NestedMessage(nested='foo')]),
            _NestedListMessage(
                nested_list=[_NestedMessage(nested='foo')])))

        self.assertTrue(mock._MessagesEqual(
            _NestedListMessage(
                nested_list=[_NestedMessage(nested='foo'),
                             _NestedMessage(nested='foo2')]),
            _NestedListMessage(
                nested_list=[_NestedMessage(nested='foo'),
                             _NestedMessage(nested='foo2')])))

        self.assertFalse(mock._MessagesEqual(
            _NestedListMessage(
                nested_list=[_NestedMessage(nested='foo')]),
            _NestedListMessage(
                nested_list=[_NestedMessage(nested='bar')])))

        self.assertFalse(mock._MessagesEqual(
            _NestedListMessage(
                nested_list=[_NestedMessage(nested='foo')]),
            _NestedListMessage(
                nested_list=[_NestedMessage(nested='foo'),
                             _NestedMessage(nested='foo')])))
