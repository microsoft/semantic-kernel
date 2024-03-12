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
"""Common utility functions for Cloud Filestore snapshot commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties

INSTANCE_NAME_TEMPLATE = 'projects/{}/locations/{}/instances/{}'
SNAPSHOT_NAME_TEMPLATE = 'projects/{}/locations/{}/snapshots/{}'
PARENT_TEMPLATE = 'projects/{}/locations/{}'


def FormatSnapshotCreateRequest(ref, args, req):
  """Python hook for yaml commands to supply the snapshot create request with proper values."""
  del ref
  req.snapshotId = args.snapshot
  # If this is a local snapshot, create it in args.instance_zone
  project = properties.VALUES.core.project.Get(required=True)
  location = args.region or args.instance_zone
  req.parent = PARENT_TEMPLATE.format(project, location)
  return req


def FormatSnapshotAccessRequest(ref, args, req):
  """Python hook for yaml commands to supply snapshot access requests with the proper name."""
  del ref
  project = properties.VALUES.core.project.Get(required=True)
  location = args.region or args.zone
  req.name = SNAPSHOT_NAME_TEMPLATE.format(project, location, args.snapshot)
  return req


def AddInstanceNameToRequest(ref, args, req):
  """Python hook for yaml commands to process the source instance name."""
  del ref
  project = properties.VALUES.core.project.Get(required=True)
  req.snapshot.sourceInstance = INSTANCE_NAME_TEMPLATE.format(
      project, args.instance_zone, args.instance)
  return req


def AddSnapshotNameToRequest(ref, args, req):
  """Python hook for yaml commands to process the source snapshot name."""
  location = args.source_snapshot_region or ref.locationsId
  if args.source_snapshot is None or location is None:
    return req
  project = properties.VALUES.core.project.Get(required=True)
  req.restoreInstanceRequest.sourceSnapshot = SNAPSHOT_NAME_TEMPLATE.format(
      project, location, args.source_snapshot)
  return req
