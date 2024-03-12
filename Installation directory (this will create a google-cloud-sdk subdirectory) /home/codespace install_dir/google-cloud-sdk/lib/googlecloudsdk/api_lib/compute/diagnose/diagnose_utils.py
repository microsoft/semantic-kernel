# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""API Utilities for gcloud diagnose commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.iam import iam_util


class DiagnoseClient(object):
  """Client for calling apis needed by diagnose commands."""

  def __init__(self, compute_client=None, iam_client=None, storage_client=None):
    """Initializes DiagnoseClient with the common api clients it uses."""
    self._compute_client = (
        compute_client or apis.GetClientInstance('compute', 'v1'))
    self._iam_client = iam_client or apis.GetClientInstance('iam', 'v1')
    self._storage_client = (
        storage_client or apis.GetClientInstance('storage', 'v1'))

  def SignBlob(self, service_account, bytes_to_sign):
    """Signs a string with the private key of the provided service account.

    Args:
      service_account: The string email of a service account that has
        permissions to sign a blob.
      bytes_to_sign: The byte-string to sign.

    Returns:
      A byte-string signature of the provided blob, signed by the provided
      service account.
    """
    messages = self._iam_client.MESSAGES_MODULE

    response = self._iam_client.projects_serviceAccounts.SignBlob(
        messages.IamProjectsServiceAccountsSignBlobRequest(
            name=iam_util.EmailToAccountResourceName(service_account),
            signBlobRequest=messages.SignBlobRequest(
                bytesToSign=bytes_to_sign)))

    return response.signature

  def ListServiceAccounts(self, project):
    """Lists all service accounts within a particular project.

    Args:
      project: The project string to search for the service account in.

    Returns:
      A list of service account message objects.
    """
    messages = self._iam_client.MESSAGES_MODULE

    response = self._iam_client.projects_serviceAccounts.List(
        messages.IamProjectsServiceAccountsListRequest(
            name=iam_util.ProjectToProjectResourceName(project)))

    return response.accounts

  def CreateServiceAccount(self, project, account_id):
    """Creates a service account within the provided project.

    Args:
      project: The project string to create a service account within.
      account_id: The string id to create the service account with.

    Returns:
      A string email of the service account.
    """
    messages = self._iam_client.MESSAGES_MODULE
    response = self._iam_client.projects_serviceAccounts.Create(
        messages.IamProjectsServiceAccountsCreateRequest(
            name=iam_util.ProjectToProjectResourceName(project),
            createServiceAccountRequest=messages.CreateServiceAccountRequest(
                accountId=account_id)))
    return response.email

  def FindBucket(self, project, prefix):
    """Gets the first bucket the project has access to with a matching prefix.

    Args:
      project: The id string of the project the bucket is associated with.
      prefix: The string literal prefix of the bucket being searched for.

    Returns:
      The first bucket message object found matching the prefix, or none.
    """
    messages = self._storage_client.MESSAGES_MODULE
    response = self._storage_client.buckets.List(
        messages.StorageBucketsListRequest(prefix=prefix, project=project))

    for bucket in response.items:
      return bucket

    return None

  def CreateBucketWithLifecycle(self, days_to_live=10):
    """Creates a bucket object that deletes its contents after a number of days.

    Args:
      days_to_live: The number of days to wait before deleting an item within
        this bucket. Count starts when the item is created.

    Returns:
      A bucket message object that has not yet been created in Cloud Storage.
    """
    messages = self._storage_client.MESSAGES_MODULE
    lifecycle = messages.Bucket.LifecycleValue()
    lifecycle_rule = messages.Bucket.LifecycleValue.RuleValueListEntry()
    lifecycle_rule.condition = (
        messages.Bucket.LifecycleValue.RuleValueListEntry.ConditionValue())
    lifecycle_rule.condition.age = days_to_live
    lifecycle_rule.action = (
        messages.Bucket.LifecycleValue.RuleValueListEntry.ActionValue(
            type='Delete'))
    lifecycle.rule.append(lifecycle_rule)
    return messages.Bucket(lifecycle=lifecycle)

  def InsertBucket(self, project_id, bucket):
    """Inserts the bucket object as a GCS bucket associated with the project.

    Args:
      project_id: The project string to save the bucket to.
      bucket: The bucket message object to insert.

    Raises:
      HttpError: with status_code 409 if the bucket already exists.
    """
    messages = self._storage_client.MESSAGES_MODULE
    self._storage_client.buckets.Insert(
        messages.StorageBucketsInsertRequest(bucket=bucket, project=project_id))

  def UpdateMetadata(self, project, instance_ref, key, val):
    """Writes a key value pair to the metadata server.

    Args:
      project: The project string the instance is in.
      instance_ref: The instance the metadata server relates to.
      key: The string key to enter the data in.
      val: The string value to be written at the key.
    """
    messages = self._compute_client.MESSAGES_MODULE
    instance = self._compute_client.instances.Get(
        messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))
    existing_metadata = instance.metadata
    new_metadata = {key: val}
    self._compute_client.instances.SetMetadata(
        messages.ComputeInstancesSetMetadataRequest(
            instance=instance.name,
            metadata=metadata_utils.ConstructMetadataMessage(
                messages,
                metadata=new_metadata,
                existing_metadata=existing_metadata),
            project=project,
            zone=instance_ref.zone))
