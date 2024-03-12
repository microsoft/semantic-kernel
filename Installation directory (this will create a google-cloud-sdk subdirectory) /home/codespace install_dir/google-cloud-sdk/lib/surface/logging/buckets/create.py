# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""'logging buckets create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(base.CreateCommand):
  """Create a bucket.

  After creating a bucket, use a log sink to route logs into the bucket.

  ## EXAMPLES

  To create a bucket 'my-bucket' in location 'global', run:

    $ {command} my-bucket --location=global --description="my custom bucket"

  To create a bucket with extended retention, run:

    $ {command} my-bucket --location=global --retention-days=365

  To create a bucket in cloud region 'us-central1', run:

    $ {command} my-bucket --location=us-central1

  To create a bucket with custom index of 'jsonPayload.foo', run:

    $ {command} my-bucket
      --index=fieldPath=jsonPayload.foo,type=INDEX_TYPE_STRING

  To create a bucket with custom CMEK, run:

    $ {command} my-bucket --location=us-central1
      --cmek-kms-key-name=CMEK_KMS_KEY_NAME

  To asynchronously create a bucket enrolled into Log Analytics, run:

    $ {command} my-bucket --location=global --async --enable-analytics
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('BUCKET_ID', help='ID of the bucket to create.')
    parser.add_argument(
        '--description', help='A textual description for the bucket.')
    parser.add_argument(
        '--restricted-fields',
        help='Comma-separated list of field paths that require permission '
        'checks in this bucket. The following fields and their children are '
        'eligible: textPayload, jsonPayload, protoPayload, httpRequest, labels,'
        ' sourceLocation.',
        type=arg_parsers.ArgList(),
        metavar='RESTRICTED_FIELD',
    )
    parser.add_argument(
        '--retention-days',
        type=int,
        help='The period logs will be retained, after which logs will '
        'automatically be deleted. The default is 30 days.')
    parser.add_argument(
        '--index',
        action='append',
        type=arg_parsers.ArgDict(
            spec={
                'fieldPath': str,
                'type': util.IndexTypeToEnum
            },
            required_keys=['fieldPath', 'type']),
        metavar='KEY=VALUE, ...',
        help=(
            'Specify an index to be added to the log bucket. This flag can be '
            'repeated. The ``fieldPath\'\' and ``type\'\' attributes are '
            'required. For example: '
            ' --index=fieldPath=jsonPayload.foo,type=INDEX_TYPE_STRING. '
            'The following keys are accepted:\n\n'
            '*fieldPath*::: The LogEntry field path to index. '
            'For example: jsonPayload.request.status. '
            'Paths are limited to 800 characters and can include only '
            'letters, digits, underscores, hyphens, and periods.\n\n'
            '*type*::: The type of data in this index. '
            'For example: INDEX_TYPE_STRING '
            'Supported types are INDEX_TYPE_STRING and '
            'INDEX_TYPE_INTEGER. \n\n '))
    parser.add_argument(
        '--cmek-kms-key-name',
        help='A valid `kms_key_name` will enable CMEK for the bucket.')
    parser.add_argument(
        '--enable-analytics',
        action='store_true',
        default=None,
        help=(
            'Whether to opt the bucket into Log Analytics. Once opted in, the'
            ' bucket cannot be opted out of Log Analytics.'
        ),
    )
    base.ASYNC_FLAG.AddToParser(parser)
    util.AddBucketLocationArg(
        parser, True,
        'Location in which to create the bucket. Once the bucket is created, '
        'the location cannot be changed.')

  def _Run(self, args):
    bucket_data = {}
    if args.IsSpecified('retention_days'):
      bucket_data['retentionDays'] = args.retention_days
    if args.IsSpecified('description'):
      bucket_data['description'] = args.description
    if args.IsSpecified('restricted_fields'):
      bucket_data['restrictedFields'] = args.restricted_fields
    if args.IsSpecified('index'):
      bucket_data['indexConfigs'] = args.index

    if args.IsSpecified('enable_analytics'):
      bucket_data['analyticsEnabled'] = args.enable_analytics

    if args.IsSpecified('cmek_kms_key_name'):
      console_io.PromptContinue(
          'CMEK cannot be disabled on a bucket once enabled.',
          cancel_on_no=True)
      cmek_settings = util.GetMessages().CmekSettings(
          kmsKeyName=args.cmek_kms_key_name)
      bucket_data['cmekSettings'] = cmek_settings

    if args.async_:
      result = util.GetClient().projects_locations_buckets.CreateAsync(
          util.GetMessages().LoggingProjectsLocationsBucketsCreateAsyncRequest(
              bucketId=args.BUCKET_ID,
              parent=util.CreateResourceName(
                  util.GetProjectResource(args.project).RelativeName(),
                  'locations',
                  args.location,
              ),
              logBucket=util.GetMessages().LogBucket(**bucket_data),
          )
      )
      log.CreatedResource(result.name, 'bucket', is_async=True)
      return result
    else:
      return util.GetClient().projects_locations_buckets.Create(
          util.GetMessages().LoggingProjectsLocationsBucketsCreateRequest(
              bucketId=args.BUCKET_ID,
              parent=util.CreateResourceName(
                  util.GetProjectResource(args.project).RelativeName(),
                  'locations',
                  args.location,
              ),
              logBucket=util.GetMessages().LogBucket(**bucket_data),
          )
      )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The created bucket.
    """
    return self._Run(args)
