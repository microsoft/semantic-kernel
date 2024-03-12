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
"""Implementation of create command for making managed folders."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import log


class Create(base.Command):
  """Create managed folders."""

  detailed_help = {
      'DESCRIPTION': 'Create managed folders.',
      'EXAMPLES': """
      The following command creates a managed folder called `folder/` in a bucket
      named `my-bucket`:

        $ {command} gs://my-bucket/folder/
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', type=str, nargs='+', help='The URLs of the folders to create.'
    )

    flags.add_additional_headers_flag(parser)

  def Run(self, args):
    urls = []
    for url_string in args.url:
      url = storage_url.storage_url_from_string(url_string)
      errors_util.raise_error_if_not_gcs_managed_folder(args.command_path, url)
      urls.append(url)

    for url in urls:
      client = api_factory.get_api(url.scheme)
      log.status.Print('Creating {}...'.format(url))
      client.create_managed_folder(url.bucket_name, url.object_name)
