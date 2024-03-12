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
"""Implementation of managed-folders get-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import storage_url


class GetIamPolicy(base.Command):
  """Get the IAM policy for a managed folder."""

  detailed_help = {
      'DESCRIPTION': """
      Get the IAM policy for a managed folder. For more information, see [Cloud
      Identity and Access
      Management](https://cloud.google.com/storage/docs/access-control/iam).
      """,
      'EXAMPLES': """
      To get the IAM policy for a managed folder `managed-folder` in a bucket `bucket`:

        $ {command} gs://bucket/managed-folder/

      To output the IAM policy for `gs://bucket/managed-folder` to a file:

        $ {command} gs://bucket/managed-folder/ > policy.txt
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', help='URL of the managed folder to get the IAM policy of.'
    )

  def Run(self, args):
    url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_managed_folder(args.command_path, url)
    client = api_factory.get_api(url.scheme)
    return client.get_managed_folder_iam_policy(
        url.bucket_name, url.object_name
    )
