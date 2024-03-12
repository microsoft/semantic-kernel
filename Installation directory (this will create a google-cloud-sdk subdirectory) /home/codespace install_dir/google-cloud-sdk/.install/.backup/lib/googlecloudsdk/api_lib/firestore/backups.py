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
"""Useful commands for interacting with the Cloud Firestore Backups API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import api_utils


def _GetBackupService():
  """Returns the service for interacting with the Firestore Backup service."""
  return api_utils.GetClient().projects_locations_backups


def ListBackups(project, location):
  """Lists backups available to Google Cloud Firestore.

  Args:
    project: the project id to list backups, a string.
    location: the location to list backups, a string.

  Returns:
    a List of Backups.
  """
  return list(
      _GetBackupService()
      .List(
          api_utils.GetMessages().FirestoreProjectsLocationsBackupsListRequest(
              parent='projects/{}/locations/{}'.format(project, location)
          )
      )
      .backups
  )


def GetBackup(project, location, backup):
  """Gets backup with the given name.

  Args:
    project: the project id to get backup, a string.
    location: the location to get backup, a string.
    backup: the backup id to get backup, a string.

  Returns:
    A Backup.
  """
  return _GetBackupService().Get(
      api_utils.GetMessages().FirestoreProjectsLocationsBackupsGetRequest(
          name='projects/{}/locations/{}/backups/{}'.format(
              project, location, backup
          )
      )
  )


def DeleteBackup(project, location, backup):
  """Deletes backup with the given name.

  Args:
    project: the project id to get backup, a string.
    location: the location to get backup, a string.
    backup: the backup id to get backup, a string.

  Returns:
    Empty.
  """

  return _GetBackupService().Delete(
      api_utils.GetMessages().FirestoreProjectsLocationsBackupsDeleteRequest(
          name='projects/{}/locations/{}/backups/{}'.format(
              project, location, backup
          )
      )
  )
