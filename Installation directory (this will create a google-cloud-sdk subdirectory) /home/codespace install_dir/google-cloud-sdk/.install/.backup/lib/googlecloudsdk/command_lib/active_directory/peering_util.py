# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Utility for updating Managed Microsoft AD domain peerings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.active_directory import util
from googlecloudsdk.command_lib.util.args import labels_util


def AddFieldToUpdateMask(field, patch_request):
  """Adds name of field to update mask."""
  update_mask = patch_request.updateMask
  if update_mask:
    if update_mask.count(field) == 0:
      patch_request.updateMask = update_mask + ',' + field
  else:
    patch_request.updateMask = field
  return patch_request


def UpdateLabels(peering_ref, args, patch_request):
  """Updates labels of domain peerings."""
  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  if labels_diff.MayHaveUpdates():
    patch_request = AddFieldToUpdateMask('labels', patch_request)
    messages = util.GetMessagesForResource(peering_ref)
    new_labels = labels_diff.Apply(messages.Peering.LabelsValue,
                                   patch_request.peering.labels).GetOrNone()
    if new_labels:
      patch_request.peering.labels = new_labels
  return patch_request


def UpdatePatchRequest(peering_ref, unused_args, patch_request):
  """Fetch existing AD domain peering to update and add it to Patch request."""
  patch_request.peering = GetExistingPeering(peering_ref)
  return patch_request


def GetExistingPeering(peering_ref):
  """Fetch existing AD domain peering."""
  client = util.GetClientForResource(peering_ref)
  messages = util.GetMessagesForResource(peering_ref)
  get_req = messages.ManagedidentitiesProjectsLocationsGlobalPeeringsGetRequest(
      name=peering_ref.RelativeName())
  return client.projects_locations_global_peerings.Get(get_req)
