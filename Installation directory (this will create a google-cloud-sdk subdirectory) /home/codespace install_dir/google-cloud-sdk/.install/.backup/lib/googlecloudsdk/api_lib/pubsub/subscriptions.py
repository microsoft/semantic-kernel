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

"""Utilities for Cloud Pub/Sub Subscriptions API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import exceptions


PULL_RPC_DEADLINE_SECONDS = '20'
SERVER_TIMEOUT_HEADER = 'X-Server-Timeout'
DEFAULT_MESSAGE_RETENTION_VALUE = 'default'
NEVER_EXPIRATION_PERIOD_VALUE = 'never'
CLEAR_DEAD_LETTER_VALUE = 'clear'
CLEAR_RETRY_VALUE = 'clear'
CLEAR_BIGQUERY_CONFIG_VALUE = 'clear'
CLEAR_CLOUD_STORAGE_CONFIG_VALUE = 'clear'
CLEAR_PUSH_NO_WRAPPER_CONFIG_VALUE = 'clear'
CLEAR_PUBSUB_EXPORT_CONFIG_VALUE = 'clear'


class NoFieldsSpecifiedError(exceptions.Error):
  """Error when no fields were specified for a Patch operation."""


def GetClientInstance(no_http=False):
  return apis.GetClientInstance('pubsub', 'v1', no_http=no_http)


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


class _SubscriptionUpdateSetting(object):
  """Data container class for updating a subscription."""

  def __init__(self, field_name, value):
    self.field_name = field_name
    self.value = value


class SubscriptionsClient(object):
  """Client for subscriptions service in the Cloud Pub/Sub API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_subscriptions

  def Ack(self, ack_ids, subscription_ref):
    """Acknowledges one or messages for a Subscription.

    Args:
      ack_ids (list[str]): List of ack ids for the messages being ack'd.
      subscription_ref (Resource): Relative name of the subscription for which
        to ack messages for.

    Returns:
      None:
    """
    ack_req = self.messages.PubsubProjectsSubscriptionsAcknowledgeRequest(
        acknowledgeRequest=self.messages.AcknowledgeRequest(ackIds=ack_ids),
        subscription=subscription_ref.RelativeName(),
    )

    return self._service.Acknowledge(ack_req)

  def Get(self, subscription_ref):
    """Gets a Subscription from the API.

    Args:
      subscription_ref (Resource): Relative name of the subscription to get.

    Returns:
      Subscription: the subscription.
    """
    get_req = self.messages.PubsubProjectsSubscriptionsGetRequest(
        subscription=subscription_ref.RelativeName()
    )

    return self._service.Get(get_req)

  def Create(
      self,
      subscription_ref,
      topic_ref,
      ack_deadline,
      push_config=None,
      retain_acked_messages=None,
      message_retention_duration=None,
      labels=None,
      no_expiration=False,
      expiration_period=None,
      enable_message_ordering=None,
      filter_string=None,
      dead_letter_topic=None,
      max_delivery_attempts=None,
      min_retry_delay=None,
      max_retry_delay=None,
      enable_exactly_once_delivery=None,
      bigquery_table=None,
      use_topic_schema=None,
      use_table_schema=None,
      write_metadata=None,
      drop_unknown_fields=None,
      cloud_storage_bucket=None,
      cloud_storage_file_prefix=None,
      cloud_storage_file_suffix=None,
      cloud_storage_file_datetime_format=None,
      cloud_storage_max_bytes=None,
      cloud_storage_max_duration=None,
      cloud_storage_output_format=None,
      cloud_storage_write_metadata=None,
      pubsub_export_topic=None,
      pubsub_export_topic_region=None,
  ):
    """Creates a Subscription.

    Args:
      subscription_ref (Resource): Resource reference for subscription to be
        created.
      topic_ref (Resource): Resource reference for the associated topic for the
        subscriptions.
      ack_deadline (int): Number of seconds the system will wait for a
        subscriber to ack a message.
      push_config (Message): Message containing the push endpoint for the
        subscription.
      retain_acked_messages (bool): Whether or not to retain acked messages.
      message_retention_duration (int): How long to retained unacked messages.
      labels (Subscriptions.LabelsValue): The labels for the request.
      no_expiration (bool): Whether or not to set no expiration on subscription.
      expiration_period (str): TTL on expiration_policy.
      enable_message_ordering (bool): Whether or not to deliver messages with
        the same ordering key in order.
      filter_string (str): filter string in the Cloud Pub/Sub filter language.
      dead_letter_topic (str): Topic for publishing dead messages.
      max_delivery_attempts (int): Threshold of failed deliveries before sending
        message to the dead letter topic.
      min_retry_delay (str): The minimum delay between consecutive deliveries of
        a given message.
      max_retry_delay (str): The maximum delay between consecutive deliveries of
        a given message.
      enable_exactly_once_delivery (bool): Whether or not to set exactly once
        delivery on the subscription.
      bigquery_table (str): BigQuery table to which to write
      use_topic_schema (bool): Whether or not to use the topic schema when
        writing to BigQuery
      use_table_schema (bool): Whether or not to use the table schema when
        writing to BigQuery
      write_metadata (bool): Whether or not to write metadata fields when
        writing to BigQuery
      drop_unknown_fields (bool): Whether or not to drop fields that are only in
        the topic schema when writing to BigQuery
      cloud_storage_bucket (str): The name for the Cloud Storage bucket.
      cloud_storage_file_prefix (str): The prefix for Cloud Storage filename.
      cloud_storage_file_suffix (str): The suffix for Cloud Storage filename.
      cloud_storage_file_datetime_format (str): The custom datetime format
        string for Cloud Storage filename.
      cloud_storage_max_bytes (int): The maximum bytes that can be written to a
        Cloud Storage file before a new file is created.
      cloud_storage_max_duration (str): The maximum duration that can elapse
        before a new Cloud Storage file is created.
      cloud_storage_output_format (str): The output format for data written to
        Cloud Storage.
      cloud_storage_write_metadata (bool): Whether or not to write the
        subscription name and other metadata in the output.
      pubsub_export_topic (str): The Pubsub topic to which to publish messages.
      pubsub_export_topic_region (str): The Cloud region to which to publish
        messages.

    Returns:
      Subscription: the created subscription
    """
    subscription = self.messages.Subscription(
        name=subscription_ref.RelativeName(),
        topic=topic_ref.RelativeName(),
        ackDeadlineSeconds=ack_deadline,
        pushConfig=push_config,
        retainAckedMessages=retain_acked_messages,
        labels=labels,
        messageRetentionDuration=message_retention_duration,
        expirationPolicy=self._ExpirationPolicy(
            no_expiration, expiration_period
        ),
        enableMessageOrdering=enable_message_ordering,
        filter=filter_string,
        deadLetterPolicy=self._DeadLetterPolicy(
            dead_letter_topic, max_delivery_attempts
        ),
        retryPolicy=self._RetryPolicy(min_retry_delay, max_retry_delay),
        enableExactlyOnceDelivery=enable_exactly_once_delivery,
        bigqueryConfig=self._BigQueryConfig(
            bigquery_table,
            use_topic_schema,
            use_table_schema,
            write_metadata,
            drop_unknown_fields,
        ),
        cloudStorageConfig=self._CloudStorageConfig(
            cloud_storage_bucket,
            cloud_storage_file_prefix,
            cloud_storage_file_suffix,
            cloud_storage_file_datetime_format,
            cloud_storage_max_bytes,
            cloud_storage_max_duration,
            cloud_storage_output_format,
            cloud_storage_write_metadata,
        ),
        pubsubExportConfig=self._PubsubExportConfig(
            pubsub_export_topic, pubsub_export_topic_region
        ),
    )
    return self._service.Create(subscription)

  def Delete(self, subscription_ref):
    """Deletes a Subscription.

    Args:
      subscription_ref (Resource): Resource reference for subscription to be
        deleted.

    Returns:
      None:
    """
    delete_req = self.messages.PubsubProjectsSubscriptionsDeleteRequest(
        subscription=subscription_ref.RelativeName()
    )
    return self._service.Delete(delete_req)

  def List(self, project_ref, page_size=100):
    """Lists Subscriptions for a given project.

    Args:
      project_ref (Resource): Resource reference to Project to list
        subscriptions from.
      page_size (int): the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      A generator of subscriptions in the project.
    """
    list_req = self.messages.PubsubProjectsSubscriptionsListRequest(
        project=project_ref.RelativeName(), pageSize=page_size
    )
    return list_pager.YieldFromList(
        self._service,
        list_req,
        batch_size=page_size,
        field='subscriptions',
        batch_size_attribute='pageSize',
    )

  def ModifyAckDeadline(self, subscription_ref, ack_ids, ack_deadline):
    """Modifies the ack deadline for messages for a Subscription.

    Args:
      subscription_ref (Resource): Resource reference for subscription to be
        modified.
      ack_ids (list[str]): List of ack ids to modify.
      ack_deadline (int): The new ack deadline for the messages.

    Returns:
      None:
    """
    mod_req = self.messages.PubsubProjectsSubscriptionsModifyAckDeadlineRequest(
        modifyAckDeadlineRequest=self.messages.ModifyAckDeadlineRequest(
            ackDeadlineSeconds=ack_deadline, ackIds=ack_ids
        ),
        subscription=subscription_ref.RelativeName(),
    )

    return self._service.ModifyAckDeadline(mod_req)

  def ModifyPushConfig(self, subscription_ref, push_config):
    """Modifies the push endpoint for a Subscription.

    Args:
      subscription_ref (Resource): Resource reference for subscription to be
        modified.
      push_config (Message): The new push endpoint for the Subscription.

    Returns:
      None:
    """
    mod_req = self.messages.PubsubProjectsSubscriptionsModifyPushConfigRequest(
        modifyPushConfigRequest=self.messages.ModifyPushConfigRequest(
            pushConfig=push_config
        ),
        subscription=subscription_ref.RelativeName(),
    )
    return self._service.ModifyPushConfig(mod_req)

  def Pull(self, subscription_ref, max_messages, return_immediately=True):
    """Pulls one or more messages from a Subscription.

    Args:
      subscription_ref (Resource): Resource reference for subscription to be
        pulled from.
      max_messages (int): The maximum number of messages to retrieve.
      return_immediately (bool): Whether or not to return immediately without
        waiting for a new message for a bounded amount of time if there is
        nothing to pull right now.

    Returns:
      PullResponse: proto containing the received messages.
    """
    pull_req = self.messages.PubsubProjectsSubscriptionsPullRequest(
        pullRequest=self.messages.PullRequest(
            maxMessages=max_messages, returnImmediately=return_immediately
        ),
        subscription=subscription_ref.RelativeName(),
    )
    self.client.additional_http_headers[SERVER_TIMEOUT_HEADER] = (
        PULL_RPC_DEADLINE_SECONDS
    )
    pull_resp = self._service.Pull(pull_req)
    del self.client.additional_http_headers[SERVER_TIMEOUT_HEADER]
    return pull_resp

  def Seek(self, subscription_ref, time=None, snapshot_ref=None):
    """Reset a Subscription's backlog to point to a given time or snapshot.

    Args:
      subscription_ref (Resource): Resource reference for subscription to be
        seeked on.
      time (str): The time to reset to.
      snapshot_ref (Resource): Resource reference to a snapshot..

    Returns:
      None:
    """
    snapshot = snapshot_ref and snapshot_ref.RelativeName()
    seek_req = self.messages.PubsubProjectsSubscriptionsSeekRequest(
        seekRequest=self.messages.SeekRequest(snapshot=snapshot, time=time),
        subscription=subscription_ref.RelativeName(),
    )
    return self._service.Seek(seek_req)

  def _ExpirationPolicy(self, no_expiration, expiration_period):
    """Build ExpirationPolicy message from argument values.

    Args:
      no_expiration (bool): Whether or not to set no expiration on subscription.
      expiration_period (str): TTL on expiration_policy.

    Returns:
      ExpirationPolicy message or None.
    """
    if no_expiration:
      return self.messages.ExpirationPolicy(ttl=None)
    if expiration_period:
      return self.messages.ExpirationPolicy(ttl=expiration_period)
    return None

  def _DeadLetterPolicy(self, dead_letter_topic, max_delivery_attempts):
    """Builds DeadLetterPolicy message from argument values.

    Args:
      dead_letter_topic (str): Topic for publishing dead messages.
      max_delivery_attempts (int): Threshold of failed deliveries before sending
        message to the dead letter topic.

    Returns:
      DeadLetterPolicy message or None.
    """
    if dead_letter_topic:
      return self.messages.DeadLetterPolicy(
          deadLetterTopic=dead_letter_topic,
          maxDeliveryAttempts=max_delivery_attempts,
      )
    return None

  def _RetryPolicy(self, min_retry_delay, max_retry_delay):
    """Builds RetryPolicy message from argument values.

    Args:
      min_retry_delay (str): The minimum delay between consecutive deliveries of
        a given message.
      max_retry_delay (str): The maximum delay between consecutive deliveries of
        a given message.

    Returns:
      DeadLetterPolicy message or None.
    """
    if min_retry_delay or max_retry_delay:
      return self.messages.RetryPolicy(
          minimumBackoff=min_retry_delay, maximumBackoff=max_retry_delay
      )
    return None

  def _BigQueryConfig(
      self,
      table,
      use_topic_schema,
      use_table_schema,
      write_metadata,
      drop_unknown_fields,
  ):
    """Builds BigQueryConfig message from argument values.

    Args:
      table (str): The name of the table
      use_topic_schema (bool): Whether or not to use the topic schema
      use_table_schema (bool): Whether or not to use the table schema
      write_metadata (bool): Whether or not to write metadata fields
      drop_unknown_fields (bool): Whether or not to drop fields that are only in
        the topic schema

    Returns:
      BigQueryConfig message or None
    """
    if table:
      return self.messages.BigQueryConfig(
          table=table,
          useTopicSchema=use_topic_schema,
          useTableSchema=use_table_schema,
          writeMetadata=write_metadata,
          dropUnknownFields=drop_unknown_fields,
      )
    return None

  def _CloudStorageConfig(
      self,
      bucket,
      file_prefix,
      file_suffix,
      file_datetime_format,
      max_bytes,
      max_duration,
      output_format,
      write_metadata,
  ):
    """Builds CloudStorageConfig message from argument values.

    Args:
      bucket (str): The name for the Cloud Storage bucket.
      file_prefix (str): The prefix for Cloud Storage filename.
      file_suffix (str): The suffix for Cloud Storage filename.
      file_datetime_format (str): The custom datetime format string for Cloud
        Storage filename.
      max_bytes (int): The maximum bytes that can be written to a Cloud Storage
        file before a new file is created.
      max_duration (str): The maximum duration that can elapse before a new
        Cloud Storage file is created.
      output_format (str): The output format for data written to Cloud Storage.
      write_metadata (bool): Whether or not to write the subscription name and
        other metadata in the output.

    Returns:
      CloudStorageConfig message or None
    """
    if bucket:
      cloud_storage_config = self.messages.CloudStorageConfig(
          bucket=bucket,
          filenamePrefix=file_prefix,
          filenameSuffix=file_suffix,
          filenameDatetimeFormat=file_datetime_format,
          maxBytes=max_bytes,
          maxDuration=max_duration,
      )
      if output_format == 'text':
        cloud_storage_config.textConfig = self.messages.TextConfig()
      elif output_format == 'avro':
        cloud_storage_config.avroConfig = self.messages.AvroConfig(
            writeMetadata=write_metadata if write_metadata else False
        )
      return cloud_storage_config
    return None

  def _PubsubExportConfig(self, topic, region):
    """Builds PubsubExportConfig message from argument values.

    Args:
      topic (str): The Pubsub topic to which to publish messages.
      region (str): The Cloud region to which to publish messages.

    Returns:
      PubsubExportConfig message or None
    """
    if topic:
      return self.messages.PubSubExportConfig(topic=topic, region=region)
    return None

  def _HandleMessageRetentionUpdate(self, update_setting):
    if update_setting.value == DEFAULT_MESSAGE_RETENTION_VALUE:
      update_setting.value = None

  def _HandleDeadLetterPolicyUpdate(self, update_setting):
    if update_setting.value == CLEAR_DEAD_LETTER_VALUE:
      update_setting.value = None

  def _HandleRetryPolicyUpdate(self, update_setting):
    if update_setting.value == CLEAR_RETRY_VALUE:
      update_setting.value = None

  def _HandleBigQueryConfigUpdate(self, update_setting):
    if update_setting.value == CLEAR_BIGQUERY_CONFIG_VALUE:
      update_setting.value = None

  def _HandleCloudStorageConfigUpdate(self, update_setting):
    if update_setting.value == CLEAR_CLOUD_STORAGE_CONFIG_VALUE:
      update_setting.value = None

  def _HandlePushNoWrapperUpdate(self, update_setting):
    if update_setting.value == CLEAR_PUSH_NO_WRAPPER_CONFIG_VALUE:
      update_setting.value = None

  def _HandlePubsubExportConfigUpdate(self, update_setting):
    if update_setting.value == CLEAR_PUBSUB_EXPORT_CONFIG_VALUE:
      update_setting.value = None

  def Patch(
      self,
      subscription_ref,
      ack_deadline=None,
      push_config=None,
      retain_acked_messages=None,
      message_retention_duration=None,
      labels=None,
      no_expiration=False,
      expiration_period=None,
      dead_letter_topic=None,
      max_delivery_attempts=None,
      clear_dead_letter_policy=False,
      min_retry_delay=None,
      max_retry_delay=None,
      clear_retry_policy=False,
      enable_exactly_once_delivery=None,
      bigquery_table=None,
      use_topic_schema=None,
      use_table_schema=None,
      write_metadata=None,
      drop_unknown_fields=None,
      clear_bigquery_config=False,
      cloud_storage_bucket=None,
      cloud_storage_file_prefix=None,
      cloud_storage_file_suffix=None,
      cloud_storage_file_datetime_format=None,
      cloud_storage_max_bytes=None,
      cloud_storage_max_duration=None,
      cloud_storage_output_format=None,
      cloud_storage_write_metadata=None,
      clear_cloud_storage_config=False,
      clear_push_no_wrapper_config=False,
      pubsub_export_topic=None,
      pubsub_export_topic_region=None,
      clear_pubsub_export_config=False,
  ):
    """Updates a Subscription.

    Args:
      subscription_ref (Resource): Resource reference for subscription to be
        updated.
      ack_deadline (int): Number of seconds the system will wait for a
        subscriber to ack a message.
      push_config (Message): Message containing the push endpoint for the
        subscription.
      retain_acked_messages (bool): Whether or not to retain acked messages.
      message_retention_duration (str): How long to retained unacked messages.
      labels (LabelsValue): The Cloud labels for the subscription.
      no_expiration (bool): Whether or not to set no expiration on subscription.
      expiration_period (str): TTL on expiration_policy.
      dead_letter_topic (str): Topic for publishing dead messages.
      max_delivery_attempts (int): Threshold of failed deliveries before sending
        message to the dead letter topic.
      clear_dead_letter_policy (bool): If set, clear the dead letter policy from
        the subscription.
      min_retry_delay (str): The minimum delay between consecutive deliveries of
        a given message.
      max_retry_delay (str): The maximum delay between consecutive deliveries of
        a given message.
      clear_retry_policy (bool): If set, clear the retry policy from the
        subscription.
      enable_exactly_once_delivery (bool): Whether or not to set exactly once
        delivery on the subscription.
      bigquery_table (str): BigQuery table to which to write
      use_topic_schema (bool): Whether or not to use the topic schema when
        writing to BigQuery
      use_table_schema (bool): Whether or not to use the table schema when
        writing to BigQuery
      write_metadata (bool): Whether or not to write metadata fields when
        writing to BigQuery
      drop_unknown_fields (bool): Whether or not to drop fields that are only in
        the topic schema when writing to BigQuery
      clear_bigquery_config (bool): If set, clear the BigQuery config from the
        subscription
      cloud_storage_bucket (bool): The name for the Cloud Storage bucket.
      cloud_storage_file_prefix (str): The prefix for Cloud Storage filename.
      cloud_storage_file_suffix (str): The suffix for Cloud Storage filename.
      cloud_storage_file_datetime_format (str): The custom datetime format
        string for Cloud Storage filename.
      cloud_storage_max_bytes (int): The maximum bytes that can be written to a
        Cloud Storage file before a new file is created.
      cloud_storage_max_duration (str): The maximum duration that can elapse
        before a new Cloud Storage file is created.
      cloud_storage_output_format (str): The output format for data written to
        Cloud Storage.
      cloud_storage_write_metadata (bool): Whether or not to write the
        subscription name and other metadata in the output.
      clear_cloud_storage_config (bool): If set, clear the Cloud Storage config
        from the subscription.
      clear_push_no_wrapper_config(bool): If set, clear
        the Push No Wrapper config from the subscription.
      pubsub_export_topic (str): The Pubsub topic to which to publish messages.
      pubsub_export_topic_region (str): The Cloud region to which to publish
        messages.
      clear_pubsub_export_config (bool): If set, clear the Pubsub export config
        from the subscription.

    Returns:
      Subscription: The updated subscription.
    Raises:
      NoFieldsSpecifiedError: if no fields were specified.
    """
    if clear_cloud_storage_config:
      cloud_storage_config_settings = CLEAR_CLOUD_STORAGE_CONFIG_VALUE
    else:
      cloud_storage_config_settings = self._CloudStorageConfig(
          cloud_storage_bucket,
          cloud_storage_file_prefix,
          cloud_storage_file_suffix,
          cloud_storage_file_datetime_format,
          cloud_storage_max_bytes,
          cloud_storage_max_duration,
          cloud_storage_output_format,
          cloud_storage_write_metadata,
      )

    if clear_dead_letter_policy:
      dead_letter_policy = CLEAR_DEAD_LETTER_VALUE
    else:
      dead_letter_policy = self._DeadLetterPolicy(
          dead_letter_topic, max_delivery_attempts
      )

    if clear_retry_policy:
      retry_policy = CLEAR_RETRY_VALUE
    else:
      retry_policy = self._RetryPolicy(min_retry_delay, max_retry_delay)

    if clear_bigquery_config:
      bigquery_config = CLEAR_BIGQUERY_CONFIG_VALUE
    else:
      bigquery_config = self._BigQueryConfig(
          bigquery_table,
          use_topic_schema,
          use_table_schema,
          write_metadata,
          drop_unknown_fields,
      )

    if clear_pubsub_export_config:
      pubsub_export_config = CLEAR_PUBSUB_EXPORT_CONFIG_VALUE
    else:
      pubsub_export_config = self._PubsubExportConfig(
          pubsub_export_topic, pubsub_export_topic_region
      )

    if clear_push_no_wrapper_config:
      push_config_no_wrapper = CLEAR_PUSH_NO_WRAPPER_CONFIG_VALUE
    else:
      push_config_no_wrapper = None

    update_settings = [
        _SubscriptionUpdateSetting('ackDeadlineSeconds', ack_deadline),
        _SubscriptionUpdateSetting('pushConfig', push_config),
        _SubscriptionUpdateSetting(
            'retainAckedMessages', retain_acked_messages
        ),
        _SubscriptionUpdateSetting(
            'enableExactlyOnceDelivery', enable_exactly_once_delivery
        ),
        _SubscriptionUpdateSetting(
            'messageRetentionDuration', message_retention_duration
        ),
        _SubscriptionUpdateSetting('labels', labels),
        _SubscriptionUpdateSetting(
            'expirationPolicy',
            self._ExpirationPolicy(no_expiration, expiration_period),
        ),
        _SubscriptionUpdateSetting('deadLetterPolicy', dead_letter_policy),
        _SubscriptionUpdateSetting('retryPolicy', retry_policy),
        _SubscriptionUpdateSetting('bigqueryConfig', bigquery_config),
        _SubscriptionUpdateSetting(
            'cloudStorageConfig', cloud_storage_config_settings
        ),
        _SubscriptionUpdateSetting(
            'pushConfig.noWrapper', push_config_no_wrapper
        ),
        _SubscriptionUpdateSetting('pubsubExportConfig', pubsub_export_config),
    ]
    subscription = self.messages.Subscription(
        name=subscription_ref.RelativeName()
    )
    update_mask = []
    for update_setting in update_settings:
      if update_setting.value is not None:
        if update_setting.field_name == 'messageRetentionDuration':
          self._HandleMessageRetentionUpdate(update_setting)
        if update_setting.field_name == 'deadLetterPolicy':
          self._HandleDeadLetterPolicyUpdate(update_setting)
        if update_setting.field_name == 'retryPolicy':
          self._HandleRetryPolicyUpdate(update_setting)
        if update_setting.field_name == 'bigqueryConfig':
          self._HandleBigQueryConfigUpdate(update_setting)
        if update_setting.field_name == 'cloudStorageConfig':
          self._HandleCloudStorageConfigUpdate(update_setting)
        if update_setting.field_name == 'pubsubExportConfig':
          self._HandlePubsubExportConfigUpdate(update_setting)
        if update_setting.field_name == 'pushConfig.noWrapper':
          self._HandlePushNoWrapperUpdate(update_setting)
          if push_config is None:
            update_mask.append(update_setting.field_name)
          continue
        setattr(subscription, update_setting.field_name, update_setting.value)
        update_mask.append(update_setting.field_name)
    if not update_mask:
      raise NoFieldsSpecifiedError('Must specify at least one field to update.')
    patch_req = self.messages.PubsubProjectsSubscriptionsPatchRequest(
        updateSubscriptionRequest=self.messages.UpdateSubscriptionRequest(
            subscription=subscription, updateMask=','.join(update_mask)
        ),
        name=subscription_ref.RelativeName(),
    )

    return self._service.Patch(patch_req)

  def SetIamPolicy(self, subscription_ref, policy):
    """Sets an IAM policy on a Subscription.

    Args:
      subscription_ref (Resource): Resource reference for subscription to set
        IAM policy on.
      policy (Policy): The policy to be added to the Subscription.

    Returns:
      Policy: the policy which was set.
    """
    request = self.messages.PubsubProjectsSubscriptionsSetIamPolicyRequest(
        resource=subscription_ref.RelativeName(),
        setIamPolicyRequest=self.messages.SetIamPolicyRequest(policy=policy),
    )
    return self._service.SetIamPolicy(request)

  def GetIamPolicy(self, subscription_ref):
    """Gets the IAM policy for a Subscription.

    Args:
      subscription_ref (Resource): Resource reference for subscription to get
        the IAM policy of.

    Returns:
      Policy: the policy for the Subscription.
    """
    request = self.messages.PubsubProjectsSubscriptionsGetIamPolicyRequest(
        resource=subscription_ref.RelativeName()
    )
    return self._service.GetIamPolicy(request)

  def AddIamPolicyBinding(self, subscription_ref, member, role):
    """Adds an IAM Policy binding to a Subscription.

    Args:
      subscription_ref (Resource): Resource reference for subscription to add
        IAM policy binding to.
      member (str): The member to add.
      role (str): The role to assign to the member.

    Returns:
      Policy: the updated policy.
    Raises:
      api_exception.HttpException: If either of the requests failed.
    """
    policy = self.GetIamPolicy(subscription_ref)
    iam_util.AddBindingToIamPolicy(self.messages.Binding, policy, member, role)
    return self.SetIamPolicy(subscription_ref, policy)

  def RemoveIamPolicyBinding(self, subscription_ref, member, role):
    """Removes an IAM Policy binding from a Subscription.

    Args:
      subscription_ref (Resource): Resource reference for subscription to remove
        IAM policy binding from.
      member (str): The member to add.
      role (str): The role to assign to the member.

    Returns:
      Policy: the updated policy.
    Raises:
      api_exception.HttpException: If either of the requests failed.
    """
    policy = self.GetIamPolicy(subscription_ref)
    iam_util.RemoveBindingFromIamPolicy(policy, member, role)
    return self.SetIamPolicy(subscription_ref, policy)
