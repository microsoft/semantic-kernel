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
"""Cloud Pub/Sub topics update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

DETAILED_HELP = {'EXAMPLES': """\
          To update existing labels on a Cloud Pub/Sub topic, run:

              $ {command} mytopic --update-labels=KEY1=VAL1,KEY2=VAL2

          To clear all labels on a Cloud Pub/Sub topic, run:

              $ {command} mytopic --clear-labels

          To remove an existing label on a Cloud Pub/Sub topic, run:

              $ {command} mytopic --remove-labels=KEY1,KEY2

          To enable customer-managed encryption for a Cloud Pub/Sub topic by protecting message data with a Cloud KMS CryptoKey, run:

              $ {command} mytopic --topic-encryption-key=projects/PROJECT_ID/locations/KMS_LOCATION/keyRings/KEYRING/cryptoKeys/KEY

          To enable or update retention on a Cloud Pub/Sub topic, run:

              $ {command} mytopic --message-retention-duration=MESSAGE_RETENTION_DURATION

          To disable retention on a Cloud Pub/Sub topic, run:

              $ {command} mytopic --clear-message-retention-duration

          To update a Cloud Pub/Sub topic's message storage policy, run:

              $ {command} mytopic --message-storage-policy-allowed-regions=some-cloud-region1,some-cloud-region2

          To recompute a Cloud Pub/Sub topic's message storage policy based on your organization's "Resource Location Restriction" policy, run:

              $ {command} mytopic --recompute-message-storage-policy

          To enforce both at-rest and in-transit guarantees for messages published to the topic, run:

              $ {command} mytopic --message-storage-policy-allowed-regions=some-cloud-region1,some-cloud-region2 --message-storage-policy-enforce-in-transit
          """}

_KMS_FLAG_OVERRIDES = {
    'kms-key': '--topic-encryption-key',
    'kms-keyring': '--topic-encryption-key-keyring',
    'kms-location': '--topic-encryption-key-location',
    'kms-project': '--topic-encryption-key-project',
}

_KMS_PERMISSION_INFO = """
The specified Cloud KMS key should have purpose set to "ENCRYPT_DECRYPT".
The service account,
"service-${CONSUMER_PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com"
requires the IAM cryptoKeyEncrypterDecrypter role for the given Cloud KMS key.
CONSUMER_PROJECT_NUMBER is the project number of the project that is the parent
of the topic being updated"""


def _GetKmsKeyNameFromArgs(args):
  """Parses the KMS key resource name from args.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.

  Returns:
    The KMS CryptoKey resource name for the key specified in args, or None.
  """
  kms_ref = args.CONCEPTS.kms_key.Parse()
  if kms_ref:
    return kms_ref.RelativeName()

  # Check whether the user specified any topic-encryption-key flags.
  for keyword in [
      'topic-encryption-key',
      'topic-encryption-key-project',
      'topic-encryption-key-location',
      'topic-encryption-key-keyring',
  ]:
    if args.IsSpecified(keyword.replace('-', '_')):
      raise core_exceptions.Error(
          '--topic-encryption-key was not fully specified.'
      )

  return None


def _Args(parser, include_ingestion_flags=False):
  """Registers flags for this command."""
  resource_args.AddTopicResourceArg(parser, 'to update.')
  labels_util.AddUpdateLabelsFlags(parser)
  resource_args.AddResourceArgs(
      parser,
      [
          kms_resource_args.GetKmsKeyPresentationSpec(
              'topic',
              flag_overrides=_KMS_FLAG_OVERRIDES,
              permission_info=_KMS_PERMISSION_INFO,
          )
      ],
  )
  flags.AddTopicMessageRetentionFlags(parser, is_update=True)

  flags.AddTopicMessageStoragePolicyFlags(parser, is_update=True)

  flags.AddSchemaSettingsFlags(parser, is_update=True)
  if include_ingestion_flags:
    flags.AddIngestionDatasourceFlags(parser, is_update=True)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Updates an existing Cloud Pub/Sub topic."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    _Args(parser, include_ingestion_flags=False)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A serialized object (dict) describing the results of the operation.

    Raises:
      An HttpException if there was a problem calling the
      API topics.Patch command.
    """
    client = topics.TopicsClient()
    topic_ref = args.CONCEPTS.topic.Parse()

    message_retention_duration = getattr(
        args, 'message_retention_duration', None
    )
    if message_retention_duration:
      message_retention_duration = util.FormatDuration(
          message_retention_duration
      )
    clear_message_retention_duration = getattr(
        args, 'clear_message_retention_duration', None
    )

    labels_update = labels_util.ProcessUpdateArgsLazy(
        args,
        client.messages.Topic.LabelsValue,
        orig_labels_thunk=lambda: client.Get(topic_ref).labels,
    )

    schema = getattr(args, 'schema', None)
    if schema:
      schema = args.CONCEPTS.schema.Parse().RelativeName()
    message_encoding_list = getattr(args, 'message_encoding', None)
    message_encoding = None
    if message_encoding_list:
      message_encoding = message_encoding_list[0]
    first_revision_id = getattr(args, 'first_revision_id', None)
    last_revision_id = getattr(args, 'last_revision_id', None)
    result = None
    clear_schema_settings = getattr(args, 'clear_schema_settings', None)

    message_storage_policy_enforce_in_transit = getattr(
        args, 'message_storage_policy_enforce_in_transit', None
    )

    kinesis_ingestion_stream_arn = getattr(
        args, 'kinesis_ingestion_stream_arn', None
    )
    kinesis_ingestion_consumer_arn = getattr(
        args, 'kinesis_ingestion_consumer_arn', None
    )
    kinesis_ingestion_role_arn = getattr(
        args, 'kinesis_ingestion_role_arn', None
    )
    kinesis_ingestion_service_account = getattr(
        args, 'kinesis_ingestion_service_account', None
    )
    clear_ingestion_data_source_settings = getattr(
        args, 'clear_ingestion_data_source_settings', None
    )

    try:
      result = client.Patch(
          topic_ref,
          labels_update.GetOrNone(),
          _GetKmsKeyNameFromArgs(args),
          message_retention_duration,
          clear_message_retention_duration,
          args.recompute_message_storage_policy,
          args.message_storage_policy_allowed_regions,
          message_storage_policy_enforce_in_transit,
          schema=schema,
          message_encoding=message_encoding,
          first_revision_id=first_revision_id,
          last_revision_id=last_revision_id,
          clear_schema_settings=clear_schema_settings,
          kinesis_ingestion_stream_arn=kinesis_ingestion_stream_arn,
          kinesis_ingestion_consumer_arn=kinesis_ingestion_consumer_arn,
          kinesis_ingestion_role_arn=kinesis_ingestion_role_arn,
          kinesis_ingestion_service_account=kinesis_ingestion_service_account,
          clear_ingestion_data_source_settings=clear_ingestion_data_source_settings,
      )
    except topics.NoFieldsSpecifiedError:
      operations = [
          'clear_labels',
          'update_labels',
          'remove_labels',
          'recompute_message_storage_policy',
          'message_storage_policy_allowed_regions',
      ]
      if not any(args.IsSpecified(arg) for arg in operations):
        raise
      log.status.Print('No update to perform.')
    else:
      log.UpdatedResource(topic_ref.RelativeName(), kind='topic')
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Updates an existing Cloud Pub/Sub topic."""

  @staticmethod
  def Args(parser):
    _Args(parser, include_ingestion_flags=False)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Updates an existing Cloud Pub/Sub topic."""

  @staticmethod
  def Args(parser):
    _Args(parser, include_ingestion_flags=True)
