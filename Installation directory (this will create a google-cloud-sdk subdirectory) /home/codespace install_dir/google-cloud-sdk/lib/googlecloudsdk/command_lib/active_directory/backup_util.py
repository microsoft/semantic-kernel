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
"""Utility for updating Managed Microsoft AD domain backups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.active_directory import util
from googlecloudsdk.command_lib.util.args import labels_util


def AddFieldToUpdateMask(field, patch_request):
  """Adds name of field to update mask."""
  if patch_request is None:
    return None
  update_mask = patch_request.updateMask
  if update_mask:
    if update_mask.count(field) == 0:
      patch_request.updateMask = update_mask + ',' + field
  else:
    patch_request.updateMask = field
  return patch_request


def UpdateLabels(backup_ref, args, patch_request):
  """Updates labels of domain backups."""
  if patch_request is None:
    return None
  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  if labels_diff.MayHaveUpdates():
    patch_request = AddFieldToUpdateMask('labels', patch_request)
    messages = util.GetMessagesForResource(backup_ref)
    new_labels = labels_diff.Apply(messages.Backup.LabelsValue,
                                   patch_request.backup.labels).GetOrNone()
    if new_labels:
      patch_request.backup.labels = new_labels
  return patch_request


def UpdatePatchRequest(backup_ref, unused_args, patch_request):
  """Fetch existing AD domain backup to update and add it to Patch request."""
  if patch_request is None:
    return None
  patch_request.backup = GetExistingBackup(backup_ref)
  return patch_request


def GetExistingBackup(backup_ref):
  """Fetch existing AD domain backup."""
  client = util.GetClientForResource(backup_ref)
  messages = util.GetMessagesForResource(backup_ref)
  get_req = messages.ManagedidentitiesProjectsLocationsGlobalDomainsBackupsGetRequest(
      name=backup_ref.RelativeName())
  return client.projects_locations_global_domains_backups.Get(get_req)
