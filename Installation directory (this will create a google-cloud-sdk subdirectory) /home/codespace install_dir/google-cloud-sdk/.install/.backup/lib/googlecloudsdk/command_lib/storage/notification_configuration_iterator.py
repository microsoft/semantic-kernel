# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for expanding and matching GCS notification configurations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import re

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator

NotificationIteratorResult = collections.namedtuple(
    'NotificationIteratorResult', ['bucket_url', 'notification_configuration'])

# Notification names might look like one of these:
# -Canonical:  projects/_/buckets/some-bucket/notificationConfigs/some-id
# -JSON API:   b/some-bucket/notificationConfigs/some-id
# Either of the above might start with "/"" if a user is copying & pasting.
_NOTIFICATION_CONFIGURATION_REGEX_TAIL = (
    '/(?P<bucket_name>[^/]+)/notificationConfigs/(?P<notification_id>.+)')
_CANONICAL_NOTIFICATION_CONFIGURATION_REGEX = re.compile(
    '/?(projects/[^/]+/)?buckets' + _NOTIFICATION_CONFIGURATION_REGEX_TAIL)
_JSON_NOTIFICATION_CONFIGURATION_REGEX = re.compile(
    '/?b' + _NOTIFICATION_CONFIGURATION_REGEX_TAIL)


def get_bucket_url_and_notification_id_from_url(url_string):
  """Extracts bucket StorageUrl and notification_id string from URL."""
  match = (
      _CANONICAL_NOTIFICATION_CONFIGURATION_REGEX.match(url_string) or
      _JSON_NOTIFICATION_CONFIGURATION_REGEX.match(url_string))
  if match:
    return (storage_url.CloudUrl(storage_url.ProviderPrefix.GCS,
                                 match.group('bucket_name')),
            match.group('notification_id'))
  return None, None


def raise_error_if_not_gcs_bucket_matching_url(url):
  """Raises error if URL is not supported for notifications."""
  if not (url.scheme is storage_url.ProviderPrefix.GCS and
          (url.is_bucket() or url.is_provider())):
    raise errors.InvalidUrlError(
        'Notification configurations available on only'
        ' Google Cloud Storage buckets. Invalid URL: ' + url.url_string)


def get_notification_configuration_iterator(
    urls, accept_notification_configuration_urls=True):
  """Yields bucket/notification tuples from command-line args.

  Given a list of strings that are bucket URLs ("gs://foo") or notification
  configuration URLs ("b/bucket/notificationConfigs/5"), yield tuples of
  bucket names and their associated notifications.

  Args:
    urls (list[str]): Bucket and notification configuration URLs to pull
      notification configurations from.
    accept_notification_configuration_urls (bool): Whether to raise an an error
      if a notification configuration URL is in `urls`.

  Yields:
    NotificationIteratorResult

  Raises:
    InvalidUrlError: Received notification configuration URL, but
      accept_notification_configuration_urls was False. Or received non-GCS
      bucket URL.
  """
  client = api_factory.get_api(storage_url.ProviderPrefix.GCS)

  for url in urls:
    bucket_url, notification_id = (
        get_bucket_url_and_notification_id_from_url(url))
    if notification_id:
      if not accept_notification_configuration_urls:
        raise errors.InvalidUrlError(
            'Received disallowed notification configuration URL: ' + url)

      notification_configuration = client.get_notification_configuration(
          bucket_url, notification_id)
      yield NotificationIteratorResult(bucket_url, notification_configuration)

    else:
      cloud_url = storage_url.storage_url_from_string(url)
      raise_error_if_not_gcs_bucket_matching_url(cloud_url)
      if cloud_url.is_provider():
        bucket_url = storage_url.CloudUrl(storage_url.ProviderPrefix.GCS, '*')
      else:
        bucket_url = cloud_url

      for bucket_resource in wildcard_iterator.get_wildcard_iterator(
          bucket_url.url_string, fields_scope=cloud_api.FieldsScope.SHORT):
        for notification_configuration in (
            client.list_notification_configurations(
                bucket_resource.storage_url)):
          yield NotificationIteratorResult(bucket_resource.storage_url,
                                           notification_configuration)
