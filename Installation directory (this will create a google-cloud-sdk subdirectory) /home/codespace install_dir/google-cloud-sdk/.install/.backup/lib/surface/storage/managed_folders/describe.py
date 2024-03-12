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
"""Implementation of command for describing managed folders."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import full_resource_formatter
from googlecloudsdk.command_lib.storage.resources import resource_util


class Describe(base.Command):
  """Describe managed folders."""

  detailed_help = {
      'DESCRIPTION': """Describe managed folders.""",
      'EXAMPLES': """
      The following command shows information about a managed folder named
      `folder` in a bucket called `my-bucket`:

        $ {command} gs://my-bucket/folder/
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        type=str,
        help='The URL of the managed folder to describe.',
    )
    flags.add_additional_headers_flag(parser)
    flags.add_raw_display_flag(parser)

  def Run(self, args):
    url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_managed_folder(args.command_path, url)
    client = api_factory.get_api(url.scheme)
    resource = client.get_managed_folder(
        url.bucket_name,
        url.object_name,
    )
    return resource_util.get_display_dict_for_resource(
        resource,
        full_resource_formatter.ManagedFolderDisplayTitlesAndDefaults,
        display_raw_keys=args.raw,
    )
