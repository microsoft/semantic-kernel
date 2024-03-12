# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for setting usage buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
import six


class SetUsageBucket(base.SilentCommand):
  """Set usage reporting bucket for a project.

    *{command}* configures usage reporting for projects.

  Setting usage reporting will cause a log of usage per resource to be
  written to a specified Google Cloud Storage bucket daily.

  For example, to write daily logs of the form usage_gce_YYYYMMDD.csv
  to the bucket `my-bucket`, run:

    $ gcloud compute project-info set-usage-bucket --bucket=gs://my-bucket

  To disable this feature, issue the command:

    $ gcloud compute project-info set-usage-bucket --no-bucket
  """

  @staticmethod
  def Args(parser):
    bucket_group = parser.add_mutually_exclusive_group(required=True)
    bucket_group.add_argument(
        '--no-bucket', action='store_true',
        help='Unsets the bucket. This disables usage report storage.')
    bucket_group.add_argument(
        '--bucket',
        help="""\
        Name of an existing Google Cloud Storage bucket where the usage
        report object should be stored. This can either be the bucket name by
        itself, such as `my-bucket`, or the bucket name with `gs://`
        or `https://storage.googleapis.com/` in front of it, such as
        `gs://my-bucket`. The Google Service Account for
        performing usage reporting is granted write access to this bucket.
        The user running this command must be an owner of the bucket.

        To clear the usage bucket, use `--no-bucket`.
        """)

    parser.add_argument(
        '--prefix',
        help="""\
        Optional prefix for the name of the usage report object stored in
        the bucket. If not supplied, then this defaults to ``usage''. The
        report is stored as a CSV file named PREFIX_gce_YYYYMMDD.csv where
        YYYYMMDD is the day of the usage according to Pacific Time. The prefix
        should conform to Google Cloud Storage object naming conventions.
        This flag must not be provided when clearing the usage bucket.
        """)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    if not args.bucket and args.prefix:
      raise compute_exceptions.ArgumentError(
          '[--prefix] cannot be specified when unsetting the usage bucket.')

    bucket_uri = None
    if args.bucket:
      bucket_uri = six.text_type(resources.REGISTRY.Parse(args.bucket))

    request = client.messages.ComputeProjectsSetUsageExportBucketRequest(
        project=properties.VALUES.core.project.GetOrFail(),
        usageExportLocation=client.messages.UsageExportLocation(
            bucketName=bucket_uri,
            reportNamePrefix=args.prefix,
        )
    )

    return client.MakeRequests([(client.apitools_client.projects,
                                 'SetUsageExportBucket', request)])
