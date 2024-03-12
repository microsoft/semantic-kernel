# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Common utility functions for Cloud Filestore backup commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.filestore import util
from googlecloudsdk.core import properties

INSTANCE_NAME_TEMPLATE = 'projects/{}/locations/{}/instances/{}'
BACKUP_NAME_TEMPLATE = 'projects/{}/locations/{}/backups/{}'
PARENT_TEMPLATE = 'projects/{}/locations/{}'

V1_API_VERSION = 'v1'
ALPHA_API_VERSION = 'v1p1alpha1'


def FormatBackupCreateRequest(ref, args, req):
  """Python hook for yaml commands to supply the backup create request with proper values."""
  del ref
  req.backupId = args.backup
  project = properties.VALUES.core.project.Get(required=True)
  location = args.region
  req.parent = PARENT_TEMPLATE.format(project, location)
  return req


def FormatBackupAccessRequest(ref, args, req):
  """Python hook for yaml commands to supply backup access requests with the proper name."""
  del ref
  project = properties.VALUES.core.project.Get(required=True)
  location = args.region
  req.name = BACKUP_NAME_TEMPLATE.format(project, location, args.backup)
  return req


def AddInstanceNameToRequest(ref, args, req):
  """Python hook for yaml commands to process the source instance name."""
  del ref
  project = properties.VALUES.core.project.Get(required=True)

  api_version = util.GetApiVersionFromArgs(args)
  if api_version == ALPHA_API_VERSION:
    req.backup.sourceInstance = INSTANCE_NAME_TEMPLATE.format(
        project, args.instance_zone, args.instance)
    return req

  if args.instance_zone is not None:
    req.backup.sourceInstance = INSTANCE_NAME_TEMPLATE.format(
        project, args.instance_zone, args.instance)
  if args.instance_location is not None:
    req.backup.sourceInstance = INSTANCE_NAME_TEMPLATE.format(
        project, args.instance_location, args.instance)
  return req


def AddBackupNameToRequest(ref, args, req):
  """Python hook for yaml commands to process the source backup name."""
  del ref  # Not used to infer location for backups.
  if args.source_backup is None or args.source_backup_region is None:
    return req
  project = properties.VALUES.core.project.Get(required=True)
  req.restoreInstanceRequest.sourceBackup = BACKUP_NAME_TEMPLATE.format(
      project, args.source_backup_region, args.source_backup)
  return req
