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

"""Tests for list_pager."""

import unittest

from apitools.base.py import list_pager
from apitools.base.py.testing import mock
from samples.fusiontables_sample.fusiontables_v1 \
    import fusiontables_v1_client as fusiontables
from samples.fusiontables_sample.fusiontables_v1 \
    import fusiontables_v1_messages as messages
from samples.iam_sample.iam_v1 import iam_v1_client as iam_client
from samples.iam_sample.iam_v1 import iam_v1_messages as iam_messages


class Example(object):
    def __init__(self):
        self.a = 'aaa'
        self.b = 'bbb'
        self.c = 'ccc'


class GetterSetterTest(unittest.TestCase):

    def testGetattrNested(self):
        o = Example()
        self.assertEqual(list_pager._GetattrNested(o, 'a'), 'aaa')
        self.assertEqual(list_pager._GetattrNested(o, ('a',)), 'aaa')
        o.b = Example()
        self.assertEqual(list_pager._GetattrNested(o, ('b', 'c')), 'ccc')

    def testSetattrNested(self):
        o = Example()
        list_pager._SetattrNested(o, 'b', Example())
        self.assertEqual(o.b.a, 'aaa')
        list_pager._SetattrNested(o, ('b', 'a'), 'AAA')
        self.assertEqual(o.b.a, 'AAA')
        list_pager._SetattrNested(o, ('c',), 'CCC')
        self.assertEqual(o.c, 'CCC')


class ListPagerTest(unittest.TestCase):

    def _AssertInstanceSequence(self, results, n):
        counter = 0
        for instance in results:
            self.assertEqual(instance.name, 'c' + str(counter))
            counter += 1

        self.assertEqual(counter, n)

    def setUp(self):
        self.mocked_client = mock.Client(fusiontables.FusiontablesV1)
        self.mocked_client.Mock()
        self.addCleanup(self.mocked_client.Unmock)

    def testYieldFromList(self):
        self.mocked_client.column.List.Expect(
            messages.FusiontablesColumnListRequest(
                maxResults=100,
                pageToken=None,
                tableId='mytable',
            ),
            messages.ColumnList(
                items=[
                    messages.Column(name='c0'),
                    messages.Column(name='c1'),
                    messages.Column(name='c2'),
                    messages.Column(name='c3'),
                ],
                nextPageToken='x',
            ))
        self.mocked_client.column.List.Expect(
            messages.FusiontablesColumnListRequest(
                maxResults=100,
                pageToken='x',
                tableId='mytable',
            ),
            messages.ColumnList(
                items=[
                    messages.Column(name='c4'),
                    messages.Column(name='c5'),
                    messages.Column(name='c6'),
                    messages.Column(name='c7'),
                ],
            ))

        client = fusiontables.FusiontablesV1(get_credentials=False)
        request = messages.FusiontablesColumnListRequest(tableId='mytable')
        results = list_pager.YieldFromList(client.column, request)

        self._AssertInstanceSequence(results, 8)

    def testYieldNoRecords(self):
        client = fusiontables.FusiontablesV1(get_credentials=False)
        request = messages.FusiontablesColumnListRequest(tableId='mytable')
        results = list_pager.YieldFromList(client.column, request, limit=False)
        self.assertEqual(0, len(list(results)))

    def testYieldFromListPartial(self):
        self.mocked_client.column.List.Expect(
            messages.FusiontablesColumnListRequest(
                maxResults=6,
                pageToken=None,
                tableId='mytable',
            ),
            messages.ColumnList(
                items=[
                    messages.Column(name='c0'),
                    messages.Column(name='c1'),
                    messages.Column(name='c2'),
                    messages.Column(name='c3'),
                ],
                nextPageToken='x',
            ))
        self.mocked_client.column.List.Expect(
            messages.FusiontablesColumnListRequest(
                maxResults=2,
                pageToken='x',
                tableId='mytable',
            ),
            messages.ColumnList(
                items=[
                    messages.Column(name='c4'),
                    messages.Column(name='c5'),
                    messages.Column(name='c6'),
                    messages.Column(name='c7'),
                ],
            ))

        client = fusiontables.FusiontablesV1(get_credentials=False)
        request = messages.FusiontablesColumnListRequest(tableId='mytable')
        results = list_pager.YieldFromList(client.column, request, limit=6)

        self._AssertInstanceSequence(results, 6)

    def testYieldFromListPaging(self):
        self.mocked_client.column.List.Expect(
            messages.FusiontablesColumnListRequest(
                maxResults=5,
                pageToken=None,
                tableId='mytable',
            ),
            messages.ColumnList(
                items=[
                    messages.Column(name='c0'),
                    messages.Column(name='c1'),
                    messages.Column(name='c2'),
                    messages.Column(name='c3'),
                    messages.Column(name='c4'),
                ],
                nextPageToken='x',
            ))
        self.mocked_client.column.List.Expect(
            messages.FusiontablesColumnListRequest(
                maxResults=4,
                pageToken='x',
                tableId='mytable',
            ),
            messages.ColumnList(
                items=[
                    messages.Column(name='c5'),
                    messages.Column(name='c6'),
                    messages.Column(name='c7'),
                    messages.Column(name='c8'),
                ],
            ))

        client = fusiontables.FusiontablesV1(get_credentials=False)
        request = messages.FusiontablesColumnListRequest(tableId='mytable')
        results = list_pager.YieldFromList(client.column,
                                           request,
                                           limit=9,
                                           batch_size=5)

        self._AssertInstanceSequence(results, 9)

    def testYieldFromListBatchSizeNone(self):
        self.mocked_client.column.List.Expect(
            messages.FusiontablesColumnListRequest(
                maxResults=None,
                pageToken=None,
                tableId='mytable',
            ),
            messages.ColumnList(
                items=[
                    messages.Column(name='c0'),
                    messages.Column(name='c1'),
                    messages.Column(name='c2'),
                    messages.Column(name='c3'),
                    messages.Column(name='c4'),
                    messages.Column(name='c5'),
                    messages.Column(name='c6'),
                ],
                nextPageToken='x',
            ))

        client = fusiontables.FusiontablesV1(get_credentials=False)
        request = messages.FusiontablesColumnListRequest(tableId='mytable')
        results = list_pager.YieldFromList(client.column,
                                           request,
                                           limit=5,
                                           batch_size=None)

        self._AssertInstanceSequence(results, 5)

    def testYieldFromListEmpty(self):
        self.mocked_client.column.List.Expect(
            messages.FusiontablesColumnListRequest(
                maxResults=6,
                pageToken=None,
                tableId='mytable',
            ),
            messages.ColumnList())

        client = fusiontables.FusiontablesV1(get_credentials=False)
        request = messages.FusiontablesColumnListRequest(tableId='mytable')
        results = list_pager.YieldFromList(client.column, request, limit=6)

        self._AssertInstanceSequence(results, 0)

    def testYieldFromListWithPredicate(self):
        self.mocked_client.column.List.Expect(
            messages.FusiontablesColumnListRequest(
                maxResults=100,
                pageToken=None,
                tableId='mytable',
            ),
            messages.ColumnList(
                items=[
                    messages.Column(name='c0'),
                    messages.Column(name='bad0'),
                    messages.Column(name='c1'),
                    messages.Column(name='bad1'),
                ],
                nextPageToken='x',
            ))
        self.mocked_client.column.List.Expect(
            messages.FusiontablesColumnListRequest(
                maxResults=100,
                pageToken='x',
                tableId='mytable',
            ),
            messages.ColumnList(
                items=[
                    messages.Column(name='c2'),
                ],
            ))

        client = fusiontables.FusiontablesV1(get_credentials=False)
        request = messages.FusiontablesColumnListRequest(tableId='mytable')
        results = list_pager.YieldFromList(
            client.column, request, predicate=lambda x: 'c' in x.name)

        self._AssertInstanceSequence(results, 3)

    def testYieldFromListWithCustomGetFieldFunction(self):
        self.mocked_client.column.List.Expect(
            messages.FusiontablesColumnListRequest(
                maxResults=100,
                pageToken=None,
                tableId='mytable',
            ),
            messages.ColumnList(
                items=[
                    messages.Column(name='c0')
                ]
            ))
        custom_getter_called = []

        def Custom_Getter(message, attribute):
            custom_getter_called.append(True)
            return getattr(message, attribute)

        client = fusiontables.FusiontablesV1(get_credentials=False)
        request = messages.FusiontablesColumnListRequest(tableId='mytable')
        results = list_pager.YieldFromList(
            client.column, request, get_field_func=Custom_Getter)

        self._AssertInstanceSequence(results, 1)
        self.assertEquals(1, len(custom_getter_called))


class ListPagerAttributeTest(unittest.TestCase):

    def setUp(self):
        self.mocked_client = mock.Client(iam_client.IamV1)
        self.mocked_client.Mock()
        self.addCleanup(self.mocked_client.Unmock)

    def testYieldFromListWithAttributes(self):
        self.mocked_client.iamPolicies.GetPolicyDetails.Expect(
            iam_messages.GetPolicyDetailsRequest(
                pageSize=100,
                pageToken=None,
                fullResourcePath='myresource',
            ),
            iam_messages.GetPolicyDetailsResponse(
                policies=[
                    iam_messages.PolicyDetail(fullResourcePath='c0'),
                    iam_messages.PolicyDetail(fullResourcePath='c1'),
                ],
                nextPageToken='x',
            ))
        self.mocked_client.iamPolicies.GetPolicyDetails.Expect(
            iam_messages.GetPolicyDetailsRequest(
                pageSize=100,
                pageToken='x',
                fullResourcePath='myresource',
            ),
            iam_messages.GetPolicyDetailsResponse(
                policies=[
                    iam_messages.PolicyDetail(fullResourcePath='c2'),
                ],
            ))

        client = iam_client.IamV1(get_credentials=False)
        request = iam_messages.GetPolicyDetailsRequest(
            fullResourcePath='myresource')
        results = list_pager.YieldFromList(
            client.iamPolicies, request,
            batch_size_attribute='pageSize',
            method='GetPolicyDetails', field='policies')

        i = 0
        for i, instance in enumerate(results):
            self.assertEquals('c{0}'.format(i), instance.fullResourcePath)
        self.assertEquals(2, i)

    def testYieldFromListWithNoBatchSizeAttribute(self):
        self.mocked_client.iamPolicies.GetPolicyDetails.Expect(
            iam_messages.GetPolicyDetailsRequest(
                pageToken=None,
                fullResourcePath='myresource',
            ),
            iam_messages.GetPolicyDetailsResponse(
                policies=[
                    iam_messages.PolicyDetail(fullResourcePath='c0'),
                    iam_messages.PolicyDetail(fullResourcePath='c1'),
                ],
            ))

        client = iam_client.IamV1(get_credentials=False)
        request = iam_messages.GetPolicyDetailsRequest(
            fullResourcePath='myresource')
        results = list_pager.YieldFromList(
            client.iamPolicies, request,
            batch_size_attribute=None,
            method='GetPolicyDetails', field='policies')

        i = 0
        for i, instance in enumerate(results):
            self.assertEquals('c{0}'.format(i), instance.fullResourcePath)
        self.assertEquals(1, i)
