# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Common utility functions for Cloud Filestore snapshot commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.command_lib.filestore import update_util
from googlecloudsdk.command_lib.filestore import util
from googlecloudsdk.core import properties

PARENT_TEMPLATE = 'projects/{}/locations/{}/instances/{}'
SNAPSHOT_NAME_TEMPLATE = PARENT_TEMPLATE + '/snapshots/{}'
V1_API_VERSION = 'v1'


def FormatSnapshotCreateRequest(ref, args, req):
  """Python hook for yaml commands to supply the snapshot create request with proper values."""
  del ref
  req.snapshotId = args.snapshot
  project = properties.VALUES.core.project.Get(required=True)
  location_id = args.instance_location if args.instance_region is None else (
      args.instance_region)

  req.parent = PARENT_TEMPLATE.format(
      project, location_id, args.instance)

  return req


def FormatSnapshotAccessRequest(ref, args, req):
  """Python hook for yaml commands to supply snapshot access requests with the proper name."""
  del ref
  project = properties.VALUES.core.project.Get(required=True)
  location_id = args.instance_location if args.instance_region is None else (
      args.instance_region)

  req.name = SNAPSHOT_NAME_TEMPLATE.format(
      project, location_id, args.instance, args.snapshot)

  return req


def FormatSnapshotsListRequest(ref, args, req):
  """Python hook for yaml commands to supply the list snapshots request with proper values."""
  del ref
  project = properties.VALUES.core.project.Get(required=True)
  location_id = args.instance_location if args.instance_region is None else (
      args.instance_region)

  req.parent = PARENT_TEMPLATE.format(
      project, location_id, args.instance)

  return req


def UpdateLabels(ref, args, req):
  """Update snapshot labels."""
  del ref
  new_labels = update_util.GetUpdatedLabels(args, req,
                                            update_util.snapshot_feature_name)
  if new_labels:
    req.snapshot.labels = new_labels
  return req


def GetResourceRef(args):
  """Creates a Snapshot and returns its reference."""
  project = properties.VALUES.core.project.Get(required=True)
  api_version = util.GetApiVersionFromArgs(args)
  registry = filestore_client.GetFilestoreRegistry(api_version)
  location_id = args.instance_location if args.instance_region is None else (
      args.instance_region)

  ref = registry.Create(
      'file.projects.locations.instances.snapshots',
      projectsId=project,
      locationsId=location_id,
      instancesId=args.instance,
      snapshotsId=args.snapshot)

  return ref


def GetExistingSnapshot(ref, args, patch_request):
  """Fetch existing Filestore instance to update and add it to Patch request."""
  del ref
  resource_ref = GetResourceRef(args)
  api_version = util.GetApiVersionFromArgs(args)
  client = filestore_client.FilestoreClient(api_version)
  orig_snapshot = client.GetInstanceSnapshot(resource_ref)
  patch_request.snapshot = orig_snapshot
  return patch_request


def FormatSnapshotUpdateResponse(response, args):
  """Python hook to generate the backup update response."""
  del response
  # Return backup describe output.
  resource_ref = GetResourceRef(args)
  api_version = util.GetApiVersionFromArgs(args)
  client = filestore_client.FilestoreClient(api_version)
  return encoding.MessageToDict(client.GetInstanceSnapshot(resource_ref))


def AddDescription(unused_instance_ref, args, patch_request):
  """Adds description to the patch request."""
  return update_util.AddDescription(unused_instance_ref, args, patch_request,
                                    update_util.snapshot_feature_name)
