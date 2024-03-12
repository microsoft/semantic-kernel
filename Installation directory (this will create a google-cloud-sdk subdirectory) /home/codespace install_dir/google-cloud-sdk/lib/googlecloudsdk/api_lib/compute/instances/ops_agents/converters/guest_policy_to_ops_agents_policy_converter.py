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
"""Converter related function for Ops Agents Policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy as agent_policy
from googlecloudsdk.calliope import exceptions


def _CreateGroupLabels(policy_group_labels):
  group_labels = []
  for policy_group_label in policy_group_labels or []:
    pairs = {
        label.key: label.value
        for label in policy_group_label.labels.additionalProperties
    }
    group_labels.append(pairs)
  return group_labels


def _ExtractDescriptionAndAgentRules(guest_policy_description):
  """Extract Ops Agents policy's description and agent rules.

  Extract Ops Agents policy's description and agent rules from description of
  OS Config guest policy.

  Args:
    guest_policy_description: OS Config guest policy's description.

  Returns:
    extracted description and agent rules for ops agents policy.

  Raises:
    BadArgumentException: If guest policy's description is illformed JSON
    object, or if it does not have keys description or agentRules.
  """

  try:
    decode_description = json.loads(guest_policy_description)
  except ValueError as e:
    raise exceptions.BadArgumentException(
        'description', 'description field is not a JSON object: {}'.format(e))

  if not isinstance(decode_description, dict):
    raise exceptions.BadArgumentException(
        'description', 'description field is not a JSON object.')

  try:
    decoded_description = decode_description['description']
  except KeyError as e:
    raise exceptions.BadArgumentException(
        'description.description', 'missing a required key description: %s' % e)
  try:
    decoded_agent_rules = decode_description['agentRules']
  except KeyError as e:
    raise exceptions.BadArgumentException(
        'description.agentRules', 'missing a required key agentRules: %s' % e)

  return (decoded_description, decoded_agent_rules)


def _CreateAgentRules(agent_rules):
  """Create agent rules in ops agent policy.

  Args:
    agent_rules: json objects.

  Returns:
    agent rules in ops agent policy.
  """
  ops_agent_rules = []

  for agent_rule in agent_rules or []:
    try:
      ops_agent_rules.append(
          agent_policy.OpsAgentPolicy.AgentRule(
              agent_rule['type'], agent_rule['enableAutoupgrade'],
              agent_rule['version'], agent_rule['packageState']))
    except KeyError as e:
      raise exceptions.BadArgumentException(
          'description.agentRules',
          'agent rule specification %s missing a required key: %s' % (
              agent_rule, e))
  return ops_agent_rules


def _CreateAssignment(guest_policy_assignment):
  """Create assignment in ops agent policy from a guest policy assignment.

  Args:
    guest_policy_assignment: type of assignment in guest policy.

  Returns:
    assignment in ops agent policy.
  """
  return agent_policy.OpsAgentPolicy.Assignment(
      group_labels=_CreateGroupLabels(guest_policy_assignment.groupLabels),
      zones=guest_policy_assignment.zones,
      instances=guest_policy_assignment.instances,
      os_types=[
          agent_policy.OpsAgentPolicy.Assignment.OsType(
              t.osShortName, t.osVersion)
          for t in guest_policy_assignment.osTypes or []])


def ConvertGuestPolicyToOpsAgentPolicy(guest_policy):
  """Converts OS Config guest policy to Ops Agent policy."""
  description, agent_rules = _ExtractDescriptionAndAgentRules(
      guest_policy.description)
  return agent_policy.OpsAgentPolicy(
      assignment=_CreateAssignment(guest_policy.assignment),
      agent_rules=_CreateAgentRules(agent_rules),
      description=description,
      etag=guest_policy.etag,
      name=guest_policy.name,
      update_time=guest_policy.updateTime,
      create_time=guest_policy.createTime)
