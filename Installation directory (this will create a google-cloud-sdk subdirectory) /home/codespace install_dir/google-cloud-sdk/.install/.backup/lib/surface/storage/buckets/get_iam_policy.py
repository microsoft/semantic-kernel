# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of buckets get-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import iam_command_util
from googlecloudsdk.command_lib.storage import storage_url


class GetIamPolicy(base.Command):
  """Get the IAM policy for a bucket."""

  detailed_help = {
      'DESCRIPTION':
          """
      Get the IAM policy for a bucket. For more information, see [Cloud
      Identity and Access
      Management](https://cloud.google.com/storage/docs/access-control/iam).
      """,
      'EXAMPLES':
          """
      To get the IAM policy for BUCKET:

        $ {command} gs://BUCKET

      To output the IAM policy for BUCKET to a file:

        $ {command} gs://BUCKET > policy.txt
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('url', help='Request IAM policy for this bucket.')

  def Run(self, args):
    url_object = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_bucket(args.command_path, url_object)
    matching_url = iam_command_util.get_single_matching_url(args.url)
    return api_factory.get_api(matching_url.scheme).get_bucket_iam_policy(
        matching_url.bucket_name)
