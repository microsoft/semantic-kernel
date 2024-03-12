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
"""Common utility functions for Cloud Filestore update snapshot commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.filestore import util
from googlecloudsdk.command_lib.util.args import labels_util


snapshot_feature_name = 'snapshot'
backup_feature_name = 'backup'


def UpdateLabelsFlags():
  remove_group = base.ArgumentGroup(mutex=True)
  remove_group.AddArgument(labels_util.GetClearLabelsFlag())
  remove_group.AddArgument(labels_util.GetRemoveLabelsFlag(''))
  return [labels_util.GetUpdateLabelsFlag(''), remove_group]


def AddFieldToUpdateMask(field, patch_request):
  update_mask = patch_request.updateMask
  if update_mask:
    if update_mask.count(field) == 0:
      patch_request.updateMask = update_mask + ',' + field
  else:
    patch_request.updateMask = field
  return patch_request


def GetUpdatedLabels(args, req, feature_name):
  """Return updated resource labels."""
  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  if labels_diff.MayHaveUpdates():
    req = AddFieldToUpdateMask('labels', req)
    api_version = util.GetApiVersionFromArgs(args)
    messages = filestore_client.GetMessages(api_version)
    if feature_name == snapshot_feature_name:
      return labels_diff.Apply(messages.Snapshot.LabelsValue,
                               req.snapshot.labels).GetOrNone()
    if feature_name == backup_feature_name:
      return labels_diff.Apply(messages.Backup.LabelsValue,
                               req.backup.labels).GetOrNone()
  return None


def AddDescription(unused_instance_ref, args, patch_request, feature_name):
  del unused_instance_ref
  if args.IsSpecified('description'):
    if feature_name == snapshot_feature_name:
      patch_request.snapshot.description = args.description
    if feature_name == backup_feature_name:
      patch_request.backup.description = args.description
    patch_request = AddFieldToUpdateMask('description', patch_request)
  return patch_request
