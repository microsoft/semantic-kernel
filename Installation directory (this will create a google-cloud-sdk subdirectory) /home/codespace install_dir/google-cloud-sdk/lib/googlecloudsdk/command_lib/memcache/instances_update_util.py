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
"""Utilities for `gcloud memcache instances update` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib import memcache


def ChooseUpdateMethod(unused_ref, args):
  if args.IsSpecified('parameters'):
    return 'updateParameters'
  return 'patch'


def AddFieldToUpdateMask(update_mask, field):
  if field not in update_mask:
    update_mask.append(field)


def ModifyMaintenanceMask(unused_ref, args, req):
  """Update patch mask for maintenancePolicy.

  Args:
    unused_ref: The field resource reference.
    args: The parsed arg namespace.
    req: The auto-generated patch request.
  Returns:
    FirestoreProjectsDatabasesCollectionGroupsFieldsPatchRequest
  """
  policy_is_updated = (
      hasattr(req, 'instance') and
      hasattr(req.instance, 'maintenancePolicy') and
      req.instance.maintenancePolicy)

  # By default the update mask has the full path that was update
  # ie maintenancePolicy.weeklyMaintenanceWindow.day
  if args.IsSpecified('maintenance_window_any') or policy_is_updated:
    policy = 'maintenancePolicy'
    mask = list(filter(
        lambda m: m and policy not in m, req.updateMask.split(',')))
    AddFieldToUpdateMask(mask, policy)
    req.updateMask = ','.join(mask)

  return req


# TODO(b/261326299): This hook is needed because the modify_method_hook does not
# determine the message until runtime. Update yaml translator to be able to map
# args to api fields when there is a dynamic method
def ModifyParams(ref, args, req):
  """Update patch request to include parameters.

  Args:
    ref: The field resource reference.
    args: The parsed arg namespace.
    req: The auto-generated patch request.
  Returns:
    FirestoreProjectsDatabasesCollectionGroupsFieldsPatchRequest
  """
  if args.IsSpecified('parameters'):
    messages = memcache.Messages(ref.GetCollectionInfo().api_version)
    params = encoding.DictToMessage(args.parameters,
                                    messages.MemcacheParameters.ParamsValue)
    parameters = messages.MemcacheParameters(params=params)
    param_req = messages.UpdateParametersRequest(
        updateMask='params', parameters=parameters)
    req.updateParametersRequest = param_req

  return req


def _GetMaintenancePolicy(message_module):
  """Returns a maintenance policy of the appropriate version."""
  if hasattr(message_module, 'GoogleCloudMemcacheV1beta2MaintenancePolicy'):
    return message_module.GoogleCloudMemcacheV1beta2MaintenancePolicy()
  elif hasattr(message_module, 'GoogleCloudMemcacheV1MaintenancePolicy'):
    return message_module.GoogleCloudMemcacheV1MaintenancePolicy()

  raise AttributeError('No MaintenancePolicy found for version V1 or V1beta2.')
