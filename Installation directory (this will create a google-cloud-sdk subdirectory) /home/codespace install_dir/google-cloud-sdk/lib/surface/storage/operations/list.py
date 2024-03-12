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
"""Command to list storage operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import operations_util
from googlecloudsdk.command_lib.storage import storage_url


class List(base.ListCommand):
  """List storage operations."""

  detailed_help = {
      'DESCRIPTION': """\
      List storage operations.
      """,
      'EXAMPLES': """\
      To list all storage operations that belong to the bucket "my-bucket", run:

        $ {command} projects/_/buckets/my-bucket

      To list operations in JSON format, run:

        $ {command} projects/_/buckets/my-bucket --format=json

      An alternative bucket format is available:

        $ {command} gs://my-bucket
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'parent_resource_name',
        help=(
            'The operation parent resource in the format'
            ' "projects/```_```/buckets/BUCKET".'
        ),
    )
    parser.add_argument(
        '--server-filter',
        help=(
            'Server-side filter string used to determine what operations to'
            " return. Example: '(done = true AND complete_time >="
            ' "2023-01-01T00:00:00Z") OR requested_cancellation = true\''
            ' Note that the entire filter string must be in quotes and'
            ' date strings within the filter must be in embedded quotes.'
        ),
    )

    # Unnecessary and unimplemented flags built into `ListCommand` base class.
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    url_object = storage_url.storage_url_from_string(args.parent_resource_name)
    if isinstance(url_object, storage_url.CloudUrl):
      errors_util.raise_error_if_not_gcs_bucket(args.command_path, url_object)
      bucket = url_object.bucket_name
    else:
      bucket = operations_util.get_operation_bucket_from_name(
          args.parent_resource_name
      )
    scheme = storage_url.ProviderPrefix.GCS
    return api_factory.get_api(scheme).list_operations(
        bucket_name=bucket,
        server_side_filter=args.server_filter,
    )
