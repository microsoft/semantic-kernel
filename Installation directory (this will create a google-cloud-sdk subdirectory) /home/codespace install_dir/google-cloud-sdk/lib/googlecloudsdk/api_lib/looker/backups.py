# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Useful commands for interacting with the Looker Backups API."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import log

# API version constants
API_VERSION_DEFAULT = 'v1alpha1'


def GetClient():
  """Returns the Looker client for backups."""
  return apis.GetClientInstance('looker', API_VERSION_DEFAULT)


def GetService():
  """Returns the service for interacting with the Backups service."""
  return GetClient().projects_locations_instances_backups


def GetMessages():
  """Import and return the appropriate operations messages module."""
  return apis.GetMessagesModule('looker', API_VERSION_DEFAULT)


def CreateBackup(parent):
  """Creates the Backup with the given parent.

  Args:
    parent: the instance where the backup will be created, a string.

  Returns:
    a long running Operation
  """
  log.status.Print(
      'Creating backup for instance {parent}'.format(parent=parent))
  return GetService().Create(
      GetMessages().LookerProjectsLocationsInstancesBackupsCreateRequest(
          parent=parent))
