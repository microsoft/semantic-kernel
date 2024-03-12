# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Cloud Pub/Sub subscriptions create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_ex
from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _Run(
    args,
    enable_labels=False,
    legacy_output=False,
    enable_push_to_cps=False,
    enable_cps_gcs_file_datetime_format=False,
):
  """Creates one or more subscriptions."""
  flags.ValidateDeadLetterPolicy(args)

  client = subscriptions.SubscriptionsClient()

  topic_ref = args.CONCEPTS.topic.Parse()
  push_config = util.ParsePushConfig(args)
  enable_message_ordering = getattr(args, 'enable_message_ordering', None)
  filter_string = getattr(args, 'message_filter', None)
  dead_letter_topic = getattr(args, 'dead_letter_topic', None)
  max_delivery_attempts = getattr(args, 'max_delivery_attempts', None)
  retain_acked_messages = getattr(args, 'retain_acked_messages', None)
  retention_duration = getattr(args, 'message_retention_duration', None)
  enable_exactly_once_delivery = getattr(
      args, 'enable_exactly_once_delivery', None
  )
  if args.IsSpecified('message_retention_duration'):
    retention_duration = util.FormatDuration(retention_duration)
  min_retry_delay = getattr(args, 'min_retry_delay', None)
  if args.IsSpecified('min_retry_delay'):
    min_retry_delay = util.FormatDuration(min_retry_delay)
  max_retry_delay = getattr(args, 'max_retry_delay', None)
  if args.IsSpecified('max_retry_delay'):
    max_retry_delay = util.FormatDuration(max_retry_delay)
  bigquery_table = getattr(args, 'bigquery_table', None)
  use_topic_schema = getattr(args, 'use_topic_schema', None)
  use_table_schema = getattr(args, 'use_table_schema', None)
  write_metadata = getattr(args, 'write_metadata', None)
  drop_unknown_fields = getattr(args, 'drop_unknown_fields', None)
  cloud_storage_bucket = getattr(args, 'cloud_storage_bucket', None)
  cloud_storage_file_prefix = getattr(args, 'cloud_storage_file_prefix', None)
  cloud_storage_file_suffix = getattr(args, 'cloud_storage_file_suffix', None)
  cloud_storage_file_datetime_format = (
      getattr(args, 'cloud_storage_file_datetime_format', None)
      if enable_cps_gcs_file_datetime_format
      else None
  )
  cloud_storage_max_bytes = getattr(args, 'cloud_storage_max_bytes', None)
  cloud_storage_max_duration = getattr(args, 'cloud_storage_max_duration', None)
  if args.IsSpecified('cloud_storage_max_duration'):
    cloud_storage_max_duration = util.FormatDuration(cloud_storage_max_duration)
  cloud_storage_output_format_list = getattr(
      args, 'cloud_storage_output_format', None
  )
  cloud_storage_output_format = None
  if cloud_storage_output_format_list:
    cloud_storage_output_format = cloud_storage_output_format_list[0]
  cloud_storage_write_metadata = getattr(
      args, 'cloud_storage_write_metadata', None
  )
  pubsub_export_topic = (
      getattr(args, 'pubsub_export_topic', None) if enable_push_to_cps else None
  )
  pubsub_export_topic_region = getattr(args, 'pubsub_export_topic_region', None)

  no_expiration = False
  expiration_period = getattr(args, 'expiration_period', None)
  if args.IsSpecified('expiration_period'):
    if expiration_period == subscriptions.NEVER_EXPIRATION_PERIOD_VALUE:
      no_expiration = True
      expiration_period = None

  if dead_letter_topic:
    dead_letter_topic = args.CONCEPTS.dead_letter_topic.Parse().RelativeName()

  if pubsub_export_topic:
    pubsub_export_topic = (
        args.CONCEPTS.pubsub_export_topic.Parse().RelativeName()
    )

  labels = None
  if enable_labels:
    labels = labels_util.ParseCreateArgs(
        args, client.messages.Subscription.LabelsValue
    )

  failed = []
  for subscription_ref in args.CONCEPTS.subscription.Parse():
    try:
      result = client.Create(
          subscription_ref,
          topic_ref,
          args.ack_deadline,
          push_config,
          retain_acked_messages,
          retention_duration,
          labels=labels,
          no_expiration=no_expiration,
          expiration_period=expiration_period,
          enable_message_ordering=enable_message_ordering,
          filter_string=filter_string,
          dead_letter_topic=dead_letter_topic,
          max_delivery_attempts=max_delivery_attempts,
          min_retry_delay=min_retry_delay,
          max_retry_delay=max_retry_delay,
          enable_exactly_once_delivery=enable_exactly_once_delivery,
          bigquery_table=bigquery_table,
          use_topic_schema=use_topic_schema,
          use_table_schema=use_table_schema,
          write_metadata=write_metadata,
          drop_unknown_fields=drop_unknown_fields,
          cloud_storage_bucket=cloud_storage_bucket,
          cloud_storage_file_prefix=cloud_storage_file_prefix,
          cloud_storage_file_suffix=cloud_storage_file_suffix,
          cloud_storage_file_datetime_format=cloud_storage_file_datetime_format,
          cloud_storage_max_bytes=cloud_storage_max_bytes,
          cloud_storage_max_duration=cloud_storage_max_duration,
          cloud_storage_output_format=cloud_storage_output_format,
          cloud_storage_write_metadata=cloud_storage_write_metadata,
          pubsub_export_topic=pubsub_export_topic,
          pubsub_export_topic_region=pubsub_export_topic_region,
      )
    except api_ex.HttpError as error:
      exc = exceptions.HttpException(error)
      log.CreatedResource(
          subscription_ref.RelativeName(),
          kind='subscription',
          failed=util.CreateFailureErrorMessage(exc.payload.status_message),
      )
      failed.append(subscription_ref.subscriptionsId)
      continue

    if legacy_output:
      result = util.SubscriptionDisplayDict(result)

    log.CreatedResource(subscription_ref.RelativeName(), kind='subscription')
    yield result

  if failed:
    raise util.RequestsFailedError(failed, 'create')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Creates one or more Cloud Pub/Sub subscriptions."""

  detailed_help = {'DESCRIPTION': """\
          Creates one or more Cloud Pub/Sub subscriptions for a given topic.
          The new subscription defaults to a PULL subscription unless a push
          endpoint is specified."""}

  @classmethod
  def Args(cls, parser):
    topic_help_text = (
        'from which this subscription is receiving messages. '
        'Each subscription is attached to a single topic.'
    )
    topic = resource_args.CreateTopicResourceArg(
        topic_help_text, positional=False
    )
    subscription = resource_args.CreateSubscriptionResourceArg(
        'to create.', plural=True
    )
    resource_args.AddResourceArgs(parser, [topic, subscription])
    flags.AddSubscriptionSettingsFlags(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    flags.ValidateFilterString(args)
    return _Run(args, enable_labels=True)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateBeta(Create):
  """Creates one or more Cloud Pub/Sub subscriptions."""

  @classmethod
  def Args(cls, parser):
    topic_help_text = (
        'from which this subscription is receiving messages. '
        'Each subscription is attached to a single topic.'
    )
    topic = resource_args.CreateTopicResourceArg(
        topic_help_text, positional=False
    )
    subscription = resource_args.CreateSubscriptionResourceArg(
        'to create.', plural=True
    )
    resource_args.AddResourceArgs(parser, [topic, subscription])
    flags.AddSubscriptionSettingsFlags(
        parser,
        enable_push_to_cps=True,
        enable_cps_gcs_file_datetime_format=True,
    )
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    flags.ValidateFilterString(args)
    legacy_output = properties.VALUES.pubsub.legacy_output.GetBool()
    return _Run(
        args,
        enable_labels=True,
        legacy_output=legacy_output,
        enable_push_to_cps=True,
        enable_cps_gcs_file_datetime_format=True,
    )
