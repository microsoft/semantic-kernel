# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Utilities for Backup for GKE commands to call Backup for GKE APIs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.backup_restore.poller import BackupPoller
from googlecloudsdk.api_lib.container.backup_restore.poller import RestorePoller
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import retry

VERSION_MAP = {base.ReleaseTrack.ALPHA: 'v1'}


class WaitForCompletionTimeoutError(exceptions.Error):
  """The command in wait-for-completion mode timed out."""


def GetMessagesModule(release_track=base.ReleaseTrack.ALPHA):
  return apis.GetMessagesModule('gkebackup', VERSION_MAP.get(release_track))


def GetClientClass(release_track=base.ReleaseTrack.ALPHA):
  return apis.GetClientClass('gkebackup', VERSION_MAP.get(release_track))


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA):
  return apis.GetClientInstance('gkebackup', VERSION_MAP.get(release_track))


def CreateBackup(backup_ref,
                 description=None,
                 labels=None,
                 retain_days=None,
                 delete_lock_days=None,
                 client=None):
  """Creates a backup resource by calling Backup for GKE service and returns a LRO."""
  if client is None:
    client = GetClientInstance()
  message = GetMessagesModule()
  req = message.GkebackupProjectsLocationsBackupPlansBackupsCreateRequest()
  req.backupId = backup_ref.Name()
  req.parent = backup_ref.Parent().RelativeName()
  req.backup = message.Backup()
  if description:
    req.backup.description = description
  if retain_days:
    req.backup.retainDays = retain_days
  if delete_lock_days:
    req.backup.deleteLockDays = delete_lock_days
  if labels:
    req.backup.labels = labels
  return client.projects_locations_backupPlans_backups.Create(req)


def CreateBackupAndWaitForLRO(backup_ref,
                              description=None,
                              labels=None,
                              retain_days=None,
                              delete_lock_days=None,
                              client=None):
  """Creates a backup resource and wait for the resulting LRO to complete."""
  if client is None:
    client = GetClientInstance()
  operation = CreateBackup(
      backup_ref,
      description=description,
      labels=labels,
      retain_days=retain_days,
      delete_lock_days=delete_lock_days,
      client=client)
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name, 'gkebackup.projects.locations.operations')

  log.CreatedResource(
      operation_ref.RelativeName(),
      kind='backup {0}'.format(backup_ref.Name()),
      is_async=True)

  poller = waiter.CloudOperationPollerNoResources(
      client.projects_locations_operations)
  return waiter.WaitFor(poller, operation_ref,
                        'Creating backup {0}'.format(backup_ref.Name()))


def _BackupStatusUpdate(result, unused_state):
  del unused_state
  log.Print('Waiting for backup to complete... Backup state: {0}.'.format(
      result.state))


def WaitForBackupToFinish(backup,
                          max_wait_ms=1800000,
                          exponential_sleep_multiplier=1.4,
                          jitter_ms=1000,
                          wait_ceiling_ms=180000,
                          status_update=_BackupStatusUpdate,
                          sleep_ms=2000,
                          client=None):
  """Waits for backup resource to be terminal state."""
  if client is None:
    client = GetClientInstance()
  messages = GetMessagesModule()
  retryer = retry.Retryer(
      max_retrials=None,
      max_wait_ms=max_wait_ms,
      exponential_sleep_multiplier=exponential_sleep_multiplier,
      jitter_ms=jitter_ms,
      wait_ceiling_ms=wait_ceiling_ms,
      status_update_func=status_update)
  backup_poller = BackupPoller(client, messages)
  try:
    result = retryer.RetryOnResult(
        func=backup_poller.Poll,
        args=(backup,),
        should_retry_if=backup_poller.IsNotDone,
        sleep_ms=sleep_ms)
    log.Print('Backup completed. Backup state: {0}'.format(result.state))
    return result
  # No need to catch MaxRetrialsException since we retry unlimitedly.
  except retry.WaitException:
    raise WaitForCompletionTimeoutError(
        'Timeout waiting for backup to complete. Backup is not completed, use "gcloud container backup-restore backups describe" command to check backup status.'
    )


def CreateRestore(restore_ref,
                  backup,
                  description=None,
                  labels=None,
                  client=None):
  """Creates a restore resource by calling Backup for GKE service and returns a LRO."""
  if client is None:
    client = GetClientInstance()
  messages = GetMessagesModule()
  req = messages.GkebackupProjectsLocationsRestorePlansRestoresCreateRequest()
  req.restoreId = restore_ref.Name()
  req.parent = restore_ref.Parent().RelativeName()
  req.restore = messages.Restore()
  req.restore.backup = backup
  if description:
    req.restore.description = description
  if labels:
    req.restore.labels = labels
  return client.projects_locations_restorePlans_restores.Create(req)


def CreateRestoreAndWaitForLRO(restore_ref,
                               backup,
                               description=None,
                               labels=None,
                               client=None):
  """Creates a restore resource by calling Backup for GKE service."""
  if client is None:
    client = GetClientInstance()
  operation = CreateRestore(
      restore_ref,
      backup=backup,
      description=description,
      labels=labels,
      client=client)
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name, 'gkebackup.projects.locations.operations')

  log.CreatedResource(
      operation_ref.RelativeName(),
      kind='restore {0}'.format(restore_ref.Name()),
      is_async=True)

  poller = waiter.CloudOperationPollerNoResources(
      client.projects_locations_operations)
  return waiter.WaitFor(poller, operation_ref,
                        'Creating restore {0}'.format(restore_ref.Name()))


def _RestoreStatusUpdate(result, unused_state):
  del unused_state
  log.Print('Waiting for restore to complete... Restore state: {0}.'.format(
      result.state))


def WaitForRestoreToFinish(restore,
                           max_wait_ms=1800000,
                           exponential_sleep_multiplier=1.4,
                           jitter_ms=1000,
                           wait_ceiling_ms=180000,
                           status_update=_RestoreStatusUpdate,
                           sleep_ms=2000,
                           client=None):
  """Waits for restore resource to be terminal state."""
  if not client:
    client = GetClientInstance()
  messages = GetMessagesModule()
  retryer = retry.Retryer(
      max_retrials=None,
      max_wait_ms=max_wait_ms,
      exponential_sleep_multiplier=exponential_sleep_multiplier,
      jitter_ms=jitter_ms,
      wait_ceiling_ms=wait_ceiling_ms,
      status_update_func=status_update)
  restore_poller = RestorePoller(client, messages)
  try:
    result = retryer.RetryOnResult(
        func=restore_poller.Poll,
        args=(restore,),
        should_retry_if=restore_poller.IsNotDone,
        sleep_ms=sleep_ms)
    log.Print('Restore completed. Restore state: {0}'.format(result.state))
    return result
  # No need to catch MaxRetrialsException since we retry unlimitedly.
  except retry.WaitException:
    raise WaitForCompletionTimeoutError(
        'Timeout waiting for restore to complete. Restore is not completed, use "gcloud container backup-restore restores describe" command to check restore status.'
    )
