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

"""Command to list notification configurations belonging to a bucket."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import notification_configuration_iterator
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_projector


_PUBSUB_DOMAIN_PREFIX_LENGTH = len('//pubsub.googleapis.com/')


def _get_human_readable_notification(url, config):
  """Returns pretty notification string."""
  if config.custom_attributes:
    custom_attributes_string = '\n\tCustom attributes:'
    for attribute in config.custom_attributes.additionalProperties:
      custom_attributes_string += '\n\t\t{}: {}'.format(
          attribute.key, attribute.value
      )
  else:
    custom_attributes_string = ''

  if config.event_types or config.object_name_prefix:
    filters_string = '\n\tFilters:'

    if config.event_types:
      filters_string += '\n\t\tEvent Types: {}'.format(
          ', '.join(config.event_types)
      )
    if config.object_name_prefix:
      filters_string += "\n\t\tObject name prefix: '{}'".format(
          config.object_name_prefix
      )
  else:
    filters_string = ''

  return (
      'projects/_/buckets/{bucket}/notificationConfigs/{notification}\n'
      '\tCloud Pub/Sub topic: {topic}'
      '{custom_attributes}{filters}\n\n'.format(
          bucket=url.bucket_name,
          notification=config.id,
          topic=config.topic[_PUBSUB_DOMAIN_PREFIX_LENGTH:],
          custom_attributes=custom_attributes_string,
          filters=filters_string,
      )
  )


class List(base.ListCommand):
  """List the notification configurations belonging to a given bucket."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* provides a list of notification configurations belonging to a
      given bucket. The listed name of each configuration can be used
      with the delete sub-command to delete that specific notification config.
      """,
      'EXAMPLES':
          """
      Fetch the list of notification configs for the bucket `example-bucket`:

        $ {command} gs://example-bucket

      Fetch the notification configs in all buckets matching a wildcard:

        $ {command} gs://example-*

      Fetch all of the notification configs for buckets in the default project:

        $ {command}
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'urls',
        nargs='*',
        help='Google Cloud Storage bucket paths. The path must begin '
        'with gs:// and may contain wildcard characters.')
    parser.add_argument(
        '--human-readable',
        action='store_true',
        # Used by shim. Could be public but don't want maintainence burden.
        hidden=True,
        help=(
            'Prints notification information in a more descriptive,'
            ' unstructured format.'
        ),
    )

  def Display(self, args, resources):
    if args.human_readable:
      resource_printer.Print(resources, 'object')
    else:
      resource_printer.Print(resources, args.format or 'yaml')

  def Run(self, args):
    if not args.urls:
      # Provider URL will fetch all notification configurations in project.
      urls = ['gs://']
    else:
      urls = args.urls

    # Not bucket URLs raise error in iterator.
    for notification_configuration_iterator_result in (
        notification_configuration_iterator
        .get_notification_configuration_iterator(
            urls, accept_notification_configuration_urls=False)):

      url, config = notification_configuration_iterator_result
      if args.human_readable:
        yield _get_human_readable_notification(url, config)
      else:
        yield {
            'Bucket URL': url.url_string,
            'Notification Configuration': resource_projector.MakeSerializable(
                config
            ),
        }
