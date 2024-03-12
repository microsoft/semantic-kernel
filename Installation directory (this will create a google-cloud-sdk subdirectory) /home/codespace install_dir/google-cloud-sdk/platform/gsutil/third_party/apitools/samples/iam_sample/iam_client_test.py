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

from apitools.base.py.testing import mock

from samples.iam_sample.iam_v1 import iam_v1_client  # nopep8
from samples.iam_sample.iam_v1 import iam_v1_messages  # nopep8


class DnsGenClientSanityTest(unittest.TestCase):

    def testBaseUrl(self):
        self.assertEquals(u'https://iam.googleapis.com/',
                          iam_v1_client.IamV1.BASE_URL)

    def testMessagesModule(self):
        self.assertEquals(iam_v1_messages, iam_v1_client.IamV1.MESSAGES_MODULE)

    def testAttributes(self):
        inner_classes = set([])
        for key, value in iam_v1_client.IamV1.__dict__.items():
            if isinstance(value, six.class_types):
                inner_classes.add(key)
        self.assertEquals(set([
            'IamPoliciesService',
            'ProjectsService',
            'ProjectsServiceAccountsKeysService',
            'ProjectsServiceAccountsService',
            'RolesService']), inner_classes)


class IamGenClientTest(unittest.TestCase):

    def setUp(self):
        self.mocked_iam_v1 = mock.Client(iam_v1_client.IamV1)
        self.mocked_iam_v1.Mock()
        self.addCleanup(self.mocked_iam_v1.Unmock)

    def testFlatPath(self):
        get_method_config = (self.mocked_iam_v1.projects_serviceAccounts_keys
                             .GetMethodConfig('Get'))
        self.assertEquals('v1/projects/{projectsId}/serviceAccounts'
                          '/{serviceAccountsId}/keys/{keysId}',
                          get_method_config.flat_path)
        self.assertEquals('v1/{+name}', get_method_config.relative_path)

    def testServiceAccountsKeysList(self):
        response_key = iam_v1_messages.ServiceAccountKey(
            name=u'test-key')
        self.mocked_iam_v1.projects_serviceAccounts_keys.List.Expect(
            iam_v1_messages.IamProjectsServiceAccountsKeysListRequest(
                name=u'test-service-account.'),
            iam_v1_messages.ListServiceAccountKeysResponse(
                keys=[response_key]))

        result = self.mocked_iam_v1.projects_serviceAccounts_keys.List(
            iam_v1_messages.IamProjectsServiceAccountsKeysListRequest(
                name=u'test-service-account.'))

        self.assertEquals([response_key], result.keys)
