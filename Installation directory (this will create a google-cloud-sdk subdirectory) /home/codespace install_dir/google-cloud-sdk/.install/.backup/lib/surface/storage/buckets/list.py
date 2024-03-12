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
"""Implementation of buckets list command for getting info on buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import full_resource_formatter
from googlecloudsdk.command_lib.storage.resources import resource_util


class List(base.ListCommand):
  """Lists Cloud Storage buckets."""

  detailed_help = {
      'DESCRIPTION':
          """
      List Cloud Storage buckets.
      """,
      'EXAMPLES':
          """

      List all Google Cloud Storage buckets in default project:

        $ {command}

      List buckets beginning with ``b'':

        $ {command} gs://b*

      List buckets with JSON formatting, only returning the ``name'' key:

        $ {command} --format="json(name)"
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'urls', nargs='*', help='Specifies URL of buckets to List.')
    flags.add_additional_headers_flag(parser)
    flags.add_raw_display_flag(parser)
    flags.add_uri_support_to_list_commands(parser)

  def Run(self, args):
    if args.urls:
      urls = []
      for url_string in args.urls:
        url = storage_url.storage_url_from_string(url_string)
        if not (url.is_provider() or url.is_bucket()):
          raise errors.InvalidUrlError(
              'URL does not match buckets: {}'.format(url_string))
        urls.append(url)
    else:
      urls = [storage_url.CloudUrl(storage_url.ProviderPrefix.GCS)]

    for url in urls:
      for bucket in wildcard_iterator.get_wildcard_iterator(
          url.url_string,
          fields_scope=cloud_api.FieldsScope.FULL,
          get_bucket_metadata=True,
      ):
        yield resource_util.get_display_dict_for_resource(
            bucket,
            full_resource_formatter.BucketDisplayTitlesAndDefaults,
            display_raw_keys=args.raw,
        )
