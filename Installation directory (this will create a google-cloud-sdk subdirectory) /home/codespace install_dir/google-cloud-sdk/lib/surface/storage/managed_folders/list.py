# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Implementation of command for listing managed folders."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import folder_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import full_resource_formatter
from googlecloudsdk.command_lib.storage.resources import resource_util


class List(base.ListCommand):
  """List managed folders."""

  detailed_help = {
      'DESCRIPTION': """List managed folders.""",
      'EXAMPLES': """
      The following command lists all managed folders in a bucket:

        $ {command} gs://my-bucket/
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', type=str, nargs='+', help='The URLs of the resources to list.'
    )
    flags.add_additional_headers_flag(parser)
    flags.add_raw_display_flag(parser)

  def Run(self, args):
    urls = []
    for url_string in args.url:
      url = storage_url.storage_url_from_string(url_string)
      errors_util.raise_error_if_not_gcs(args.command_path, url)
      urls.append(url)

    for url in urls:
      for resource in wildcard_iterator.CloudWildcardIterator(
          url.join('**'),
          managed_folder_setting=folder_util.ManagedFolderSetting.LIST_WITHOUT_OBJECTS,
      ):
        yield resource_util.get_display_dict_for_resource(
            resource,
            full_resource_formatter.ManagedFolderDisplayTitlesAndDefaults,
            display_raw_keys=args.raw,
        )
