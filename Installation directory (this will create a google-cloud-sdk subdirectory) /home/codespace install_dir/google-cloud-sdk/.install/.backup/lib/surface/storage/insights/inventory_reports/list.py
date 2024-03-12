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
"""Implementation of insights inventory-reports list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url


class List(base.ListCommand):
  """Lists all inventory report configs."""

  detailed_help = {
      'DESCRIPTION':
          """
      List Cloud Storage inventory report configs.
      """,
      'EXAMPLES':
          """

      List all inventory report configs in the source bucket
      "my-bucket":

        $ {command} --source=gs://my-bucket

      List buckets with JSON formatting, only returning the "displayName" field:

        $ {command} --source=gs://my-bucket --format="json(displayName)"
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--source',
        metavar='SOURCE_BUCKET_URL',
        help='Specifies URL of the source bucket that contains the inventory '
             'report configuration.')
    parser.add_argument(
        '--location',
        help='The location of the report configs.')
    parser.display_info.AddFormat(
        """
        table(
            format('{}',name.basename()):label=REPORT_CONFIG_ID,
            format(
                '{:04d}-{:02d}-{:02d}',
                frequencyOptions.startDate.year,
                frequencyOptions.startDate.month,
                frequencyOptions.startDate.day):label=START_DATE,
            format(
                '{:04d}-{:02d}-{:02d}',
                frequencyOptions.endDate.year,
                frequencyOptions.endDate.month,
                frequencyOptions.endDate.day):label=END_DATE,
            format(
                'gs://{}',
                objectMetadataReportOptions.storageFilters.bucket
            ):label=SOURCE_BUCKET:wrap,
            format(
                'gs://{}/{}',
                objectMetadataReportOptions.storageDestinationOptions.bucket,
                objectMetadataReportOptions.storageDestinationOptions.
                destinationPath.flatten()):label=DESTINATION:wrap
        )
        """
    )

  def Run(self, args):
    if args.source is None and args.location is None:
      raise errors.Error(
          'At least one of --source or --location is required.')

    source_bucket = storage_url.storage_url_from_string(
        args.source) if args.source is not None else None

    return insights_api.InsightsApi().list_inventory_reports(
        source_bucket, location=args.location, page_size=args.page_size
    )
