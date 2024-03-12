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
"""'logging buckets update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'DESCRIPTION': """
        Update the properties of a bucket.
    """,
    'EXAMPLES': """
     To update a bucket in your project, run:

        $ {command} my-bucket --location=global --description=my-new-description

     To update a bucket in your project and remove all indexes, run:

        $ {command} my-bucket --location=global --clear-indexes

     To update a bucket in your project and remove an index, run:

        $ {command} my-bucket --location=global --remove-indexes=jsonPayload.foo2

     To update a bucket in your project and add an index, run:

        $ {command} my-bucket --location=global --add-index=fieldPath=jsonPayload.foo2,type=INDEX_TYPE_STRING

     To update a bucket in your project and update an existing index, run:

        $ {command} my-bucket --location=global --update-index=fieldPath=jsonPayload.foo,type=INDEX_TYPE_INTEGER

     To update a bucket in your project and update existing cmek, run:

        $ {command} my-bucket --location=global --cmek-kms-key-name=CMEK_KEY_NAME

     To asynchronously enroll a bucket in your project into Log Analytics, run:

        $ {command} my-bucket --location=global --async --enable-analytics
    """,
}


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Update(base.UpdateCommand):
  """Update a bucket.

  Changes one or more properties associated with a bucket.
  """

  def __init__(self, *args, **kwargs):
    super(Update, self).__init__(*args, **kwargs)
    self._current_bucket = None

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('BUCKET_ID', help='The id of the bucket to update.')
    parser.add_argument(
        '--retention-days',
        type=int,
        help='A new retention period for the bucket.')
    parser.add_argument(
        '--description', help='A new description for the bucket.')
    util.AddBucketLocationArg(parser, True, 'Location of the bucket.')
    parser.add_argument(
        '--locked',
        action='store_true',
        help=('Lock the bucket and prevent it from being modified or deleted '
              '(unless it is empty).'))
    parser.add_argument(
        '--restricted-fields',
        help='A new set of restricted fields for the bucket.',
        type=arg_parsers.ArgList(),
        metavar='RESTRICTED_FIELD')
    parser.add_argument(
        '--clear-indexes',
        action='store_true',
        help=('Remove all logging indexes from the bucket.'))
    parser.add_argument(
        '--remove-indexes',
        type=arg_parsers.ArgList(),
        metavar='FIELD PATH',
        help=('Specify the field path of the logging index(es) to delete.'))
    parser.add_argument(
        '--add-index',
        action='append',
        type=arg_parsers.ArgDict(
            spec={
                'fieldPath': str,
                'type': util.IndexTypeToEnum
            },
            required_keys=['fieldPath', 'type']),
        metavar='KEY=VALUE, ...',
        help=('Add an index to be added to the log bucket. This flag can be '
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
              'Supported types are strings and integers. \n\n '))
    parser.add_argument(
        '--update-index',
        action='append',
        type=arg_parsers.ArgDict(
            spec={
                'fieldPath': str,
                'type': util.IndexTypeToEnum
            },
            required_keys=['fieldPath', 'type']),
        metavar='KEY=VALUE, ...',
        help=(
            'Update an index to be added to the log bucket. '
            'This will update the type of the index, and also update its '
            'createTime to the new update time. '
            'This flag can be repeated. The ``fieldPath\'\' and ``type\'\' '
            'attributes are required. For example: '
            ' --index=fieldPath=jsonPayload.foo,type=INDEX_TYPE_STRING. '
            'The following keys are accepted:\n\n'
            '*fieldPath*::: The LogEntry field path to index. '
            'For example: jsonPayload.request.status. '
            'Paths are limited to 800 characters and can include only '
            'letters, digits, underscores, hyphens, and periods.\n\n'
            '*type*::: The type of data in this index. '
            'For example: INDEX_TYPE_STRING '
            'Supported types are strings and integers. '))
    parser.add_argument(
        '--enable-analytics',
        action='store_true',
        default=None,
        help=(
            'Whether to opt the bucket into Log Analytics. Once opted in, the'
            ' bucket cannot be opted out of Log Analytics.'
        ),
    )
    parser.add_argument(
        '--cmek-kms-key-name',
        help='A valid `kms_key_name` will enable CMEK for the bucket.')
    base.ASYNC_FLAG.AddToParser(parser)

  def GetCurrentBucket(self, args):
    """Returns a bucket specified by the arguments.

    Loads the current bucket at most once. If called multiple times, the
    previously-loaded bucket will be returned.

    Args:
      args: The argument set. This is not checked across GetCurrentBucket calls,
        and must be consistent.
    """
    if not self._current_bucket:
      return util.GetClient().projects_locations_buckets.Get(
          util.GetMessages().LoggingProjectsLocationsBucketsGetRequest(
              name=util.CreateResourceName(
                  util.CreateResourceName(
                      util.GetProjectResource(args.project).RelativeName(),
                      'locations', args.location), 'buckets', args.BUCKET_ID)))
    return self._current_bucket

  def _Run(self, args):
    bucket_data = {}
    update_mask = []
    parameter_names = ['--retention-days', '--description', '--locked']
    if args.IsSpecified('retention_days'):
      bucket_data['retentionDays'] = args.retention_days
      update_mask.append('retention_days')
    if args.IsSpecified('description'):
      bucket_data['description'] = args.description
      update_mask.append('description')
    if args.IsSpecified('locked'):
      bucket_data['locked'] = args.locked
      update_mask.append('locked')
      if args.locked:
        console_io.PromptContinue(
            'WARNING: Locking a bucket cannot be undone.',
            default=False,
            cancel_on_no=True)
    if args.IsSpecified('restricted_fields'):
      bucket_data['restrictedFields'] = args.restricted_fields
      update_mask.append('restricted_fields')

    if args.IsSpecified('enable_analytics'):
      bucket_data['analyticsEnabled'] = args.enable_analytics
      update_mask.append('analytics_enabled')

    if (args.IsSpecified('clear_indexes') or
        args.IsSpecified('remove_indexes') or args.IsSpecified('add_index') or
        args.IsSpecified('update_index')):
      bucket = self.GetCurrentBucket(args)
      bucket_data['indexConfigs'] = []
      update_mask.append('index_configs')
      indexes_to_remove = (
          args.remove_indexes if args.IsSpecified('remove_indexes') else [])
      indexes_to_update = (
          args.update_index if args.IsSpecified('update_index') else [])
      for index in bucket.indexConfigs:
        if index.fieldPath in indexes_to_remove:
          indexes_to_remove.remove(index.fieldPath)
        else:
          for i in range(len(indexes_to_update)):
            if index.fieldPath == indexes_to_update[i]['fieldPath']:
              for key, value in indexes_to_update[i].items():
                if key == 'type':
                  index.type = value
              indexes_to_update.pop(i)
              break
          bucket_data['indexConfigs'].append(index)

      if indexes_to_remove:
        raise calliope_exceptions.InvalidArgumentException(
            '--remove-indexes',
            'Indexes {0} do not exist'.format(','.join(indexes_to_remove)))

      if indexes_to_update:
        raise calliope_exceptions.InvalidArgumentException(
            '--update-index', 'Indexes {0} do not exist'.format(','.join(
                [index['fieldPath'] for index in indexes_to_update])))

      if args.IsSpecified('clear_indexes'):
        bucket_data['indexConfigs'] = []

      if args.IsSpecified('add_index'):
        bucket_data['indexConfigs'] += args.add_index

    if args.IsSpecified('cmek_kms_key_name'):
      bucket = self.GetCurrentBucket(args)
      if not bucket.cmekSettings:
        # This is the first time CMEK settings are being applied. Warn the user
        # that this is irreversible.
        console_io.PromptContinue(
            'CMEK cannot be disabled on a bucket once enabled.',
            cancel_on_no=True)

      cmek_settings = util.GetMessages().CmekSettings(
          kmsKeyName=args.cmek_kms_key_name)
      bucket_data['cmekSettings'] = cmek_settings
      update_mask.append('cmek_settings')

    if not update_mask:
      raise calliope_exceptions.MinimumArgumentException(
          parameter_names, 'Please specify at least one property to update')

    if args.async_:
      result = util.GetClient().projects_locations_buckets.UpdateAsync(
          util.GetMessages().LoggingProjectsLocationsBucketsUpdateAsyncRequest(
              name=util.CreateResourceName(
                  util.CreateResourceName(
                      util.GetProjectResource(args.project).RelativeName(),
                      'locations',
                      args.location,
                  ),
                  'buckets',
                  args.BUCKET_ID,
              ),
              logBucket=util.GetMessages().LogBucket(**bucket_data),
              updateMask=','.join(update_mask),
          )
      )
      log.UpdatedResource(result.name, 'bucket', is_async=True)
      return result
    else:
      return util.GetClient().projects_locations_buckets.Patch(
          util.GetMessages().LoggingProjectsLocationsBucketsPatchRequest(
              name=util.CreateResourceName(
                  util.CreateResourceName(
                      util.GetProjectResource(args.project).RelativeName(),
                      'locations',
                      args.location,
                  ),
                  'buckets',
                  args.BUCKET_ID,
              ),
              logBucket=util.GetMessages().LogBucket(**bucket_data),
              updateMask=','.join(update_mask),
          )
      )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated bucket.
    """
    return self._Run(args)


Update.detailed_help = DETAILED_HELP
