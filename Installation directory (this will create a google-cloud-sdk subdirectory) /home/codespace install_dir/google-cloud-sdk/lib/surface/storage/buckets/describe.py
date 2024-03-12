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
"""Implementation of buckets describe command for getting info on buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import full_resource_formatter
from googlecloudsdk.command_lib.storage.resources import gsutil_json_printer
from googlecloudsdk.command_lib.storage.resources import resource_util


class Describe(base.DescribeCommand):
  """Describes Cloud Storage buckets."""

  detailed_help = {
      'DESCRIPTION':
          """
      Describe a Cloud Storage bucket.
      """,
      'EXAMPLES':
          """

      Describe a Google Cloud Storage bucket named "my-bucket":

        $ {command} gs://my-bucket

      Describe bucket with JSON formatting, only returning the "name" key:

        $ {command} gs://my-bucket --format="json(name)"
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('url', help='Specifies URL of bucket to describe.')
    flags.add_additional_headers_flag(parser)
    flags.add_raw_display_flag(parser)
    gsutil_json_printer.GsutilJsonPrinter.Register()

  def Run(self, args):
    if wildcard_iterator.contains_wildcard(args.url):
      raise errors.InvalidUrlError(
          'Describe does not accept wildcards because it returns a single'
          ' resource. Please use the `ls` or `buckets list` command for'
          ' retrieving multiple resources.')
    url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_bucket(args.command_path, url)
    bucket_resource = api_factory.get_api(url.scheme).get_bucket(
        url.bucket_name, fields_scope=cloud_api.FieldsScope.FULL)

    return resource_util.get_display_dict_for_resource(
        bucket_resource,
        full_resource_formatter.BucketDisplayTitlesAndDefaults,
        display_raw_keys=args.raw,
    )
