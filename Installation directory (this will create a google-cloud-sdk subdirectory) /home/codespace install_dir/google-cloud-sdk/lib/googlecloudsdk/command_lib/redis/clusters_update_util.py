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
"""Utility for updating Memorystore Redis clusters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def AddFieldToUpdateMask(field, patch_request):
  update_mask = patch_request.updateMask
  if update_mask:
    if update_mask.count(field) == 0:
      patch_request.updateMask = update_mask + ',' + field
  else:
    patch_request.updateMask = field
  return patch_request


def UpdateReplicaCount(unused_instance_ref, args, patch_request):
  """Hook to add replica count to the redis cluster update request."""
  if args.IsSpecified('replica_count'):
    patch_request.cluster.replicaCount = args.replica_count
    patch_request = AddFieldToUpdateMask('replica_count', patch_request)
  return patch_request


def UpdateShardCount(unused_instance_ref, args, patch_request):
  """Hook to add shard count to the redis cluster update request."""
  if args.IsSpecified('shard_count'):
    patch_request.cluster.shardCount = args.shard_count
    patch_request = AddFieldToUpdateMask('shard_count', patch_request)
  return patch_request


def UpdateDeletionProtection(unused_instance_ref, args, patch_request):
  """Hook to add delete protection to the redis cluster update request."""
  if args.IsSpecified('deletion_protection'):
    patch_request.cluster.deletionProtectionEnabled = args.deletion_protection
    patch_request = AddFieldToUpdateMask(
        'deletion_protection_enabled', patch_request
    )
  return patch_request
