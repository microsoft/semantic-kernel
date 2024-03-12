# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Integration tests for notification command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import re
import time
import uuid

import boto

from gslib.cloud_api_delegator import CloudApiDelegator
import gslib.tests.testcase as testcase
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import unittest
from gslib.utils.retry_util import Retry

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock


def _LoadNotificationUrl():
  return boto.config.get_value('GSUtil', 'test_notification_url')


NOTIFICATION_URL = _LoadNotificationUrl()


class TestNotificationUnit(testcase.GsUtilUnitTestCase):

  @mock.patch.object(CloudApiDelegator,
                     'CreateNotificationConfig',
                     autospec=True)
  def test_notification_splits_dash_m_value_correctly(self,
                                                      mock_create_notification):
    bucket_uri = self.CreateBucket(bucket_name='foo_notification')
    stdout = self.RunCommand(
        'notification',
        ['create', '-f', 'none', '-s', '-m', 'foo:bar:baz',
         suri(bucket_uri)],
        return_stdout=True)
    mock_create_notification.assert_called_once_with(
        mock.ANY,  # Client instance.
        'foo_notification',
        pubsub_topic=mock.ANY,
        payload_format=mock.ANY,
        custom_attributes={'foo': 'bar:baz'},
        event_types=None,
        object_name_prefix=mock.ANY,
        provider=mock.ANY)


class TestNotification(testcase.GsUtilIntegrationTestCase):
  """Integration tests for notification command."""

  @unittest.skipUnless(NOTIFICATION_URL,
                       'Test requires notification URL configuration.')
  def test_watch_bucket(self):
    """Tests creating a notification channel on a bucket."""
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(
        ['notification', 'watchbucket', NOTIFICATION_URL,
         suri(bucket_uri)])

    identifier = str(uuid.uuid4())
    token = str(uuid.uuid4())
    stderr = self.RunGsUtil([
        'notification', 'watchbucket', '-i', identifier, '-t', token,
        NOTIFICATION_URL,
        suri(bucket_uri)
    ],
                            return_stderr=True)
    self.assertIn('token: %s' % token, stderr)
    self.assertIn('identifier: %s' % identifier, stderr)

  @unittest.skipUnless(NOTIFICATION_URL,
                       'Test requires notification URL configuration.')
  def test_stop_channel(self):
    """Tests stopping a notification channel on a bucket."""
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(
        ['notification', 'watchbucket', NOTIFICATION_URL,
         suri(bucket_uri)],
        return_stderr=True)

    channel_id = re.findall(r'channel identifier: (?P<id>.*)', stderr)
    self.assertEqual(len(channel_id), 1)
    resource_id = re.findall(r'resource identifier: (?P<id>.*)', stderr)
    self.assertEqual(len(resource_id), 1)

    channel_id = channel_id[0]
    resource_id = resource_id[0]

    self.RunGsUtil(['notification', 'stopchannel', channel_id, resource_id])

  @unittest.skipUnless(NOTIFICATION_URL,
                       'Test requires notification URL configuration.')
  def test_list_one_channel(self):
    """Tests listing notification channel on a bucket."""
    # TODO(b/132277269): Re-enable these once the service-side bug is fixed.
    return unittest.skip('Functionality has been disabled due to b/132277269')

    bucket_uri = self.CreateBucket()

    # Set up an OCN (object change notification) on the newly created bucket.
    self.RunGsUtil(
        ['notification', 'watchbucket', NOTIFICATION_URL,
         suri(bucket_uri)],
        return_stderr=False)
    # The OCN listing in the service is eventually consistent. In initial
    # tests, it almost never was ready immediately after calling WatchBucket
    # above, so we A) sleep for a few seconds before the first OCN listing
    # attempt, and B) wrap the OCN listing attempt in retry logic in case
    # it raises a BucketNotFoundException (note that RunGsUtil will raise this
    # as an AssertionError due to the exit status not being 0).
    @Retry(AssertionError, tries=3, timeout_secs=5)
    def _ListObjectChangeNotifications():
      stderr = self.RunGsUtil(['notification', 'list', '-o',
                               suri(bucket_uri)],
                              return_stderr=True)
      return stderr

    time.sleep(5)
    stderr = _ListObjectChangeNotifications()

    channel_id = re.findall(r'Channel identifier: (?P<id>.*)', stderr)
    self.assertEqual(len(channel_id), 1)
    resource_id = re.findall(r'Resource identifier: (?P<id>.*)', stderr)
    self.assertEqual(len(resource_id), 1)
    push_url = re.findall(r'Application URL: (?P<id>.*)', stderr)
    self.assertEqual(len(push_url), 1)
    subscriber_email = re.findall(r'Created by: (?P<id>.*)', stderr)
    self.assertEqual(len(subscriber_email), 1)
    creation_time = re.findall(r'Creation time: (?P<id>.*)', stderr)
    self.assertEqual(len(creation_time), 1)

  def test_invalid_subcommand(self):
    stderr = self.RunGsUtil(['notification', 'foo', 'bar', 'baz'],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('Invalid subcommand', stderr)
