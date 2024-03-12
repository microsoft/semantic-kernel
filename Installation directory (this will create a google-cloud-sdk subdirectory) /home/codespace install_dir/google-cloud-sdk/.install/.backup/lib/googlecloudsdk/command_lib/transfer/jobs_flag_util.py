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
"""Utils for managng the many transfer job flags.

Tested more through command surface tests.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from googlecloudsdk.calliope import arg_parsers

_POSIX_SOURCE_OR_DESTINATION_HELP_TEXT = (
    'POSIX filesystem - Specify the `posix://` scheme followed by the absolute'
    ' path to the desired directory, starting from the root of the host machine'
    ' (denoted by a leading slash). For example:\n'
    '* posix:///path/directory/\n\n'
    'A file transfer agent must be installed on the POSIX filesystem, and you'
    ' need an agent pool flag on this `jobs` command to activate the agent.')
_SOURCE_HELP_TEXT = (
    'The source of your data. Available sources and formatting information:\n\n'
    'Public clouds -\n'
    '* [Google Cloud Storage] gs://example-bucket/example-folder/\n'
    '* [Amazon S3] s3://examplebucket/example-folder\n'
    '* [Azure Blob Storage or Data Lake Storage] http://examplestorageaccount.'
    'blob.core.windows.net/examplecontainer/examplefolder\n\n'
    '{}\n\n'
    'Publicly-accessible objects - Specify the URL of a TSV file containing a'
    ' list of URLs of publicly-accessible objects. For example:\n'
    '* http://example.com/tsvfile'
).format(_POSIX_SOURCE_OR_DESTINATION_HELP_TEXT)
_DESTINATION_HELP_TEXT = (
    'The destination of your transferred data. Available destinations and '
    ' formatting information:\n\n'
    'Google Cloud Storage - Specify the `gs://` scheme; name of the bucket;'
    ' and, if transferring to a folder, the path to the folder. For example:\n'
    '* gs://example-bucket/example-folder/\n\n'
    '{}'
).format(_POSIX_SOURCE_OR_DESTINATION_HELP_TEXT)


class AuthMethod(enum.Enum):
  AWS_SIGNATURE_V2 = 'AWS_SIGNATURE_V2'
  AWS_SIGNATURE_V4 = 'AWS_SIGNATURE_V4'


class DeleteOption(enum.Enum):
  DESTINATION_IF_UNIQUE = 'destination-if-unique'
  SOURCE_AFTER_TRANSFER = 'source-after-transfer'


class JobStatus(enum.Enum):
  DELETED = 'deleted'
  DISABLED = 'disabled'
  ENABLED = 'enabled'


class LogAction(enum.Enum):
  COPY = 'copy'
  DELETE = 'delete'
  FIND = 'find'


class LogActionState(enum.Enum):
  FAILED = 'failed'
  SUCCEEDED = 'succeeded'


class PreserveMetadataField(enum.Enum):
  ACL = 'acl'
  GID = 'gid'
  KMS_KEY = 'kms-key'
  MODE = 'mode'
  STORAGE_CLASS = 'storage-class'
  SYMLINK = 'symlink'
  TEMPORARY_HOLD = 'temporary-hold'
  TIME_CREATED = 'time-created'
  UID = 'uid'


class ListApi(enum.Enum):
  LIST_OBJECTS = 'LIST_OBJECTS'
  LIST_OBJECTS_V2 = 'LIST_OBJECTS_V2'


class NetworkProtocol(enum.Enum):
  HTTP = 'HTTP'
  HTTPS = 'HTTPS'


class OverwriteOption(enum.Enum):
  ALWAYS = 'always'
  DIFFERENT = 'different'
  NEVER = 'never'


class RequestModel(enum.Enum):
  PATH_STYLE = 'PATH_STYLE'
  VIRTUAL_HOSTED_STYLE = 'VIRTUAL_HOSTED_STYLE'


def add_source_creds_flag(parser):
  parser.add_argument(
      '--source-creds-file',
      help='Path to a local file on your machine that includes credentials'
      ' for an Amazon S3 or Azure Blob Storage source (not required for'
      ' Google Cloud Storage sources). If not specified for an S3 source,'
      ' gcloud will check your system for an AWS config file. However, this'
      ' flag must be specified to use AWS\'s "role_arn" auth service. For'
      ' formatting, see:\n\n'
      'S3: https://cloud.google.com/storage-transfer/docs/reference/'
      'rest/v1/TransferSpec#AwsAccessKey\n'
      'Note: Be sure to put quotations around the JSON value strings.\n\n'
      'Azure: https://cloud.google.com/storage-transfer/docs/reference/rest/'
      'v1/TransferSpec#AzureCredentials\n\n')


def setup_parser(parser, is_update=False):
  """Adds flags to job create and job update commands."""
  # Flags and arg groups appear in help text in the order they are added here.
  # The order was designed by UX, so please do not modify.
  parser.SetSortArgs(False)
  if is_update:
    parser.add_argument(
        'name', help="Name of the transfer job you'd like to update.")
  else:
    parser.add_argument('source', help=_SOURCE_HELP_TEXT)
    parser.add_argument('destination', help=_DESTINATION_HELP_TEXT)

  job_information = parser.add_group(help='JOB INFORMATION', sort_args=False)
  if is_update:
    job_information.add_argument(
        '--status',
        choices=sorted(status.value for status in JobStatus),
        help='Specify this flag to change the status of the job. Options'
        " include 'enabled', 'disabled', 'deleted'.")
    job_information.add_argument('--source', help=_SOURCE_HELP_TEXT)
    job_information.add_argument('--destination', help=_DESTINATION_HELP_TEXT)
    job_information.add_argument(
        '--clear-description',
        action='store_true',
        help='Remove the description from the transfer job.')
    job_information.add_argument(
        '--clear-source-creds-file',
        action='store_true',
        help='Remove the source creds file from the transfer job.')
    job_information.add_argument(
        '--clear-source-agent-pool',
        action='store_true',
        help='Remove the source agent pool from the transfer job.')
    job_information.add_argument(
        '--clear-destination-agent-pool',
        action='store_true',
        help='Remove the destination agent pool from the transfer job.')
    job_information.add_argument(
        '--clear-intermediate-storage-path',
        action='store_true',
        help='Remove the intermediate storage path from the transfer job.')
    job_information.add_argument(
        '--clear-manifest-file',
        action='store_true',
        help='Remove the manifest file from the transfer job.')
  else:
    job_information.add_argument(
        '--name',
        help='A unique identifier for the job. Referring to your source and'
        ' destination is recommended. If left blank, the name is'
        ' auto-generated upon submission of the job.')
  job_information.add_argument(
      '--description',
      help='An optional description to help identify the job using details'
      " that don't fit in its name.")
  add_source_creds_flag(job_information)
  job_information.add_argument(
      '--source-agent-pool',
      help='If using a POSIX filesystem source, specify the ID of the agent'
      ' pool associated with source filesystem.')
  job_information.add_argument(
      '--destination-agent-pool',
      help='If using a POSIX filesystem destination, specify the ID of the'
      ' agent pool associated with destination filesystem.')
  job_information.add_argument(
      '--intermediate-storage-path',
      help='If transferring between filesystems, specify the path to a folder'
      ' in a Google Cloud Storage bucket (gs://example-bucket/example-folder)'
      ' to use as intermediary storage. Recommended: Use an empty folder'
      " reserved for this transfer job to ensure transferred data doesn't"
      ' interact with any of your existing Cloud Storage data.')
  job_information.add_argument(
      '--manifest-file',
      help='Path to a .csv file containing a list of files to transfer from'
      ' your source. For manifest files in Cloud Storage, specify the absolute'
      ' path (e.g., `gs://mybucket/manifest.csv`). For manifest files stored in'
      ' a source or destination POSIX file system, provide the relative path'
      ' (e.g., `source://path/to/manfest.csv` or'
      ' `destination://path/to/manifest.csv`). For manifest file formatting,'
      ' see https://cloud.google.com/storage-transfer/docs/manifest.')

  event_stream = parser.add_group(
      help=('EVENT STREAM\n\nConfigure an event stream to transfer data'
            ' whenever it is added or changed at your source, enabling you to'
            ' act on the data in near real time. This event-driven transfer'
            ' execution mode is available for transfers from Google Cloud'
            ' Storage and Amazon S3. For formatting information, see'
            ' https://cloud.google.com/sdk/gcloud/reference/topic/datetimes.'),
      sort_args=False)
  event_stream.add_argument(
      '--event-stream-name',
      help=('Specify an event stream that Storage Transfer Service can use to'
            ' listen for when objects are created or updated. For Google Cloud'
            ' Storage sources, specify a Cloud Pub/Sub subscription, using'
            ' format "projects/yourproject/subscriptions/yoursubscription". For'
            ' Amazon S3 sources, specify the Amazon Resource Name (ARN) of an'
            ' Amazon Simple Queue Service (SQS) queue using format'
            ' "arn:aws:sqs:region:account_id:queue_name".'))
  event_stream.add_argument(
      '--event-stream-starts',
      help=('Set when to start listening for events UTC using the'
            ' %Y-%m-%dT%H:%M:%S%z datetime format (e.g.,'
            ' 2020-04-12T06:42:12+04:00). If not set, the job will start'
            ' running and listening for events upon the successful submission'
            ' of the create job command.'))
  event_stream.add_argument(
      '--event-stream-expires',
      help=('Set when to stop listening for events UTC using the'
            ' %Y-%m-%dT%H:%M:%S%z datetime format (e.g.,'
            ' 2020-04-12T06:42:12+04:00). If not set, the job will continue'
            ' running and listening for events indefinitely.'))
  if is_update:
    event_stream.add_argument(
        '--clear-event-stream',
        action='store_true',
        help=(
            "Remove the job's entire event stream configuration by clearing all scheduling"
            ' all event stream flags. The job will no longer listen for'
            ' events unless a new configuratin is specified.'))

  schedule = parser.add_group(
      help=("SCHEDULE\n\nA job's schedule determines when and how often the job"
            ' will run. For formatting information, see'
            ' https://cloud.google.com/sdk/gcloud/reference/topic/datetimes.'),
      sort_args=False)
  if is_update:
    schedule.add_argument(
        '--clear-schedule',
        action='store_true',
        help=("Remove the job's entire schedule by clearing all scheduling"
              ' flags. The job will no longer run unless an operation is'
              ' manually started or a new schedule is specified.'))
  else:
    schedule.add_argument(
        '--do-not-run',
        action='store_true',
        help='Disable default Transfer Service behavior of running job upon'
        ' creation if no schedule is set. If this flag is specified, the job'
        " won't run until an operation is manually started or a schedule is"
        ' added.')
  schedule.add_argument(
      '--schedule-starts',
      type=arg_parsers.Datetime.Parse,
      help='Set when the job will start using the %Y-%m-%dT%H:%M:%S%z'
      ' datetime format (e.g., 2020-04-12T06:42:12+04:00). If not set,'
      ' the job will run upon the successful submission of the create'
      ' job command unless the --do-not-run flag is included.')
  schedule.add_argument(
      '--schedule-repeats-every',
      type=arg_parsers.Duration(),
      help='Set the frequency of the job using the absolute duration'
      ' format (e.g., 1 month is p1m; 1 hour 30 minutes is 1h30m). If'
      ' not set, the job will run once.')
  schedule.add_argument(
      '--schedule-repeats-until',
      type=arg_parsers.Datetime.Parse,
      help='Set when the job will stop recurring using the'
      ' %Y-%m-%dT%H:%M:%S%z datetime format (e.g.,'
      ' 2020-04-12T06:42:12+04:00). If specified, you must also include a'
      ' value for the --schedule-repeats-every flag. If not specified, the'
      ' job will continue to repeat as specified in its repeat-every field'
      ' unless the job is manually disabled or you add this field later.')

  object_conditions = parser.add_group(
      help=(
          'OBJECT CONDITIONS\n\nA set of conditions to determine which objects'
          ' are transferred. For time-based object condition formatting tips,'
          ' see https://cloud.google.com/sdk/gcloud/reference/topic/datetimes.'
          ' Note: If you specify multiple conditions, objects must have at'
          " least one of the specified 'include' prefixes and all of the"
          " specified time conditions. If an object has an 'exclude' prefix, it"
          ' will be excluded even if it matches other conditions.'),
      sort_args=False)
  if is_update:
    object_conditions.add_argument(
        '--clear-include-prefixes',
        action='store_true',
        help='Remove the list of object prefixes to include from the'
        ' object conditions.')
    object_conditions.add_argument(
        '--clear-exclude-prefixes',
        action='store_true',
        help='Remove the list of object prefixes to exclude from the'
        ' object conditions.')
    object_conditions.add_argument(
        '--clear-include-modified-before-absolute',
        action='store_true',
        help='Remove the maximum modification datetime from the'
        ' object conditions.')
    object_conditions.add_argument(
        '--clear-include-modified-after-absolute',
        action='store_true',
        help='Remove the minimum modification datetime from the'
        ' object conditions.')
    object_conditions.add_argument(
        '--clear-include-modified-before-relative',
        action='store_true',
        help='Remove the maximum duration since modification from the'
        ' object conditions.')
    object_conditions.add_argument(
        '--clear-include-modified-after-relative',
        action='store_true',
        help='Remove the minimum duration since modification from the'
        ' object conditions.')
  object_conditions.add_argument(
      '--include-prefixes',
      type=arg_parsers.ArgList(),
      metavar='INCLUDED_PREFIXES',
      help='Include only objects that start with the specified prefix(es).'
      ' Separate multiple prefixes with commas, omitting spaces after'
      ' the commas (e.g., --include-prefixes=foo,bar).')
  object_conditions.add_argument(
      '--exclude-prefixes',
      type=arg_parsers.ArgList(),
      metavar='EXCLUDED_PREFIXES',
      help='Exclude any objects that start with the prefix(es) entered.'
      ' Separate multiple prefixes with commas, omitting spaces after'
      ' the commas (e.g., --exclude-prefixes=foo,bar).')
  object_conditions.add_argument(
      '--include-modified-before-absolute',
      type=arg_parsers.Datetime.Parse,
      help='Include objects last modified before an absolute date/time. Ex.'
      " by specifying '2020-01-01', the transfer would include objects"
      ' last modified before January 1, 2020. Use the'
      ' %Y-%m-%dT%H:%M:%S%z datetime format.')
  object_conditions.add_argument(
      '--include-modified-after-absolute',
      type=arg_parsers.Datetime.Parse,
      help='Include objects last modified after an absolute date/time. Ex.'
      " by specifying '2020-01-01', the transfer would include objects"
      ' last modified after January 1, 2020. Use the'
      ' %Y-%m-%dT%H:%M:%S%z datetime format.')
  object_conditions.add_argument(
      '--include-modified-before-relative',
      type=arg_parsers.Duration(),
      help='Include objects that were modified before a relative date/time in'
      " the past. Ex. by specifying a duration of '10d', the transfer"
      ' would include objects last modified *more than* 10 days before'
      ' its start time. Use the absolute duration format (ex. 1m for 1'
      ' month; 1h30m for 1 hour 30 minutes).')
  object_conditions.add_argument(
      '--include-modified-after-relative',
      type=arg_parsers.Duration(),
      help='Include objects that were modified after a relative date/time in'
      " the past. Ex. by specifying a duration of '10d', the transfer"
      ' would include objects last modified *less than* 10 days before'
      ' its start time. Use the absolute duration format (ex. 1m for 1'
      ' month; 1h30m for 1 hour 30 minutes).')

  transfer_options = parser.add_group(help='TRANSFER OPTIONS', sort_args=False)
  if is_update:
    transfer_options.add_argument(
        '--clear-delete-from',
        action='store_true',
        help='Remove a specified deletion option from the transfer job. If '
        " this flag is specified, the transfer job won't delete any data from"
        ' your source or destination.')
    transfer_options.add_argument(
        '--clear-preserve-metadata',
        action='store_true',
        help='Skips preserving optional metadata fields of objects being'
        ' transferred.')
    transfer_options.add_argument(
        '--clear-custom-storage-class',
        action='store_true',
        help='Reverts to using destination default storage class.')
  transfer_options.add_argument(
      '--overwrite-when',
      choices=sorted(option.value for option in OverwriteOption),
      help='Determine when destination objects are overwritten by source'
      ' objects. Options include:\n'
      " - 'different' - Overwrites files with the same name if the contents"
      " are different (e.g., if etags or checksums don't match)\n"
      " - 'always' - Overwrite destination file whenever source file has the"
      " same name -- even if they're identical\n"
      " - 'never' - Never overwrite destination file when source file has the"
      ' same name')
  transfer_options.add_argument(
      '--delete-from',
      choices=sorted(option.value for option in DeleteOption),
      help="By default, transfer jobs won't delete any data from your source"
      ' or destination. These options enable you to delete data if'
      ' needed for your use case. Options include:\n'
      " - 'destination-if-unique' - Delete files from destination if they're"
      ' not also at source. Use to sync destination to source (i.e., make'
      ' destination match source exactly)\n'
      " - 'source-after-transfer' - Delete files from source after they're"
      ' transferred')
  transfer_options.add_argument(
      '--preserve-metadata',
      type=arg_parsers.ArgList(
          choices=sorted(field.value for field in PreserveMetadataField)),
      metavar='METADATA_FIELDS',
      help='Specify object metadata values that can optionally be preserved.'
      ' Example: --preserve-metadata=storage-class,uid\n\n'
      'For more info, see: https://cloud.google.com/storage-transfer/docs/'
      'metadata-preservation\n\n')
  transfer_options.add_argument(
      '--custom-storage-class',
      help='Specifies the storage class to set on objects being transferred to'
      " Cloud Storage buckets. If unspecified, the objects' storage class is"
      ' set to the destination bucket default.'
      ' Valid values are:\n\n'
      ' - Any of the values listed in the Cloud Storage documentation:'
      '   [Available storage classes](https://cloud.google.com/storage/docs/storage-classes#classes).\n'
      " - `preserve` - Preserves each object's original storage class. Only"
      '   supported for transfers between Cloud Storage buckets.\n'
      ' \nCustom storage class settings are ignored if the destination bucket'
      ' is'
      ' [Autoclass-enabled](https://cloud.google.com/storage/docs/autoclass).'
      ' Objects transferred into Autoclass-enabled buckets are initially'
      ' set to the `STANDARD` storage class.')

  notification_config = parser.add_group(
      help=(
          'NOTIFICATION CONFIG\n\nA configuration for receiving notifications of'
          'transfer operation status changes via Cloud Pub/Sub.'),
      sort_args=False)
  if is_update:
    notification_config.add_argument(
        '--clear-notification-config',
        action='store_true',
        help="Remove the job's full notification configuration to no"
        ' longer receive notifications via Cloud Pub/Sub.')
    notification_config.add_argument(
        '--clear-notification-event-types',
        action='store_true',
        help='Remove the event types from the notification config.')
  notification_config.add_argument(
      '--notification-pubsub-topic',
      help='Pub/Sub topic used for notifications.')
  notification_config.add_argument(
      '--notification-event-types',
      type=arg_parsers.ArgList(choices=['success', 'failed', 'aborted']),
      metavar='EVENT_TYPES',
      help='Define which change of transfer operation status will trigger'
      " Pub/Sub notifications. Choices include 'success', 'failed',"
      " 'aborted'. To trigger notifications for all three status changes,"
      " you can leave this flag unspecified as long as you've specified"
      ' a topic for the --notification-pubsub-topic flag.')
  notification_config.add_argument(
      '--notification-payload-format',
      choices=['json', 'none'],
      help="If 'none', no transfer operation details are included with"
      " notifications. If 'json', a json representation of the relevant"
      ' transfer operation is included in notification messages (e.g., to'
      ' see errors after an operation fails).')

  logging_config = parser.add_group(
      help=('LOGGING CONFIG\n\nConfigure which transfer actions and action'
            ' states are reported when logs are generated for this job. Logs'
            ' can be viewed by running the following command:\n'
            'gcloud logging read "resource.type=storage_transfer_job"'),
      sort_args=False)
  if is_update:
    logging_config.add_argument(
        '--clear-log-config',
        action='store_true',
        help="Remove the job's full logging config.")
  logging_config.add_argument(
      '--enable-posix-transfer-logs',
      action=arg_parsers.StoreTrueFalseAction,
      help='Sets whether to generate logs for transfers with a POSIX'
      ' filesystem source. This setting will later be merged with other log'
      ' configurations.')
  logging_config.add_argument(
      '--log-actions',
      type=arg_parsers.ArgList(
          choices=sorted(option.value for option in LogAction)),
      metavar='LOG_ACTIONS',
      help='Define the transfer operation actions to report in logs. Separate'
      ' multiple actions with commas, omitting spaces after the commas'
      ' (e.g., --log-actions=find,copy).')
  logging_config.add_argument(
      '--log-action-states',
      type=arg_parsers.ArgList(
          choices=sorted(option.value for option in LogActionState)),
      metavar='LOG_ACTION_STATES',
      help='The states in which the actions specified in --log-actions are'
      ' logged. Separate multiple states with a comma, omitting the space after'
      ' the comma (e.g., --log-action-states=succeeded,failed).')

  additional_options = parser.add_group(
      help='ADDITIONAL OPTIONS', sort_args=False)
  additional_options.add_argument(
      '--source-endpoint',
      help='For transfers from S3-compatible sources, specify your storage'
      " system's endpoint. Check with your provider for formatting (ex."
      ' s3.us-east-1.amazonaws.com for Amazon S3).')
  additional_options.add_argument(
      '--source-signing-region',
      help='For transfers from S3-compatible sources, specify a region for'
      ' signing requests. You can leave this unspecified if your storage'
      " provider doesn't require a signing region.")
  additional_options.add_argument(
      '--source-auth-method',
      choices=sorted(option.value for option in AuthMethod),
      help='For transfers from S3-compatible sources, choose a process for'
      " adding authentication information to S3 API requests. Refer to AWS's"
      ' SigV4 (https://docs.aws.amazon.com/general/latest/gr/signature-version'
      '-4.html) and SigV2 (https://docs.aws.amazon.com/general/latest/gr/'
      'signature-version-2.html) documentation for more information.')
  additional_options.add_argument(
      '--source-list-api',
      choices=sorted(option.value for option in ListApi),
      help='For transfers from S3-compatible sources, choose the version of the'
      " S3 listing API for returning objects from the bucket. Refer to AWS's"
      ' ListObjectsV2 (https://docs.aws.amazon.com/AmazonS3/latest/API/'
      'API_ListObjectsV2.html) and ListObjects (https://docs.aws.amazon.com/'
      'AmazonS3/latest/API/API_ListObjects.html) documentation for more'
      ' information.')
  additional_options.add_argument(
      '--source-network-protocol',
      choices=sorted(option.value for option in NetworkProtocol),
      help='For transfers from S3-compatible sources, choose the network'
      ' protocol agents should use for this job.')
  additional_options.add_argument(
      '--source-request-model',
      choices=sorted(option.value for option in RequestModel),
      help='For transfers from S3-compatible sources, choose which addressing'
      ' style to use. Determines if the bucket name is in the hostname or part'
      ' of the URL. For example, https://s3.region.amazonaws.com/bucket-name'
      '/key-name for path style and Ex. https://bucket-name.s3.region.'
      'amazonaws.com/key-name for virtual-hosted style.')
  if is_update:
    additional_options.add_argument(
        '--clear-source-endpoint',
        action='store_true',
        help='Removes source endpoint.')
    additional_options.add_argument(
        '--clear-source-signing-region',
        action='store_true',
        help='Removes source signing region.')
    additional_options.add_argument(
        '--clear-source-auth-method',
        action='store_true',
        help='Removes source auth method.')
    additional_options.add_argument(
        '--clear-source-list-api',
        action='store_true',
        help='Removes source list API.')
    additional_options.add_argument(
        '--clear-source-network-protocol',
        action='store_true',
        help='Removes source network protocol.')
    additional_options.add_argument(
        '--clear-source-request-model',
        action='store_true',
        help='Removes source request model.')

  if not is_update:
    execution_options = parser.add_group(
        help='EXECUTION OPTIONS', sort_args=False)
    execution_options.add_argument(
        '--no-async',
        action='store_true',
        help='For jobs set to run upon creation, this flag blocks other tasks'
        " in your terminal until the job's initial, immediate transfer"
        ' operation has completed. If not included, tasks will run'
        ' asynchronously.')
