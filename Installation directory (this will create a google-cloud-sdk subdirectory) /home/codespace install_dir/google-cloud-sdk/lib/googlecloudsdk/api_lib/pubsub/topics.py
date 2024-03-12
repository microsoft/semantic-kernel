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
"""Utilities for Cloud Pub/Sub Topics API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import exceptions


class PublishOperationException(exceptions.Error):
  """Error when something went wrong with publish."""


class EmptyMessageException(exceptions.Error):
  """Error when no message was specified for a Publish operation."""


class NoFieldsSpecifiedError(exceptions.Error):
  """Error when no fields were specified for a Patch operation."""


class InvalidSchemaSettingsException(exceptions.Error):
  """Error when the schema settings are invalid."""


class _TopicUpdateSetting(object):
  """Data container class for updating a topic."""

  def __init__(self, field_name, value):
    self.field_name = field_name
    self.value = value


def GetClientInstance(no_http=False):
  return apis.GetClientInstance('pubsub', 'v1', no_http=no_http)


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


def ParseMessageEncoding(messages, message_encoding):
  enc = message_encoding.lower()
  if enc == 'json':
    return messages.SchemaSettings.EncodingValueValuesEnum.JSON
  elif enc == 'binary':
    return messages.SchemaSettings.EncodingValueValuesEnum.BINARY
  else:
    raise InvalidSchemaSettingsException('Unknown message encoding. '
                                         'Options are JSON or BINARY.')


class TopicsClient(object):
  """Client for topics service in the Cloud Pub/Sub API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_topics
    self._subscriptions_service = self.client.projects_subscriptions

  def _ParseIngestionDataSourceSettings(
      self,
      kinesis_ingestion_stream_arn=None,
      kinesis_ingestion_consumer_arn=None,
      kinesis_ingestion_role_arn=None,
      kinesis_ingestion_service_account=None,
  ):
    """Returns an IngestionDataSourceSettings message from the provided args.
    """

    # For each datasource type, check if all required flags are passed, and
    # conditionally construct the source and return the first datasource type
    # which is present. We let the argument parser enforce mutual exclusion of
    # argument groups.

    is_kinesis = (
        (kinesis_ingestion_stream_arn is not None)
        and (kinesis_ingestion_consumer_arn is not None)
        and (kinesis_ingestion_role_arn is not None)
        and (kinesis_ingestion_service_account is not None)
    )

    if is_kinesis:
      kinesis_source = self.messages.AwsKinesis(
          streamArn=kinesis_ingestion_stream_arn,
          consumerArn=kinesis_ingestion_consumer_arn,
          awsRoleArn=kinesis_ingestion_role_arn,
          gcpServiceAccount=kinesis_ingestion_service_account,
      )
      return self.messages.IngestionDataSourceSettings(
          awsKinesis=kinesis_source
      )
    return None

  def Create(
      self,
      topic_ref,
      labels=None,
      kms_key=None,
      message_retention_duration=None,
      message_storage_policy_allowed_regions=None,
      message_storage_policy_enforce_in_transit=False,
      schema=None,
      message_encoding=None,
      first_revision_id=None,
      last_revision_id=None,
      kinesis_ingestion_stream_arn=None,
      kinesis_ingestion_consumer_arn=None,
      kinesis_ingestion_role_arn=None,
      kinesis_ingestion_service_account=None
  ):
    """Creates a Topic.

    Args:
      topic_ref (Resource): Resource reference to the Topic to create.
      labels (LabelsValue): Labels for the topic to create.
      kms_key (str): Full resource name of kms_key to set on Topic or None.
      message_retention_duration (str): How long to retain messages published to
        the Topic.
      message_storage_policy_allowed_regions (list[str]): List of Cloud regions
        in which messages are allowed to be stored at rest.
      message_storage_policy_enforce_in_transit (bool): Whether or not to
        enforce in-transit guarantees for this topic using the allowed regions.
      schema (Resource): Full resource name of schema used to validate messages
        published on Topic.
      message_encoding (str): If a schema is set, the message encoding of
        incoming messages to be validated against the schema.
      first_revision_id (str): If a schema is set, the revision id of the oldest
        revision allowed for validation.
      last_revision_id (str): If a schema is set, the revision id of the newest
        revision allowed for validation.
      kinesis_ingestion_stream_arn (str): The Kinesis data stream ARN to ingest
        data from.
      kinesis_ingestion_consumer_arn (str): The Kinesis data streams consumer
        ARN to use for ingestion.
      kinesis_ingestion_role_arn (str): AWS role ARN to be used for Federated
        Identity authentication with Kinesis.
      kinesis_ingestion_service_account (str): The GCP service account to be
        used for Federated Identity authentication with Kinesis

    Returns:
      Topic: The created topic.

    Raises:
      InvalidSchemaSettingsException: If an invalid --schema,
          --message-encoding flag comnbination is specified,
          or if the --first_revision_id revision is newer than
          the --last_revision_id specified.
    """
    topic = self.messages.Topic(
        name=topic_ref.RelativeName(),
        labels=labels,
        messageRetentionDuration=message_retention_duration)
    if kms_key:
      topic.kmsKeyName = kms_key
    if message_storage_policy_allowed_regions:
      message_storage_policy = self.messages.MessageStoragePolicy(
          allowedPersistenceRegions=message_storage_policy_allowed_regions
      )
      if message_storage_policy_enforce_in_transit:
        message_storage_policy.enforceInTransit = (
            message_storage_policy_enforce_in_transit
        )
      topic.messageStoragePolicy = message_storage_policy
    if schema and message_encoding:
      encoding_enum = ParseMessageEncoding(self.messages, message_encoding)
      topic.schemaSettings = self.messages.SchemaSettings(
          schema=schema,
          encoding=encoding_enum,
          firstRevisionId=first_revision_id,
          lastRevisionId=last_revision_id,
      )
    topic.ingestionDataSourceSettings = self._ParseIngestionDataSourceSettings(
        kinesis_ingestion_stream_arn=kinesis_ingestion_stream_arn,
        kinesis_ingestion_consumer_arn=kinesis_ingestion_consumer_arn,
        kinesis_ingestion_role_arn=kinesis_ingestion_role_arn,
        kinesis_ingestion_service_account=kinesis_ingestion_service_account,
    )
    return self._service.Create(topic)

  def Get(self, topic_ref):
    """Gets a Topic.

    Args:
      topic_ref (Resource): Resource reference to the Topic to get.

    Returns:
      Topic: The topic.
    """
    get_req = self.messages.PubsubProjectsTopicsGetRequest(
        topic=topic_ref.RelativeName())
    return self._service.Get(get_req)

  def Delete(self, topic_ref):
    """Deletes a Topic.

    Args:
      topic_ref (Resource): Resource reference to the Topic to delete.

    Returns:
      Empty: An empty response message.
    """
    delete_req = self.messages.PubsubProjectsTopicsDeleteRequest(
        topic=topic_ref.RelativeName())
    return self._service.Delete(delete_req)

  def DetachSubscription(self, subscription_ref):
    """Detaches the subscription from its topic.

    Args:
      subscription_ref (Resource): Resource reference to the Subscription to
        detach.

    Returns:
      Empty: An empty response message.
    """
    detach_req = self.messages.PubsubProjectsSubscriptionsDetachRequest(
        subscription=subscription_ref.RelativeName())
    return self._subscriptions_service.Detach(detach_req)

  def List(self, project_ref, page_size=100):
    """Lists Topics for a given project.

    Args:
      project_ref (Resource): Resource reference to Project to list Topics from.
      page_size (int): the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      A generator of Topics in the Project.
    """
    list_req = self.messages.PubsubProjectsTopicsListRequest(
        project=project_ref.RelativeName(), pageSize=page_size)
    return list_pager.YieldFromList(
        self._service,
        list_req,
        batch_size=page_size,
        field='topics',
        batch_size_attribute='pageSize')

  def ListSnapshots(self, topic_ref, page_size=100):
    """Lists Snapshots for a given topic.

    Args:
      topic_ref (Resource): Resource reference to Topic to list snapshots from.
      page_size (int): the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      A generator of Snapshots for the Topic.
    """
    list_req = self.messages.PubsubProjectsTopicsSnapshotsListRequest(
        topic=topic_ref.RelativeName(), pageSize=page_size)
    list_snaps_service = self.client.projects_topics_snapshots
    return list_pager.YieldFromList(
        list_snaps_service,
        list_req,
        batch_size=page_size,
        field='snapshots',
        batch_size_attribute='pageSize')

  def ListSubscriptions(self, topic_ref, page_size=100):
    """Lists Subscriptions for a given topic.

    Args:
      topic_ref (Resource): Resource reference to Topic to list subscriptions
        from.
      page_size (int): the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      A generator of Subscriptions for the Topic..
    """
    list_req = self.messages.PubsubProjectsTopicsSubscriptionsListRequest(
        topic=topic_ref.RelativeName(), pageSize=page_size)
    list_subs_service = self.client.projects_topics_subscriptions
    return list_pager.YieldFromList(
        list_subs_service,
        list_req,
        batch_size=page_size,
        field='subscriptions',
        batch_size_attribute='pageSize')

  def Publish(self,
              topic_ref,
              message_body=None,
              attributes=None,
              ordering_key=None):
    """Publishes a message to the given topic.

    Args:
      topic_ref (Resource): Resource reference to Topic to publish to.
      message_body (bytes): Message to send.
      attributes (list[AdditionalProperty]): List of attributes to attach to the
        message.
      ordering_key (string): The ordering key to associate with this message.

    Returns:
      PublishResponse: Response message with message ids from the API.
    Raises:
      EmptyMessageException: If neither message nor attributes is
        specified.
      PublishOperationException: When something went wrong with the publish
        operation.
    """
    if not message_body and not attributes:
      raise EmptyMessageException(
          'You cannot send an empty message. You must specify either a '
          'MESSAGE, one or more ATTRIBUTE, or both.')
    message = self.messages.PubsubMessage(
        data=message_body,
        attributes=self.messages.PubsubMessage.AttributesValue(
            additionalProperties=attributes),
        orderingKey=ordering_key)
    publish_req = self.messages.PubsubProjectsTopicsPublishRequest(
        publishRequest=self.messages.PublishRequest(messages=[message]),
        topic=topic_ref.RelativeName())
    result = self._service.Publish(publish_req)
    if not result.messageIds:
      # If we got a result with empty messageIds, then we've got a problem.
      raise PublishOperationException(
          'Publish operation failed with Unknown error.')
    return result

  def SetIamPolicy(self, topic_ref, policy):
    """Sets an IAM policy on a Topic.

    Args:
      topic_ref (Resource): Resource reference for topic to set IAM policy on.
      policy (Policy): The policy to be added to the Topic.

    Returns:
      Policy: the policy which was set.
    """
    request = self.messages.PubsubProjectsTopicsSetIamPolicyRequest(
        resource=topic_ref.RelativeName(),
        setIamPolicyRequest=self.messages.SetIamPolicyRequest(policy=policy))
    return self._service.SetIamPolicy(request)

  def GetIamPolicy(self, topic_ref):
    """Gets the IAM policy for a Topic.

    Args:
      topic_ref (Resource): Resource reference for topic to get the IAM policy
        of.

    Returns:
      Policy: the policy for the Topic.
    """
    request = self.messages.PubsubProjectsTopicsGetIamPolicyRequest(
        resource=topic_ref.RelativeName())
    return self._service.GetIamPolicy(request)

  def AddIamPolicyBinding(self, topic_ref, member, role):
    """Adds an IAM Policy binding to a Topic.

    Args:
      topic_ref (Resource): Resource reference for subscription to add IAM
        policy binding to.
      member (str): The member to add.
      role (str): The role to assign to the member.

    Returns:
      Policy: the updated policy.
    Raises:
      api_exception.HttpException: If either of the requests failed.
    """
    policy = self.GetIamPolicy(topic_ref)
    iam_util.AddBindingToIamPolicy(self.messages.Binding, policy, member, role)
    return self.SetIamPolicy(topic_ref, policy)

  def RemoveIamPolicyBinding(self, topic_ref, member, role):
    """Removes an IAM Policy binding from a Topic.

    Args:
      topic_ref (Resource): Resource reference for subscription to remove IAM
        policy binding from.
      member (str): The member to remove.
      role (str): The role to remove the member from.

    Returns:
      Policy: the updated policy.
    Raises:
      api_exception.HttpException: If either of the requests failed.
    """
    policy = self.GetIamPolicy(topic_ref)
    iam_util.RemoveBindingFromIamPolicy(policy, member, role)
    return self.SetIamPolicy(topic_ref, policy)

  def Patch(
      self,
      topic_ref,
      labels=None,
      kms_key_name=None,
      message_retention_duration=None,
      clear_message_retention_duration=False,
      recompute_message_storage_policy=False,
      message_storage_policy_allowed_regions=None,
      message_storage_policy_enforce_in_transit=False,
      schema=None,
      message_encoding=None,
      first_revision_id=None,
      last_revision_id=None,
      clear_schema_settings=None,
      clear_ingestion_data_source_settings=False,
      kinesis_ingestion_stream_arn=None,
      kinesis_ingestion_consumer_arn=None,
      kinesis_ingestion_role_arn=None,
      kinesis_ingestion_service_account=None,
  ):
    """Updates a Topic.

    Args:
      topic_ref (Resource): Resource reference for the topic to be updated.
      labels (LabelsValue): The Cloud labels for the topic.
      kms_key_name (str): The full resource name of the Cloud KMS key to
        associate with the topic, or None.
      message_retention_duration (str): How long to retain messages.
      clear_message_retention_duration (bool): If set, remove retention from the
        topic.
      recompute_message_storage_policy (bool): True to have the API recalculate
        the message storage policy.
      message_storage_policy_allowed_regions (list[str]): List of Cloud regions
        in which messages are allowed to be stored at rest.
      message_storage_policy_enforce_in_transit (bool): Whether or not to
        enforce in-transit guarantees for this topic using the allowed regions.
      schema (Resource): Full resource name of schema used to validate messages
        published on Topic.
      message_encoding (str): If a schema is set, the message encoding of
        incoming messages to be validated against the schema.
      first_revision_id (str): If a schema is set, the revision id of the oldest
        revision allowed for validation.
      last_revision_id (str): If a schema is set, the revision id of the newest
        revision allowed for validation.
      clear_schema_settings (bool): If set, clear schema settings from the
        topic.
      clear_ingestion_data_source_settings (bool): If set, clear
        IngestionDataSourceSettings from the topic.
      kinesis_ingestion_stream_arn (str): The Kinesis data stream ARN to
        ingest data from.
      kinesis_ingestion_consumer_arn (str): The Kinesis data streams consumer
        ARN to use for ingestion.
      kinesis_ingestion_role_arn (str): AWS role ARN to be used for Federated
        Identity authentication with Kinesis.
      kinesis_ingestion_service_account (str): The GCP service account to be
        used for Federated Identity authentication with Kinesis

    Returns:
      Topic: The updated topic.
    Raises:
      NoFieldsSpecifiedError: if no fields were specified.
      PatchConflictingArgumentsError: if conflicting arguments were provided
      InvalidSchemaSettingsException: If an invalid --schema,
          --message-encoding flag comnbination is specified,
          or if the --first_revision_id revision is newer than
          the --last_revision_id specified.
    """
    update_settings = []
    if labels:
      update_settings.append(_TopicUpdateSetting('labels', labels))

    if kms_key_name:
      update_settings.append(_TopicUpdateSetting('kmsKeyName', kms_key_name))

    if message_retention_duration:
      update_settings.append(
          _TopicUpdateSetting('messageRetentionDuration',
                              message_retention_duration))
    if clear_message_retention_duration:
      update_settings.append(
          _TopicUpdateSetting('messageRetentionDuration', None))

    if recompute_message_storage_policy:
      update_settings.append(_TopicUpdateSetting('messageStoragePolicy', None))
    elif message_storage_policy_allowed_regions:
      message_storage_policy = self.messages.MessageStoragePolicy(
          allowedPersistenceRegions=message_storage_policy_allowed_regions
      )
      if message_storage_policy_enforce_in_transit:
        message_storage_policy.enforceInTransit = (
            message_storage_policy_enforce_in_transit
        )
      update_settings.append(
          _TopicUpdateSetting('messageStoragePolicy', message_storage_policy)
      )

    if clear_schema_settings:
      update_settings.append(_TopicUpdateSetting('schemaSettings', None))
    elif schema and message_encoding:
      encoding_enum = ParseMessageEncoding(self.messages, message_encoding)
      update_settings.append(
          _TopicUpdateSetting(
              'schemaSettings',
              self.messages.SchemaSettings(
                  schema=schema,
                  encoding=encoding_enum,
                  firstRevisionId=first_revision_id,
                  lastRevisionId=last_revision_id,
              ),
          )
      )

    if clear_ingestion_data_source_settings:
      update_settings.append(
          _TopicUpdateSetting('ingestionDataSourceSettings', None)
      )
    else:
      new_settings = self._ParseIngestionDataSourceSettings(
          kinesis_ingestion_stream_arn=kinesis_ingestion_stream_arn,
          kinesis_ingestion_consumer_arn=kinesis_ingestion_consumer_arn,
          kinesis_ingestion_role_arn=kinesis_ingestion_role_arn,
          kinesis_ingestion_service_account=kinesis_ingestion_service_account,
      )
      if new_settings is not None:
        update_settings.append(
            _TopicUpdateSetting('ingestionDataSourceSettings', new_settings)
        )

    topic = self.messages.Topic(name=topic_ref.RelativeName())

    update_mask = []
    for update_setting in update_settings:
      setattr(topic, update_setting.field_name, update_setting.value)
      update_mask.append(update_setting.field_name)
    if not update_mask:
      raise NoFieldsSpecifiedError('Must specify at least one field to update.')

    patch_req = self.messages.PubsubProjectsTopicsPatchRequest(
        updateTopicRequest=self.messages.UpdateTopicRequest(
            topic=topic, updateMask=','.join(update_mask)),
        name=topic_ref.RelativeName())

    return self._service.Patch(patch_req)
