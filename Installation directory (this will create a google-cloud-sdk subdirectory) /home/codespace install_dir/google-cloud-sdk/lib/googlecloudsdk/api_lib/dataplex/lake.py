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
"""Client for interaction with LAKE API CRUD DATAPLEX."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.command_lib.iam import iam_util


def SetIamPolicy(lake_ref, policy):
  """Set Iam Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesSetIamPolicyRequest(
      resource=lake_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule()
      .GoogleIamV1SetIamPolicyRequest(policy=policy))
  return dataplex_api.GetClientInstance().projects_locations_lakes.SetIamPolicy(
      set_iam_policy_req)


def GetIamPolicy(lake_ref):
  """Get Iam Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesGetIamPolicyRequest(
      resource=lake_ref.RelativeName())
  return dataplex_api.GetClientInstance().projects_locations_lakes.GetIamPolicy(
      get_iam_policy_req)


def AddIamPolicyBinding(lake_ref, member, role):
  """Add iam policy binding request."""
  policy = GetIamPolicy(lake_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role)
  return SetIamPolicy(lake_ref, policy)


def RemoveIamPolicyBinding(lake_ref, member, role):
  """Remove iam policy binding request."""
  policy = GetIamPolicy(lake_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return SetIamPolicy(lake_ref, policy)


def AddServiceAccountToDatasetPolicy(access_message_type, dataset_policy,
                                     member, role):
  """Add service account to dataset."""
  for entry in dataset_policy.access:
    if entry.role == role and member in entry.userByEmail:
      return False
  dataset_policy.access.append(
      access_message_type(userByEmail=member, role='{0}'.format(role)))
  return True


def SetIamPolicyFromFile(lake_ref, policy_file):
  """Set iam policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file,
      dataplex_api.GetMessageModule().GoogleIamV1Policy)
  return SetIamPolicy(lake_ref, policy)


def RemoveServiceAccountFromBucketPolicy(bucket_ref, member, role):
  """Deauthorize Account for Buckets."""
  policy = storage_api.StorageClient().GetIamPolicy(bucket_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return storage_api.StorageClient().SetIamPolicy(bucket_ref, policy)


def RemoveServiceAccountFromDatasetPolicy(dataset_policy, member, role):
  """Deauthorize Account for Dataset."""
  for entry in dataset_policy.access:
    if entry.role == role and member in entry.userByEmail:
      dataset_policy.access.remove(entry)
      return True
  return False


def GenerateUpdateMask(args):
  """Create Update Mask for Lakes."""
  update_mask = []
  if args.IsSpecified('description'):
    update_mask.append('description')
  if args.IsSpecified('display_name'):
    update_mask.append('displayName')
  if args.IsSpecified('labels'):
    update_mask.append('labels')
  if args.IsSpecified('metastore_service'):
    update_mask.append('metastore.service')
  return update_mask


def WaitForOperation(operation):
  """Waits for the given google.longrunning.Operation to complete."""
  return dataplex_api.WaitForOperation(
      operation,
      dataplex_api.GetClientInstance().projects_locations_lakes)


def WaitForLongOperation(operation):
  """Waits for the given google.longrunning.Operation to complete."""
  return dataplex_api.WaitForOperation(
      operation,
      dataplex_api.GetClientInstance().projects_locations_lakes,
      sleep_ms=10000,
      pre_start_sleep_ms=120000)
