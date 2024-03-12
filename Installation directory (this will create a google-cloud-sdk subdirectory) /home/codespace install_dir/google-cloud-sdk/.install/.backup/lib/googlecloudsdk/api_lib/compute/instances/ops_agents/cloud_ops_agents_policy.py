# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""This class will store in-memory instance of ops agents policy."""

import dataclasses
import enum
import json
import sys
from typing import Any, Mapping
from apitools.base.py import encoding
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.generated_clients.apis.osconfig.v1 import osconfig_v1_messages


_StrEnum = (
    (enum.StrEnum,) if sys.version_info[:2] >= (3, 11) else (str, enum.Enum)
)

_OPS_AGENTS_POLICY_KEYS = frozenset({'agents_rule', 'instance_filter'})


@dataclasses.dataclass(repr=False)
class OpsAgentsPolicy(object):
  """An Ops Agent policy encapsulates the underlying VMM Policy.

  Attr:
    agents_rule: the agents rule to be applied to VMs.
    instance_filter:
      [InstanceFilter](https://cloud.google.com/compute/docs/osconfig/rest/v1/projects.locations.osPolicyAssignments#InstanceFilter)
      Filters to select target VMs for an assignment. Only Ops Agent supported
      [osShortName](https://cloud.google.com/compute/docs/osconfig/rest/v1/projects.locations.osPolicyAssignments#inventory)
      values are allowed.
  """

  @dataclasses.dataclass(repr=False)
  class AgentsRule(object):
    """An Ops agents rule contains package state, and version.

    Attr:
      version: agent version, e.g. 'latest', '2.52.1'.
      package_state: desired state for the package.
    """

    class PackageState(*_StrEnum):
      INSTALLED = 'installed'
      REMOVED = 'removed'

    version: str = 'latest'
    package_state: PackageState = PackageState.INSTALLED

    def __repr__(self) -> str:
      """Generate JSON with camel-cased keys."""

      key_camel_cased_dict = {
          resource_property.ConvertToCamelCase(key): value
          for key, value in self.__dict__.items()
      }
      return json.dumps(key_camel_cased_dict, default=str, sort_keys=True)

  agents_rule: AgentsRule
  instance_filter: osconfig_v1_messages.OSPolicyAssignmentInstanceFilter

  def __repr__(self) -> str:
    """JSON format string representation for testing."""

    policy_map = {
        'agents_rule': self.agents_rule,
        'instance_filter': encoding.MessageToPyValue(self.instance_filter),
    }

    return json.dumps(
        policy_map,
        default=lambda o: o.__dict__,
        indent=2,
        separators=(',', ': '),
        sort_keys=True,
    )


def CreateAgentsRule(
    agents_rule: Mapping[str, str]
) -> OpsAgentsPolicy.AgentsRule:
  """Create agents rule in ops agents policy.

  Args:
    agents_rule: fields (version, package_state) describing agents rule from the
      command line.

  Returns:
    An OpsAgentPolicy.AgentsRule object.
  """
  if not agents_rule or agents_rule.keys() != {'version', 'package_state'}:
    raise ValueError('agents_rule must contain version and package_state')

  return OpsAgentsPolicy.AgentsRule(
      version=agents_rule['version'],
      package_state=OpsAgentsPolicy.AgentsRule.PackageState(
          agents_rule['package_state']
      ),
  )


def CreateOpsAgentsPolicy(
    ops_agents_policy: Mapping[str, Any],
) -> OpsAgentsPolicy:
  """Create Ops Agent Policy.

  Args:
    ops_agents_policy: fields (agents_rule, instance_filter) describing ops
      agents policy from the command line.

  Returns:
    Ops agents policy.
  """

  if (
      not ops_agents_policy
      or ops_agents_policy.keys() != _OPS_AGENTS_POLICY_KEYS
  ):
    raise ValueError(
        'ops_agents_policy must contain agents_rule and instance_filter'
    )

  return OpsAgentsPolicy(
      agents_rule=CreateAgentsRule(ops_agents_policy['agents_rule']),
      instance_filter=encoding.PyValueToMessage(
          osconfig_v1_messages.OSPolicyAssignmentInstanceFilter,
          ops_agents_policy['instance_filter'],
      ),
  )


def UpdateOpsAgentsPolicy(
    update_ops_agents_policy: Mapping[str, Any],
    ops_agents_policy: OpsAgentsPolicy,
) -> OpsAgentsPolicy:
  """Merge existing ops agents policy with user updates.

  Unless explicitly mentioned, a None value means "leave unchanged".

  Args:
    update_ops_agents_policy: fields describing a subset of an ops agents policy
      that will overwrite the existing policy.
    ops_agents_policy: fields describing ops agents policy from the command
      line.

  Returns:
    Updated ops agents policy.
  """
  if update_ops_agents_policy is None:
    raise ValueError('update_ops_agents_policy cannot be None')

  unknown_keys = set(update_ops_agents_policy) - _OPS_AGENTS_POLICY_KEYS
  if unknown_keys:
    raise ValueError(
        f'unknown OpsAgentsPolicy fields: {unknown_keys} in'
        ' update_ops_agents_policy'
    )

  agents_rule = update_ops_agents_policy.get('agents_rule')
  instance_filter = update_ops_agents_policy.get('instance_filter')

  if agents_rule is not None:
    updated_agents_rule = CreateAgentsRule(agents_rule)
  else:
    updated_agents_rule = ops_agents_policy.agents_rule

  if instance_filter is not None:
    updated_instance_filter = encoding.PyValueToMessage(
        osconfig_v1_messages.OSPolicyAssignmentInstanceFilter,
        instance_filter,
    )
  else:
    updated_instance_filter = ops_agents_policy.instance_filter

  return OpsAgentsPolicy(
      instance_filter=updated_instance_filter,
      agents_rule=updated_agents_rule,
  )
