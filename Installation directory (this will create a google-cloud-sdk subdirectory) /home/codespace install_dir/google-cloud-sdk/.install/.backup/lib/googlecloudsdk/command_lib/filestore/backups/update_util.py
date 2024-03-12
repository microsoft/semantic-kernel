# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Common utility functions for Cloud Filestore update backup commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.command_lib.filestore import update_util
from googlecloudsdk.command_lib.filestore import util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def UpdateLabels(unused_ref, args, req):
  """Update backup labels."""
  new_labels = update_util.GetUpdatedLabels(args, req,
                                            update_util.backup_feature_name)
  if new_labels:
    req.backup.labels = new_labels
  return req


def AddDescription(unused_instance_ref, args, patch_request):
  return update_util.AddDescription(unused_instance_ref, args, patch_request,
                                    update_util.backup_feature_name)


def GetResourceRef(args):
  project = properties.VALUES.core.project.Get(required=True)
  location = args.region
  ref = resources.REGISTRY.Create(
      'file.projects.locations.backups',
      projectsId=project,
      locationsId=location,
      backupsId=args.backup)
  return ref


def GetExistingBackup(unused_resource_ref, args, patch_request):
  """Fetch existing Filestore instance to update and add it to Patch request."""
  resource_ref = GetResourceRef(args)
  api_version = util.GetApiVersionFromArgs(args)
  client = filestore_client.FilestoreClient(api_version)
  orig_backup = client.GetBackup(resource_ref)
  patch_request.backup = orig_backup
  return patch_request


def FormatBackupUpdateResponse(response, args):
  """Python hook to generate the backup update response."""
  del response
  # Return backup describe output.
  resource_ref = GetResourceRef(args)
  api_version = util.GetApiVersionFromArgs(args)
  client = filestore_client.FilestoreClient(api_version)
  return encoding.MessageToDict(client.GetBackup(resource_ref))
