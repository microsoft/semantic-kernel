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
"""Poller for Backup for GKE resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class BackupPoller(object):
  """Backup poller for polling backup until it's terminal."""

  def __init__(self, client, messages):
    self.client = client
    self.messages = messages

  def IsNotDone(self, backup, unused_state):
    del unused_state
    return not (
        backup.state == self.messages.Backup.StateValueValuesEnum.SUCCEEDED or
        backup.state == self.messages.Backup.StateValueValuesEnum.FAILED or
        backup.state == self.messages.Backup.StateValueValuesEnum.DELETING)

  def _GetBackup(self, backup):
    req = self.messages.GkebackupProjectsLocationsBackupPlansBackupsGetRequest()
    req.name = backup
    return self.client.projects_locations_backupPlans_backups.Get(req)

  def Poll(self, backup):
    return self._GetBackup(backup)

  def GetResult(self, backup):
    return self._GetBackup(backup)


class RestorePoller(object):
  """Restore poller for polling restore until it's terminal."""

  def __init__(self, client, messages):
    self.client = client
    self.messages = messages

  def IsNotDone(self, restore, unused_state):
    del unused_state
    return not (
        restore.state == self.messages.Restore.StateValueValuesEnum.SUCCEEDED or
        restore.state == self.messages.Restore.StateValueValuesEnum.FAILED or
        restore.state == self.messages.Restore.StateValueValuesEnum.DELETING)

  def _GetRestore(self, restore):
    req = self.messages.GkebackupProjectsLocationsRestorePlansRestoresGetRequest(
    )
    req.name = restore
    return self.client.projects_locations_restorePlans_restores.Get(req)

  def Poll(self, restore):
    return self._GetRestore(restore)

  def GetResult(self, restore):
    return self._GetRestore(restore)
