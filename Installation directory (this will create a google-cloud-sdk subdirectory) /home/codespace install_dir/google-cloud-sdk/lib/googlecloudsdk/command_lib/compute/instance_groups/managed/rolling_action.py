# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Create requests for rolling-action restart/recreate commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.managed_instance_groups import update_instances_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import times
import six


def CreateRequest(args,
                  client,
                  resources,
                  minimal_action,
                  max_surge=None):
  """Create request helper for compute instance-groups managed rolling-action.

  Args:
    args: argparse namespace
    client: The compute client
    resources: The compute resources
    minimal_action: MinimalActionValueValuesEnum value
    max_surge: InstanceGroupManagerUpdatePolicy.maxSurge value

  Returns:
    ComputeInstanceGroupManagersPatchRequest or
    ComputeRegionInstanceGroupManagersPatchRequest instance

  Raises:
    ValueError: if instance group manager collection path is unknown
  """
  resource_arg = instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
  default_scope = compute_scope.ScopeEnum.ZONE
  scope_lister = flags.GetDefaultScopeLister(client)
  igm_ref = resource_arg.ResolveAsResource(
      args, resources, default_scope=default_scope, scope_lister=scope_lister)

  if igm_ref.Collection() not in [
      'compute.instanceGroupManagers', 'compute.regionInstanceGroupManagers'
  ]:
    raise ValueError('Unknown reference type {0}'.format(igm_ref.Collection()))

  update_policy_type = (client.messages.InstanceGroupManagerUpdatePolicy.
                        TypeValueValuesEnum.PROACTIVE)
  max_unavailable = update_instances_utils.ParseFixedOrPercent(
      '--max-unavailable', 'max-unavailable', args.max_unavailable,
      client.messages)

  igm_info = managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
      igm_ref, client)

  versions = (igm_info.versions or [
      client.messages.InstanceGroupManagerVersion(
          instanceTemplate=igm_info.instanceTemplate)
  ])
  current_time_str = six.text_type(times.Now(times.UTC))
  for i, version in enumerate(versions):
    version.name = '%d/%s' % (i, current_time_str)

  update_policy = client.messages.InstanceGroupManagerUpdatePolicy(
      maxSurge=max_surge,
      maxUnavailable=max_unavailable,
      minimalAction=minimal_action,
      type=update_policy_type)
  # min_ready is available in alpha and beta APIs only
  if hasattr(args, 'min_ready'):
    update_policy.minReadySec = args.min_ready
  # replacement_method is available in alpha API only
  if hasattr(args, 'replacement_method'):
    replacement_method = update_instances_utils.ParseReplacementMethod(
        args.replacement_method, client.messages)
    update_policy.replacementMethod = replacement_method

  ValidateAndFixUpdaterAgainstStateful(update_policy, igm_info, client, args)

  igm_resource = client.messages.InstanceGroupManager(
      instanceTemplate=None, updatePolicy=update_policy, versions=versions)
  if igm_ref.Collection() == 'compute.instanceGroupManagers':
    service = client.apitools_client.instanceGroupManagers
    request = client.messages.ComputeInstanceGroupManagersPatchRequest(
        instanceGroupManager=igm_ref.Name(),
        instanceGroupManagerResource=igm_resource,
        project=igm_ref.project,
        zone=igm_ref.zone)
  else:
    service = client.apitools_client.regionInstanceGroupManagers
    request = client.messages.ComputeRegionInstanceGroupManagersPatchRequest(
        instanceGroupManager=igm_ref.Name(),
        instanceGroupManagerResource=igm_resource,
        project=igm_ref.project,
        region=igm_ref.region)
  return (service, 'Patch', request)


def ValidateAndFixUpdaterAgainstStateful(update_policy, igm_info, client, args):
  """Validates and fixes update policy for patching stateful IGM.

  Updating stateful IGMs requires maxSurge=0 and replacementMethod=RECREATE.
  If the field has the value set, it is validated.
  If the field has the value not set, it is being set.

  Args:
    update_policy: Update policy to be validated
    igm_info: Full resource of IGM being validated
    client: The compute API client
    args: argparse namespace used to select used version
  """
  if not managed_instance_groups_utils.IsStateful(igm_info):
    return
  if hasattr(args, 'replacement_method'):
    recreate = (
        client.messages.InstanceGroupManagerUpdatePolicy
        .ReplacementMethodValueValuesEnum.RECREATE)
    if update_policy.replacementMethod is None:
      update_policy.replacementMethod = recreate
    elif update_policy.replacementMethod != recreate:
      raise exceptions.Error(
          'For performing this action on a stateful IGMs '
          '--replacement-method has to be RECREATE')
  if update_policy.maxSurge is None:
    update_policy.maxSurge = client.messages.FixedOrPercent(fixed=0)
  else:
    max_surge_is_zero = True
    if update_policy.maxSurge.fixed is not None:
      if update_policy.maxSurge.fixed != 0:
        max_surge_is_zero = False
    if update_policy.maxSurge.percent is not None:
      if update_policy.maxSurge.percent != 0:
        max_surge_is_zero = False
    if not max_surge_is_zero:
      raise exceptions.Error(
          'For performing this action on a stateful IGMs '
          '--max-surge has to be 0')
