# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""A library containing flags used by Cloud Pub/Sub commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import log

# Maximum number of attributes you can specify for a message.
MAX_ATTRIBUTES = 100

# Format string for deprecation message for renaming positional to flag.
DEPRECATION_FORMAT_STR = (
    'Positional argument `{0}` is deprecated. Please use `{1}` instead.'
)

# Help string for duration format flags.
DURATION_HELP_STR = (
    'Valid values are strings of the form INTEGER[UNIT], where UNIT is one of '
    '"s", "m", "h", and "d" for seconds, minutes, hours, and days, '
    'respectively. If the unit is omitted, seconds is assumed.'
)


def NegativeBooleanFlagHelpText(flag_name):
  return f'Use --no-{flag_name} to disable this flag.'


def AddBooleanFlag(parser, flag_name, help_text, **kwargs):
  parser.add_argument(
      '--' + flag_name,
      help=help_text + ' ' + NegativeBooleanFlagHelpText(flag_name),
      **kwargs,
  )


def AddAckIdFlag(parser, action, add_deprecated=False):
  """Adds parsing and help text for ack_id flag."""

  help_text = (
      'One or more ACK_IDs to {} An ACK_ID is a [string that is returned to '
      'subscribers](https://cloud.google.com/pubsub/docs/reference/rpc/google.pubsub.v1#google.pubsub.v1.ReceivedMessage).'
      ' along with the message. The ACK_ID is different from the [message '
      'ID](https://cloud.google.com/pubsub/docs/reference/rpc/google.pubsub.v1#google.pubsub.v1.PubsubMessage).'
  ).format(action)
  group = parser
  if add_deprecated:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        'ack_id',
        nargs='*',
        help=help_text,
        action=actions.DeprecationAction(
            'ACK_ID',
            show_message=lambda _: False,  # See ParseAckIdsArgs for reason.
            warn=DEPRECATION_FORMAT_STR.format('ACK_ID', '--ack-ids'),
        ),
    )
  group.add_argument(
      '--ack-ids',
      metavar='ACK_ID',
      required=not add_deprecated,
      type=arg_parsers.ArgList(),
      help=help_text,
  )


def ParseAckIdsArgs(args):
  """Gets the list of ack_ids from args.

  This is only necessary because we are deprecating the positional `ack_id`.
  Putting the positional and a flag in an argument group, will group flag
  under positional args. This would be confusing.

  DeprecationAction can't be used here because in order to make the positional
  argument optional, we have to use `nargs='*'`. Since this means zero or more,
  the DeprecationAction warn message is always triggered.

  This function does not exist in util.py in order to group the explanation for
  why this exists with the deprecated flags.

  Once the positional is removed, this function can be removed.

  Args:
    args (argparse.Namespace): Parsed arguments

  Returns:
    list[str]: List of ack ids.
  """
  if args.ack_id:
    log.warning(DEPRECATION_FORMAT_STR.format('ACK_ID', '--ack-ids'))
  ack_ids = args.ack_id or args.ack_ids
  if not isinstance(ack_ids, list):
    ack_ids = [ack_ids]
  return ack_ids


def AddIamPolicyFileFlag(parser):
  parser.add_argument(
      'policy_file', help='JSON or YAML file with the IAM policy'
  )


def AddSeekFlags(parser):
  """Adds flags for the seek command to the parser."""
  seek_to_group = parser.add_mutually_exclusive_group(required=True)
  seek_to_group.add_argument(
      '--time',
      type=arg_parsers.Datetime.Parse,
      help="""\
          The time to seek to. Messages in the subscription that
          were published before this time are marked as acknowledged, and
          messages retained in the subscription that were published after
          this time are marked as unacknowledged.
          See $ gcloud topic datetimes for information on time formats.""",
  )
  seek_to_group.add_argument(
      '--snapshot',
      help=(
          "The name of the snapshot. The snapshot's topic must be the same "
          'as that of the subscription.'
      ),
  )
  parser.add_argument(
      '--snapshot-project',
      help="""\
          The name of the project the snapshot belongs to (if seeking to
          a snapshot). If not set, it defaults to the currently selected
          cloud project.""",
  )


def AddPullFlags(
    parser, add_deprecated=False, add_wait=False, add_return_immediately=False
):
  """Adds the main set of message pulling flags to a parser."""
  if add_deprecated:
    parser.add_argument(
        '--max-messages',
        type=int,
        default=1,
        help=(
            'The maximum number of messages that Cloud Pub/Sub can return '
            'in this response.'
        ),
        action=actions.DeprecationAction(
            '--max-messages',
            warn='`{flag_name}` is deprecated. Please use --limit instead.',
        ),
    )
  AddBooleanFlag(
      parser=parser,
      flag_name='auto-ack',
      action='store_true',
      default=False,
      help_text=(
          'Automatically ACK every message pulled from this subscription.'
      ),
  )
  if add_wait and add_return_immediately:
    parser = parser.add_group(mutex=True, help='Pull timeout behavior.')
  if add_wait:
    parser.add_argument(
        '--wait',
        default=True,
        help=(
            'Wait (for a bounded amount of time) for new messages from the '
            'subscription, if there are none.'
        ),
        action=actions.DeprecationAction(
            '--wait',
            warn=(
                '`{flag_name}` is deprecated. This flag is non-operational, as'
                ' the wait behavior is now the default.'
            ),
            action='store_true',
        ),
    )
  if add_return_immediately:
    AddBooleanFlag(
        parser=parser,
        flag_name='return-immediately',
        action='store_true',
        default=False,
        help_text=(
            'If this flag is set, the system responds immediately with any'
            ' messages readily available in memory buffers. If no messages are'
            ' available in the buffers, returns an empty list of messages as'
            ' response, even if having messages in the backlog. Do not set this'
            ' flag as it adversely impacts the performance of pull.'
        ),
    )


def AddPushConfigFlags(parser, required=False, is_update=False):
  """Adds flags for push subscriptions to the parser."""
  parser.add_argument(
      '--push-endpoint',
      required=required,
      help=(
          'A URL to use as the endpoint for this subscription. This will '
          'also automatically set the subscription type to PUSH.'
      ),
  )
  parser.add_argument(
      '--push-auth-service-account',
      required=False,
      dest='SERVICE_ACCOUNT_EMAIL',
      help=(
          'Service account email used as the identity for the generated '
          'Open ID Connect token for authenticated push.'
      ),
  )
  parser.add_argument(
      '--push-auth-token-audience',
      required=False,
      dest='OPTIONAL_AUDIENCE_OVERRIDE',
      help=(
          'Audience used in the generated Open ID Connect token for '
          'authenticated push. If not specified, it will be set to the '
          'push-endpoint.'
      ),
  )
  current_group = parser
  if is_update:
    mutual_exclusive_group = current_group.add_mutually_exclusive_group()
    AddBooleanFlag(
        parser=mutual_exclusive_group,
        flag_name='clear-push-no-wrapper-config',
        action='store_true',
        help_text="""If set, clear the NoWrapper config from the subscription.""",
    )
    current_group = mutual_exclusive_group
  definition_group = current_group.add_group(
      mutex=False,
      help='NoWrapper Config Options.',
      required=False,
  )
  AddBooleanFlag(
      parser=definition_group,
      flag_name='push-no-wrapper',
      help_text=(
          'When set, the message data is delivered directly as the HTTP body.'
      ),
      action='store_true',
      required=True,
  )
  AddBooleanFlag(
      parser=definition_group,
      flag_name='push-no-wrapper-write-metadata',
      help_text=(
          'When true, writes the Pub/Sub message metadata to'
          ' `x-goog-pubsub-<KEY>:<VAL>` headers of the HTTP request. Writes'
          ' the Pub/Sub message attributes to `<KEY>:<VAL>` headers of the'
          ' HTTP request.'
      ),
      action='store_true',
      required=False,
  )


def AddAckDeadlineFlag(parser, required=False):
  parser.add_argument(
      '--ack-deadline',
      type=int,
      required=required,
      help=(
          'The number of seconds the system will wait for a subscriber to '
          'acknowledge receiving a message before re-attempting delivery.'
      ),
  )


def AddSubscriptionMessageRetentionFlags(parser, is_update):
  """Adds flags subscription's messsage retention properties to the parser."""
  if is_update:
    retention_parser = ParseSubscriptionRetentionDurationWithDefault
    retention_default_help = 'Specify "default" to use the default value.'
  else:
    retention_parser = arg_parsers.Duration()
    retention_default_help = (
        'The default value is 7 days, the minimum is '
        '10 minutes, and the maximum is 7 days.'
    )

  retention_parser = retention_parser or arg_parsers.Duration()
  AddBooleanFlag(
      parser=parser,
      flag_name='retain-acked-messages',
      action='store_true',
      default=None,
      help_text="""\
          Whether or not to retain acknowledged messages. If true,
          messages are not expunged from the subscription's backlog
          until they fall out of the --message-retention-duration
          window. Acknowledged messages are not retained by default. """,
  )
  parser.add_argument(
      '--message-retention-duration',
      type=retention_parser,
      help="""\
          How long to retain unacknowledged messages in the
          subscription's backlog, from the moment a message is
          published. If --retain-acked-messages is true, this also
          configures the retention of acknowledged messages. {} {}""".format(
          retention_default_help, DURATION_HELP_STR
      ),
  )


def AddSubscriptionTopicResourceFlags(parser):
  """Adds --topic and --topic-project flags to a parser."""
  parser.add_argument(
      '--topic',
      required=True,
      help=(
          'The name of the topic from which this subscription is receiving '
          'messages. Each subscription is attached to a single topic.'
      ),
  )
  parser.add_argument(
      '--topic-project',
      help=(
          'The name of the project the provided topic belongs to. '
          'If not set, it defaults to the currently selected cloud project.'
      ),
  )


def AddBigQueryConfigFlags(
    parser,
    is_update,
):
  """Adds BigQuery config flags to parser."""
  current_group = parser
  if is_update:
    mutual_exclusive_group = current_group.add_mutually_exclusive_group()
    AddBooleanFlag(
        parser=mutual_exclusive_group,
        flag_name='clear-bigquery-config',
        action='store_true',
        default=None,
        help_text="""If set, clear the BigQuery config from the subscription.""",
    )
    current_group = mutual_exclusive_group
  bigquery_config_group = current_group.add_argument_group(
      help="""BigQuery Config Options. The Cloud Pub/Sub service account
         associated with the enclosing subscription's parent project (i.e.,
         service-{project_number}@gcp-sa-pubsub.iam.gserviceaccount.com)
         must have permission to write to this BigQuery table."""
  )
  bigquery_config_group.add_argument(
      '--bigquery-table',
      required=True,
      help=(
          'A BigQuery table  of the form {project}:{dataset_name}.{table_name}'
          ' to which to write messages for this subscription.'
      ),
  )

  bigquery_schema_config_mutually_exclusive_group = (
      bigquery_config_group.add_mutually_exclusive_group()
  )

  AddBooleanFlag(
      parser=bigquery_schema_config_mutually_exclusive_group,
      flag_name='use-topic-schema',
      action='store_true',
      default=None,
      help_text=(
          "Whether or not to use the schema for the subscription's topic (if it"
          ' exists) when writing messages to BigQuery. If --drop-unknown-fields'
          ' is not set, then the BigQuery schema must contain all fields that'
          ' are present in the topic schema.'
      ),
  )
  AddBooleanFlag(
      parser=bigquery_schema_config_mutually_exclusive_group,
      flag_name='use-table-schema',
      action='store_true',
      default=None,
      help_text=(
          'Whether or not to use the BigQuery table schema when writing'
          ' messages to BigQuery.'
      ),
  )
  AddBooleanFlag(
      parser=bigquery_config_group,
      flag_name='write-metadata',
      action='store_true',
      default=None,
      help_text=(
          'Whether or not to write message metadata including message ID,'
          ' publish timestamp, ordering key, and attributes to BigQuery. The'
          ' subscription name, message_id, and publish_time fields are put in'
          ' their own columns while all other message properties other than'
          ' data (for example, an ordering_key, if present) are written to a'
          ' JSON object in the attributes column.'
      ),
  )
  AddBooleanFlag(
      parser=bigquery_config_group,
      flag_name='drop-unknown-fields',
      action='store_true',
      default=None,
      help_text=(
          'If either --use-topic-schema or --use-table-schema is set, whether'
          ' or not to ignore fields in the message that do not appear in the'
          ' BigQuery table schema.'
      ),
  )


def AddCloudStorageConfigFlags(
    parser, is_update, enable_cps_gcs_file_datetime_format
):
  """Adds Cloud Storage config flags to parser."""
  current_group = parser
  cloud_storage_config_group_help = """Cloud Storage Config Options. The Cloud
        Pub/Sub service account associated with the enclosing subscription's
        parent project (i.e.,
        service-{project_number}@gcp-sa-pubsub.iam.gserviceaccount.com)
        must have permission to write to this Cloud Storage bucket and to read
        this bucket's metadata."""
  if is_update:
    mutual_exclusive_group = current_group.add_mutually_exclusive_group()
    AddBooleanFlag(
        parser=mutual_exclusive_group,
        flag_name='clear-cloud-storage-config',
        action='store_true',
        default=None,
        help_text="""If set, clear the Cloud Storage config from the subscription.""",
    )
    current_group = mutual_exclusive_group
    cloud_storage_config_group_help += """\n\nNote that an update to the Cloud
          Storage config will replace it with a new config containing only the
          flags that are passed in the `update` CLI."""
  cloud_storage_config_group = current_group.add_argument_group(
      help=cloud_storage_config_group_help
  )
  cloud_storage_config_group.add_argument(
      '--cloud-storage-bucket',
      required=True,
      help=(
          'A Cloud Storage bucket to which to write messages for this'
          ' subscription.'
      ),
  )
  cloud_storage_config_group.add_argument(
      '--cloud-storage-file-prefix',
      default=None,
      help='The prefix for Cloud Storage filename.',
  )
  cloud_storage_config_group.add_argument(
      '--cloud-storage-file-suffix',
      default=None,
      help='The suffix for Cloud Storage filename.',
  )
  if enable_cps_gcs_file_datetime_format:
    # TODO(b/317043091): Link flag help text to docs describing allowed datetime
    # formats once they are available.
    cloud_storage_config_group.add_argument(
        '--cloud-storage-file-datetime-format',
        default=None,
        hidden=True,
        help='The custom datetime format string for Cloud Storage filename.',
    )
  cloud_storage_config_group.add_argument(
      '--cloud-storage-max-bytes',
      type=arg_parsers.BinarySize(
          lower_bound='1KB',
          upper_bound='10GB',
          default_unit='KB',
          suggested_binary_size_scales=['KB', 'KiB', 'MB', 'MiB', 'GB', 'GiB'],
      ),
      default=None,
      help=(
          ' The maximum bytes that can be written to a Cloud Storage file'
          ' before a new file is created. The value must be between 1KB to'
          ' 10GB. If the unit is omitted, KB is assumed.'
      ),
  )
  cloud_storage_config_group.add_argument(
      '--cloud-storage-max-duration',
      type=arg_parsers.Duration(
          lower_bound='1m', upper_bound='10m', default_unit='s'
      ),
      help="""The maximum duration that can elapse before a new Cloud Storage
          file is created. The value must be between 1m and 10m.
          {}""".format(DURATION_HELP_STR),
  )
  cloud_storage_config_group.add_argument(
      '--cloud-storage-output-format',
      type=arg_parsers.ArgList(
          element_type=lambda x: str(x).lower(),
          min_length=1,
          max_length=1,
          choices=['text', 'avro'],
      ),
      default='text',
      metavar='OUTPUT_FORMAT',
      help=(
          'The output format for data written to Cloud Storage. Values: text'
          ' (messages will be written as raw text, separated by a newline) or'
          ' avro (messages will be written as an Avro binary).'
      ),
  )
  AddBooleanFlag(
      parser=cloud_storage_config_group,
      flag_name='cloud-storage-write-metadata',
      action='store_true',
      default=None,
      help_text=(
          'Whether or not to write the subscription name, message_id,'
          ' publish_time, attributes, and ordering_key as additional fields in'
          ' the output. The subscription name, message_id, and publish_time'
          ' fields are put in their own fields while all other message'
          ' properties other than data (for example, an ordering_key, if'
          ' present) are added as entries in the attributes map. This has an'
          ' effect only for subscriptions with'
          ' --cloud-storage-output-format=avro.'
      ),
  )


def AddPubsubExportConfigFlags(parser, is_update):
  """Adds Pubsub export config flags to parser."""
  current_group = parser
  if is_update:
    mutual_exclusive_group = current_group.add_mutually_exclusive_group(
        hidden=True
    )
    AddBooleanFlag(
        parser=mutual_exclusive_group,
        flag_name='clear-pubsub-export-config',
        action='store_true',
        default=None,
        hidden=True,
        help_text=(
            'If set, clear the Pubsub Export config from the subscription.'
        ),
    )
    current_group = mutual_exclusive_group
  pubsub_export_config_group = current_group.add_argument_group(
      hidden=True,
      help="""Cloud Pub/Sub Export Config Options. The Cloud Pub/Sub service
      account associated with the enclosing subscription's parent project
      (i.e., service-{project_number}@gcp-sa-pubsub.iam.gserviceaccount.com)
      must have permission to publish to the destination Cloud Pub/Sub topic.""",
  )
  pubsub_export_topic = resource_args.CreateTopicResourceArg(
      'to publish messages to.',
      flag_name='pubsub-export-topic',
      positional=False,
      required=True,
  )
  resource_args.AddResourceArgs(
      pubsub_export_config_group, [pubsub_export_topic]
  )
  pubsub_export_config_group.add_argument(
      '--pubsub-export-topic-region',
      required=False,
      help=(
          'The Google Cloud region to which messages are published. For'
          ' example, us-east1. Do not specify more than one region. If the'
          ' region you specified is different from the region to which messages'
          ' were published, egress fees are incurred. If the region is not'
          ' specified, Pub/Sub uses the same region to which the messages were'
          ' originally published on a best-effort basis.'
      ),
  )


def ParseSubscriptionRetentionDurationWithDefault(value):
  if value == subscriptions.DEFAULT_MESSAGE_RETENTION_VALUE:
    return value
  return util.FormatDuration(arg_parsers.Duration()(value))


def ParseExpirationPeriodWithNeverSentinel(value):
  if value == subscriptions.NEVER_EXPIRATION_PERIOD_VALUE:
    return value
  return util.FormatDuration(arg_parsers.Duration()(value))


def AddSubscriptionSettingsFlags(
    parser,
    is_update=False,
    enable_push_to_cps=False,
    enable_cps_gcs_file_datetime_format=False,
):
  """Adds the flags for creating or updating a subscription.

  Args:
    parser: The argparse parser.
    is_update: Whether or not this is for the update operation (vs. create).
    enable_push_to_cps: whether or not to enable Pubsub Export config flags
      support.
    enable_cps_gcs_file_datetime_format: whether or not to enable GCS file
      datetime format flags support.
  """
  AddAckDeadlineFlag(parser)
  AddPushConfigFlags(
      parser,
      is_update=is_update,
  )

  mutex_group = parser.add_mutually_exclusive_group()
  AddBigQueryConfigFlags(mutex_group, is_update)
  AddCloudStorageConfigFlags(
      mutex_group, is_update, enable_cps_gcs_file_datetime_format
  )
  if enable_push_to_cps:
    AddPubsubExportConfigFlags(mutex_group, is_update)
  AddSubscriptionMessageRetentionFlags(parser, is_update)
  if not is_update:
    AddBooleanFlag(
        parser=parser,
        flag_name='enable-message-ordering',
        action='store_true',
        default=None,
        help_text="""Whether to receive messages with the same ordering key in order.
            If set, messages with the same ordering key are sent to subscribers
            in the order that Pub/Sub receives them.""",
    )
  if not is_update:
    parser.add_argument(
        '--message-filter',
        type=str,
        help="""Expression to filter messages. If set, Pub/Sub only delivers the
        messages that match the filter. The expression must be a non-empty
        string in the [Pub/Sub filtering
        language](https://cloud.google.com/pubsub/docs/filtering).""",
    )
  current_group = parser
  if is_update:
    mutual_exclusive_group = current_group.add_mutually_exclusive_group()
    AddBooleanFlag(
        parser=mutual_exclusive_group,
        flag_name='clear-dead-letter-policy',
        action='store_true',
        default=None,
        help_text="""If set, clear the dead letter policy from the subscription.""",
    )
    current_group = mutual_exclusive_group

  set_dead_letter_policy_group = current_group.add_argument_group(
      help="""Dead Letter Queue Options. The Cloud Pub/Sub service account
           associated with the enclosing subscription's parent project (i.e.,
           service-{project_number}@gcp-sa-pubsub.iam.gserviceaccount.com)
           must have permission to Publish() to this topic and Acknowledge()
           messages on this subscription."""
  )
  dead_letter_topic = resource_args.CreateTopicResourceArg(
      'to publish dead letter messages to.',
      flag_name='dead-letter-topic',
      positional=False,
      required=False,
  )
  resource_args.AddResourceArgs(
      set_dead_letter_policy_group, [dead_letter_topic]
  )
  set_dead_letter_policy_group.add_argument(
      '--max-delivery-attempts',
      type=arg_parsers.BoundedInt(5, 100),
      default=None,
      help="""Maximum number of delivery attempts for any message. The value
          must be between 5 and 100. Defaults to 5. `--dead-letter-topic`
          must also be specified.""",
  )
  parser.add_argument(
      '--expiration-period',
      type=ParseExpirationPeriodWithNeverSentinel,
      help="""The subscription will expire if it is inactive for the given
          period. {} This flag additionally accepts the special value "never" to
          indicate that the subscription will never expire.""".format(
          DURATION_HELP_STR
      ),
  )

  current_group = parser
  if is_update:
    mutual_exclusive_group = current_group.add_mutually_exclusive_group()
    AddBooleanFlag(
        parser=mutual_exclusive_group,
        flag_name='clear-retry-policy',
        action='store_true',
        default=None,
        help_text="""If set, clear the retry policy from the subscription.""",
    )
    current_group = mutual_exclusive_group

  set_retry_policy_group = current_group.add_argument_group(
      help="""Retry Policy Options. Retry policy specifies how Cloud Pub/Sub
              retries message delivery for this subscription."""
  )

  set_retry_policy_group.add_argument(
      '--min-retry-delay',
      type=arg_parsers.Duration(lower_bound='0s', upper_bound='600s'),
      help="""The minimum delay between consecutive deliveries of a given
          message. Value should be between 0 and 600 seconds. Defaults to 10
          seconds. {}""".format(DURATION_HELP_STR),
  )
  set_retry_policy_group.add_argument(
      '--max-retry-delay',
      type=arg_parsers.Duration(lower_bound='0s', upper_bound='600s'),
      help="""The maximum delay between consecutive deliveries of a given
          message. Value should be between 0 and 600 seconds. Defaults to 10
          seconds. {}""".format(DURATION_HELP_STR),
  )
  help_text_suffix = ''
  if is_update:
    help_text_suffix = (
        ' To disable exactly-once delivery use '
        '`--no-enable-exactly-once-delivery`.'
    )
  AddBooleanFlag(
      parser=parser,
      flag_name='enable-exactly-once-delivery',
      action='store_true',
      default=None,
      help_text="""\
          Whether or not to enable exactly-once delivery on the subscription.
          If true, Pub/Sub provides the following guarantees for the delivery
          of a message with a given value of `message_id` on this
          subscription: The message sent to a subscriber is guaranteed not to
          be resent before the message's acknowledgment deadline expires. An
          acknowledged message will not be resent to a subscriber."""
      + help_text_suffix,
  )


def AddPublishMessageFlags(parser, add_deprecated=False):
  """Adds the flags for building a PubSub message to the parser.

  Args:
    parser: The argparse parser.
    add_deprecated: Whether or not to add the deprecated flags.
  """
  message_help_text = """\
      The body of the message to publish to the given topic name.
      Information on message formatting and size limits can be found at:
      https://cloud.google.com/pubsub/docs/publisher#publish"""
  if add_deprecated:
    parser.add_argument(
        'message_body',
        nargs='?',
        default=None,
        help=message_help_text,
        action=actions.DeprecationAction(
            'MESSAGE_BODY',
            show_message=lambda _: False,
            warn=DEPRECATION_FORMAT_STR.format('MESSAGE_BODY', '--message'),
        ),
    )
  parser.add_argument('--message', help=message_help_text)

  parser.add_argument(
      '--attribute',
      type=arg_parsers.ArgDict(max_length=MAX_ATTRIBUTES),
      help=(
          'Comma-separated list of attributes. Each ATTRIBUTE has the form '
          'name="value". You can specify up to {0} attributes.'.format(
              MAX_ATTRIBUTES
          )
      ),
  )

  parser.add_argument(
      '--ordering-key',
      help="""The key for ordering delivery to subscribers. All messages with
          the same ordering key are sent to subscribers in the order that
          Pub/Sub receives them.""",
  )


def AddSchemaSettingsFlags(parser, is_update=False):
  """Adds the flags for filling the SchemaSettings message.

  Args:
    parser: The argparse parser.
    is_update: (bool) If true, add another group with clear-schema-settings as a
      mutually exclusive argument.
  """
  current_group = parser
  if is_update:
    mutual_exclusive_group = current_group.add_mutually_exclusive_group()
    AddBooleanFlag(
        parser=mutual_exclusive_group,
        flag_name='clear-schema-settings',
        action='store_true',
        default=None,
        help_text="""If set, clear the Schema Settings from the topic.""",
    )
    current_group = mutual_exclusive_group
  set_schema_settings_group = current_group.add_argument_group(
      # pylint: disable=line-too-long
      help="""Schema settings. The schema that messages published to this topic must conform to and the expected message encoding."""
  )

  schema_help_text = 'that messages published to this topic must conform to.'
  schema = resource_args.CreateSchemaResourceArg(
      schema_help_text, positional=False, plural=False, required=True
  )
  resource_args.AddResourceArgs(set_schema_settings_group, [schema])
  set_schema_settings_group.add_argument(
      '--message-encoding',
      type=arg_parsers.ArgList(
          element_type=lambda x: str(x).lower(),
          min_length=1,
          max_length=1,
          choices=['json', 'binary'],
      ),
      metavar='ENCODING',
      help="""The encoding of messages validated against the schema.""",
      required=True,
  )
  set_schema_settings_group.add_argument(
      '--first-revision-id',
      help="""The id of the oldest
      revision allowed for the specified schema.""",
      required=False,
  )
  set_schema_settings_group.add_argument(
      '--last-revision-id',
      help="""The id of the most recent
      revision allowed for the specified schema""",
      required=False,
  )


def AddIngestionDatasourceFlags(parser, is_update=False):
  """Adds the flags for Datasource Ingestion.

  Args:
    parser: The argparse parser
    is_update: (bool) If true, add a wrapper group with
      clear-ingestion-data-source-settings as a mutually exclusive argument.
  """
  current_group = parser

  if is_update:
    clear_settings_group = current_group.add_mutually_exclusive_group(
        help=(
            'Specify either --clear-ingestion-data-source-settings or a new'
            ' ingestion source.'
        ),
        hidden=True,
    )
    AddBooleanFlag(
        parser=clear_settings_group,
        flag_name='clear-ingestion-data-source-settings',
        action='store_true',
        default=None,
        help_text=(
            'If set, clear the Ingestion Data Source Settings from the topic.'
        ),
    )
    current_group = clear_settings_group

  ingestion_source_types_group = current_group.add_mutually_exclusive_group(
      hidden=(not is_update)
  )

  aws_kinesis_group = ingestion_source_types_group.add_argument_group(
      help=(
          'The flags for specifying an Amazon Web Services (AWS) Kinesis'
          ' Ingestion Topic'
      )
  )
  aws_kinesis_group.add_argument(
      '--kinesis-ingestion-stream-arn',
      default=None,
      help=(
          'The Kinesis data stream Amazon Resource Name (ARN) to ingest data'
          ' from.'
      ),
      required=True,
  )
  aws_kinesis_group.add_argument(
      '--kinesis-ingestion-consumer-arn',
      default=None,
      help=(
          'The Kinesis data streams consumer Amazon Resource Name (ARN) to use'
          ' for ingestion.'
      ),
      required=True,
  )
  aws_kinesis_group.add_argument(
      '--kinesis-ingestion-role-arn',
      default=None,
      help=(
          'AWS role Amazon Resource Name (ARN) to be used for Federated'
          ' Identity authentication with Kinesis.'
      ),
      required=True,
  )
  aws_kinesis_group.add_argument(
      '--kinesis-ingestion-service-account',
      default=None,
      help=(
          'The GCP service account to be used for Federated Identity'
          ' authentication with Kinesis.'
      ),
      required=True,
  )


def AddCommitSchemaFlags(parser):
  """Adds the flags for the Schema Definition.

  Args:
    parser: The argparse parser
  """
  definition_group = parser.add_group(
      mutex=True, help='Schema definition', required=True
  )
  definition_group.add_argument(
      '--definition', type=str, help='The new definition of the schema.'
  )
  definition_group.add_argument(
      '--definition-file',
      type=arg_parsers.FileContents(),
      help='File containing the new schema definition.',
  )
  parser.add_argument(
      '--type', type=str, help='The type of the schema.', required=True
  )


def AddTopicMessageRetentionFlags(parser, is_update):
  """Add flags for the topic message retention property to the parser.

  Args:
    parser: The argparse parser.
    is_update: Whether the operation is for updating message retention.
  """
  current_group = parser
  if is_update:
    mutual_exclusive_group = parser.add_mutually_exclusive_group()
    AddBooleanFlag(
        parser=mutual_exclusive_group,
        flag_name='clear-message-retention-duration',
        action='store_true',
        default=None,
        help_text="""If set, clear the message retention duration from the topic.""",
    )
    current_group = mutual_exclusive_group

  current_group.add_argument(
      '--message-retention-duration',
      type=arg_parsers.Duration(lower_bound='10m', upper_bound='31d'),
      help="""\
          Indicates the minimum duration to retain a message after it is
          published to the topic. If this field is set, messages published to
          the topic in the last MESSAGE_RETENTION_DURATION are always available
          to subscribers. For instance, it allows any attached subscription to
          seek to a timestamp that is up to MESSAGE_RETENTION_DURATION in the
          past. If this field is not set, message retention is controlled by
          settings on individual subscriptions. The minimum is 10 minutes and
          the maximum is 31 days. {}""".format(DURATION_HELP_STR),
  )


def AddTopicMessageStoragePolicyFlags(parser, is_update):
  """Add flags for the Message Storage Policy.

  Args:
    parser: The argparse parser.
    is_update: Whether the operation is for updating message storage policy.
  """
  current_group = parser
  help_message = (
      'Options for explicitly specifying the [message storage'
      ' policy](https://cloud.google.com/pubsub/docs/resource-location-restriction)'
      ' for a topic.'
  )

  if is_update:
    recompute_msp_group = current_group.add_group(
        mutex=True, help='Message storage policy options.'
    )
    recompute_msp_group.add_argument(
        '--recompute-message-storage-policy',
        action='store_true',
        help=(
            'If given, Pub/Sub recomputes the regions where messages'
            ' can be stored at rest, based on your organization\'s "Resource '
            ' Location Restriction" policy.'
        ),
    )
    current_group = recompute_msp_group
    help_message = (
        f'{help_message} These fields can be set only if the'
        ' `--recompute-message-storage-policy` flag is not set.'
    )

  explicit_msp_group = current_group.add_argument_group(help=(help_message))
  explicit_msp_group.add_argument(
      '--message-storage-policy-allowed-regions',
      metavar='REGION',
      type=arg_parsers.ArgList(),
      required=True,
      help=(
          'A list of one or more Cloud regions where messages are allowed to'
          ' be stored at rest.'
      ),
  )
  explicit_msp_group.add_argument(
      '--message-storage-policy-enforce-in-transit',
      action='store_true',
      help=(
          'Whether or not to enforce in-transit guarantees for this topic'
          ' using the allowed regions. This ensures that publishing, pulling,'
          ' and push delivery are only handled in allowed Cloud regions.'
      ),
  )


def ParseMessageBody(args):
  """Gets the message body from args.

  This is only necessary because we are deprecating the positional `ack_id`.
  Putting the positional and a flag in an argument group, will group flag
  under positional args. This would be confusing.

  DeprecationAction can't be used here because the positional argument is
  optional (nargs='?') Since this means zero or more, the DeprecationAction
  warn message is always triggered.

  This function does not exist in util.py in order to group the explanation for
  why this exists with the deprecated flags.

  Once the positional is removed, this function can be removed.

  Args:
    args (argparse.Namespace): Parsed arguments

  Returns:
    Optional[str]: message body.
  """
  if args.message_body and args.message:
    raise exceptions.ConflictingArgumentsException('MESSAGE_BODY', '--message')

  if args.message_body is not None:
    log.warning(DEPRECATION_FORMAT_STR.format('MESSAGE_BODY', '--message'))
  return args.message_body or args.message


def ValidateFilterString(args):
  """Raises an exception if filter string is empty.

  Args:
    args (argparse.Namespace): Parsed arguments

  Raises:
    InvalidArgumentException: if filter string is empty.
  """
  if args.message_filter is not None and not args.message_filter:
    raise exceptions.InvalidArgumentException(
        '--message-filter',
        'Filter string must be non-empty. If you do not want a filter, '
        + 'do not set the --message-filter argument.',
    )


def ValidateDeadLetterPolicy(args):
  """Raises an exception if args has invalid dead letter arguments.

  Args:
    args (argparse.Namespace): Parsed arguments

  Raises:
    RequiredArgumentException: if max_delivery_attempts is set without
      dead_letter_topic being present.
  """
  if args.max_delivery_attempts and not args.dead_letter_topic:
    raise exceptions.RequiredArgumentException(
        'DEAD_LETTER_TOPIC', '--dead-letter-topic'
    )
