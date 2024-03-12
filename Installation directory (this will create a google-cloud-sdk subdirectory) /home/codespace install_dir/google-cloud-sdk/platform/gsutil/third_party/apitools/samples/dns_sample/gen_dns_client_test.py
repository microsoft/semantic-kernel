#
# Copyright 2016 Google Inc.
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

"""Test for generated sample module."""

import unittest

import six

from apitools.base.py import list_pager
from apitools.base.py.testing import mock

from samples.dns_sample.dns_v1 import dns_v1_client
from samples.dns_sample.dns_v1 import dns_v1_messages


class DnsGenClientSanityTest(unittest.TestCase):

    def testBaseUrl(self):
        self.assertEquals(u'https://www.googleapis.com/dns/v1/',
                          dns_v1_client.DnsV1.BASE_URL)

    def testMessagesModule(self):
        self.assertEquals(dns_v1_messages, dns_v1_client.DnsV1.MESSAGES_MODULE)

    def testAttributes(self):
        inner_classes = set([])
        for key, value in dns_v1_client.DnsV1.__dict__.items():
            if isinstance(value, six.class_types):
                inner_classes.add(key)
        self.assertEquals(set([
            'ChangesService',
            'ProjectsService',
            'ManagedZonesService',
            'ResourceRecordSetsService']), inner_classes)


class DnsGenClientTest(unittest.TestCase):

    def setUp(self):
        self.mocked_dns_v1 = mock.Client(dns_v1_client.DnsV1)
        self.mocked_dns_v1.Mock()
        self.addCleanup(self.mocked_dns_v1.Unmock)

    def testFlatPath(self):
        get_method_config = self.mocked_dns_v1.projects.GetMethodConfig('Get')
        self.assertIsNone(get_method_config.flat_path)
        self.assertEquals('projects/{project}',
                          get_method_config.relative_path)

    def testRecordSetList(self):
        response_record_set = dns_v1_messages.ResourceRecordSet(
            kind=u"dns#resourceRecordSet",
            name=u"zone.com.",
            rrdatas=[u"1.2.3.4"],
            ttl=21600,
            type=u"A")
        self.mocked_dns_v1.resourceRecordSets.List.Expect(
            dns_v1_messages.DnsResourceRecordSetsListRequest(
                project=u'my-project',
                managedZone=u'test_zone_name',
                type=u'green',
                maxResults=100),
            dns_v1_messages.ResourceRecordSetsListResponse(
                rrsets=[response_record_set]))

        results = list(list_pager.YieldFromList(
            self.mocked_dns_v1.resourceRecordSets,
            dns_v1_messages.DnsResourceRecordSetsListRequest(
                project='my-project',
                managedZone='test_zone_name',
                type='green'),
            limit=100, field='rrsets'))

        self.assertEquals([response_record_set], results)
