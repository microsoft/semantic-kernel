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

"""Command to show metadata of a notification configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import notification_configuration_iterator
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core.resource import resource_projector


class Describe(base.DescribeCommand):
  """Show metadata for a notification configuration."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* prints populated metadata for a notification configuration.
      """,
      'EXAMPLES':
          """
      Describe a single notification configuration (with ID 3) in the
      bucket `example-bucket`:

        $ {command} projects/_/buckets/example-bucket/notificationConfigs/3
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('url', help='The url of the notification configuration')

  def Run(self, args):
    bucket_url, notification_id = (
        notification_configuration_iterator
        .get_bucket_url_and_notification_id_from_url(args.url))
    if not (bucket_url and notification_id):
      raise errors.InvalidUrlError(
          'Received invalid notification configuration URL: ' + args.url)
    return resource_projector.MakeSerializable(
        api_factory.get_api(
            storage_url.ProviderPrefix.GCS).get_notification_configuration(
                bucket_url, notification_id))
