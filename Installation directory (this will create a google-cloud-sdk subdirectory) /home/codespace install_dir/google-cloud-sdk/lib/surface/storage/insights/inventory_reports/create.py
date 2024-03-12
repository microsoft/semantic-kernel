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
"""Implementation of create command for inventory reports."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import log


class Create(base.Command):
  """Create a new inventory report config."""

  detailed_help = {
      'DESCRIPTION': """
       Create an inventory report config that defines how often
       inventory reports are generated, the metadata fields you want the reports
       to include, and a bucket/prefix in which to store the reports, also known
       as the destination.
      """,
      'EXAMPLES': """
       To create an inventory report about "my-bucket" that will store report
       details in "report-bucket" with the prefix "save-path/".

         $ {command} gs://my-bucket --destination=gs://report-bucket/save-path/
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'source_bucket_url',
        type=str,
        help='URL of the source bucket that will contain the '
             'inventory report configuration.')
    flags.add_inventory_reports_flags(parser, require_create_flags=True)

  def Run(self, args):
    source_bucket = storage_url.storage_url_from_string(
        storage_url.add_gcs_scheme_if_missing(args.source_bucket_url))
    if (not isinstance(source_bucket, storage_url.CloudUrl) or
        not source_bucket.is_bucket()):
      raise errors.InvalidUrlError(
          'Invalid bucket URL: {}. Only bucket URLs are accepted'
          ' for SOURCE_BUCKET_URL. Example: "gs://bucket"'.format(
              args.source_bucket_url))

    if args.destination is not None:
      destination = storage_url.storage_url_from_string(
          storage_url.add_gcs_scheme_if_missing(args.destination))
    else:
      destination = storage_url.CloudUrl(
          scheme=source_bucket.scheme,
          bucket_name=source_bucket.bucket_name,
          object_name='inventory_reports/')

    if args.schedule_starts is not None:
      start_date = args.schedule_starts
    else:
      start_date = (datetime.datetime.now(datetime.timezone.utc) +
                    datetime.timedelta(days=1)).date()

    if args.schedule_repeats_until is not None:
      end_date = args.schedule_repeats_until
    else:
      end_date = start_date + datetime.timedelta(days=365)

    report_config = insights_api.InsightsApi().create_inventory_report(
        source_bucket=source_bucket.bucket_name,
        destination_url=destination,
        metadata_fields=list(args.metadata_fields),
        start_date=start_date,
        end_date=end_date,
        frequency=args.schedule_repeats,
        csv_delimiter=args.csv_delimiter,
        csv_separator=args.csv_separator,
        csv_header=args.csv_header,
        parquet=args.parquet,
        display_name=args.display_name,
    )
    log.status.Print(
        'Created report configuration: {}'.format(report_config.name))
