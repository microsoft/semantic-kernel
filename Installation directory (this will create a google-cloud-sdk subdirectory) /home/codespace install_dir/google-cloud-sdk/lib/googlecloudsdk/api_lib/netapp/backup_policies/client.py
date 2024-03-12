# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Commands for interacting with the Cloud NetApp Files Backup Policy API resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.netapp import constants
from googlecloudsdk.api_lib.netapp import util as netapp_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class BackupPoliciesClient(object):
  """Wrapper for working with Backup Policies in the Cloud NetApp Files API Client."""

  def __init__(self, release_track=base.ReleaseTrack.BETA):
    if release_track == base.ReleaseTrack.BETA:
      self._adapter = BetaBackupPoliciesAdapter()
    else:
      raise ValueError('[{}] is not a valid API version.'.format(
          netapp_util.VERSION_MAP[release_track]))

  @property
  def client(self):
    return self._adapter.client

  @property
  def messages(self):
    return self._adapter.messages

  def WaitForOperation(self, operation_ref):
    """Waits on the long-running operation until the done field is True.

    Args:
      operation_ref: the operation reference.

    Raises:
      waiter.OperationError: if the operation contains an error.

    Returns:
      the 'response' field of the Operation.
    """
    return waiter.WaitFor(
        waiter.CloudOperationPollerNoResources(
            self.client.projects_locations_operations
        ),
        operation_ref,
        'Waiting for [{0}] to finish'.format(operation_ref.Name()),
    )

  def CreateBackupPolicy(self, backuppolicy_ref, async_, backup_policy):
    """Create a Cloud NetApp Backup Policy."""
    request = self.messages.NetappProjectsLocationsBackupPoliciesCreateRequest(
        parent=backuppolicy_ref.Parent().RelativeName(),
        backupPolicyId=backuppolicy_ref.Name(),
        backupPolicy=backup_policy,
    )
    create_op = self.client.projects_locations_backupPolicies.Create(request)
    if async_:
      return create_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        create_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def ParseBackupPolicy(
      self,
      name=None,
      enabled=None,
      daily_backup_limit=None,
      weekly_backup_limit=None,
      monthly_backup_limit=None,
      description=None,
      labels=None
  ):
    """Parses the command line arguments for Create Backup Policy into a message.

    Args:
      name: the name of the Backup Policy
      enabled: the Boolean value indicating whether or not backups are made
        automatically according to schedule.
      daily_backup_limit: the number of daily backups to keep.
      weekly_backup_limit: the number of weekly backups to keep.
      monthly_backup_limit: the number of monthly backups to keep.
      description: the description of the Backup Policy.
      labels: the parsed labels value

    Returns:
      The configuration that will be used as the request body for creating a
      Cloud NetApp Backup Policy.
    """
    backup_policy = self.messages.BackupPolicy()
    backup_policy.name = name
    backup_policy.enabled = enabled
    backup_policy.dailyBackupLimit = daily_backup_limit
    backup_policy.weeklyBackupLimit = weekly_backup_limit
    backup_policy.monthlyBackupLimit = monthly_backup_limit
    backup_policy.description = description
    backup_policy.labels = labels
    return backup_policy

  def ListBackupPolicies(self, location_ref, limit=None):
    """Make API calls to List Cloud NetApp Backup Policies.

    Args:
      location_ref: The parsed location of the listed NetApp Backup Policies.
      limit: The number of Cloud NetApp Backup Policies
        to limit the results to. This limit is passed to
        the server and the server does the limiting.

    Returns:
      Generator that yields the Cloud NetApp Backup Policies.
    """
    request = self.messages.NetappProjectsLocationsBackupPoliciesListRequest(
        parent=location_ref)
    # Check for unreachable locations.
    response = self.client.projects_locations_backupPolicies.List(request)
    for location in response.unreachable:
      log.warning('Location {} may be unreachable.'.format(location))
    return list_pager.YieldFromList(
        self.client.projects_locations_backupPolicies,
        request,
        field=constants.BACKUP_POLICY_RESOURCE,
        limit=limit,
        batch_size_attribute='pageSize')

  def GetBackupPolicy(self, backuppolicy_ref):
    """Get Cloud NetApp Backup Policy information."""
    request = self.messages.NetappProjectsLocationsBackupPoliciesGetRequest(
        name=backuppolicy_ref.RelativeName())
    return self.client.projects_locations_backupPolicies.Get(request)

  def DeleteBackupPolicy(self, backuppolicy_ref, async_):
    """Deletes an existing Cloud NetApp Backup Policy."""
    request = (
        self.messages.NetappProjectsLocationsBackupPoliciesDeleteRequest(
            name=backuppolicy_ref.RelativeName()
        )
    )
    return self._DeleteBackupPolicy(async_, request)

  def _DeleteBackupPolicy(self, async_, request):
    delete_op = self.client.projects_locations_backupPolicies.Delete(request)
    if async_:
      return delete_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        delete_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def UpdateBackupPolicy(
      self, backuppolicy_ref, backup_policy, update_mask, async_
  ):
    """Updates a Backup Policy.

    Args:
      backuppolicy_ref: the reference to the Backup Policy.
      backup_policy: Backup Policy message, the updated Backup Policy.
      update_mask: str, a comma-separated list of updated fields.
      async_: bool, if False, wait for the operation to complete.
    Returns:
      an Operation or Backup Policy message.
    """
    update_op = self._adapter.UpdateBackupPolicy(
        backuppolicy_ref, backup_policy, update_mask
    )
    if async_:
      return update_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        update_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def ParseUpdatedBackupPolicy(
      self,
      backup_policy,
      enabled=None,
      daily_backup_limit=None,
      weekly_backup_limit=None,
      monthly_backup_limit=None,
      description=None,
      labels=None,
  ):
    """Parses updates into an Backup Policy."""
    return self._adapter.ParseUpdatedBackupPolicy(
        backup_policy=backup_policy,
        enabled=enabled,
        daily_backup_limit=daily_backup_limit,
        weekly_backup_limit=weekly_backup_limit,
        monthly_backup_limit=monthly_backup_limit,
        description=description,
        labels=labels,
    )


class BetaBackupPoliciesAdapter(object):
  """Adapter for the Beta Cloud NetApp Files API for Backup Policies."""

  def __init__(self):
    self.release_track = base.ReleaseTrack.BETA
    self.client = netapp_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_util.GetMessagesModule(
        release_track=self.release_track
    )

  def ParseUpdatedBackupPolicy(
      self, backup_policy, daily_backup_limit=None, weekly_backup_limit=None,
      monthly_backup_limit=None, enabled=None, description=None, labels=None
  ):
    """Parses updates into a new Backup Policy."""
    if enabled is not None:
      backup_policy.enabled = enabled
    if daily_backup_limit is not None:
      backup_policy.dailyBackupLimit = daily_backup_limit
    if weekly_backup_limit is not None:
      backup_policy.weeklyBackupLimit = weekly_backup_limit
    if monthly_backup_limit is not None:
      backup_policy.monthlyBackupLimit = monthly_backup_limit
    if description is not None:
      backup_policy.description = description
    if labels is not None:
      backup_policy.labels = labels
    return backup_policy

  def UpdateBackupPolicy(self, backuppolicy_ref, backup_policy, update_mask):
    """Send a Patch request for the Cloud NetApp Backup Policy."""
    update_request = (
        self.messages.NetappProjectsLocationsBackupPoliciesPatchRequest(
            backupPolicy=backup_policy,
            name=backuppolicy_ref.RelativeName(),
            updateMask=update_mask))
    update_op = self.client.projects_locations_backupPolicies.Patch(
        update_request)
    return update_op

