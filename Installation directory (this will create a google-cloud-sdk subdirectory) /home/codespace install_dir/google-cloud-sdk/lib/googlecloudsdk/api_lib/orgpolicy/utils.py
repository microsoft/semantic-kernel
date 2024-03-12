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
"""Utilities for manipulating organization policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.org_policies import exceptions


def GetConstraintFromPolicyName(policy_name):
  """Returns the constraint from the specified policy name.

  A constraint has the following syntax: constraints/{constraint_name}.

  Args:
    policy_name: The name of the policy. A policy name has the following syntax:
      [organizations|folders|projects]/{resource_id}/policies/{constraint_name}.
  """
  policy_name_tokens = _GetPolicyNameTokens(policy_name)
  return 'constraints/{}'.format(policy_name_tokens[3])


def GetResourceFromPolicyName(policy_name):
  """Returns the resource from the specified policy name.

  A resource has the following syntax:
  [organizations|folders|projects]/{resource_id}.

  Args:
    policy_name: The name of the policy. A policy name has the following syntax:
      [organizations|folders|projects]/{resource_id}/policies/{constraint_name}.
  """
  policy_name_tokens = _GetPolicyNameTokens(policy_name)
  return '{}/{}'.format(policy_name_tokens[0], policy_name_tokens[1])


def GetPolicyNameFromConstraintName(constraint_name):
  """Returns the associated policy name for the specified constraint name.

  A policy name has the following syntax:
  [organizations|folders|projects]/{resource_id}/policies/{constraint_name}.

  Args:
    constraint_name: The name of the constraint. A constraint name has the
      following syntax:
        [organizations|folders|projects]/{resource_id}/constraints/{constraint_name}.
  """
  constraint_name_tokens = _GetConstraintNameTokens(constraint_name)
  return '{}/{}/policies/{}'.format(constraint_name_tokens[0],
                                    constraint_name_tokens[1],
                                    constraint_name_tokens[3])


def GetMatchingRulesFromPolicy(policy, condition_expression=None):
  """Returns a list of rules on the policy that contain the specified condition expression.

  In the case that condition_expression is None, rules without conditions are
  returned.

  Args:
    policy: messages.GoogleCloudOrgpolicy{api_version}Policy, The policy object
      to search.
    condition_expression: str, The condition expression to look for.
  """
  if condition_expression is None:
    condition_filter = lambda rule: rule.condition is None
  else:
    condition_filter = lambda rule: rule.condition is not None and rule.condition.expression == condition_expression

  return list(filter(condition_filter, policy.spec.rules))


def GetNonMatchingRulesFromPolicy(policy, condition_expression=None):
  """Returns a list of rules on the policy that do not contain the specified condition expression.

  In the case that condition_expression is None, rules with conditions are
  returned.

  Args:
    policy: messages.GoogleCloudOrgpolicy{api_version}Policy, The policy object
      to search.
    condition_expression: str, The condition expression to look for.
  """
  if condition_expression is None:
    condition_filter = lambda rule: rule.condition is not None
  else:
    condition_filter = lambda rule: rule.condition is None or rule.condition.expression != condition_expression

  return list(filter(condition_filter, policy.spec.rules))


def _GetPolicyNameTokens(policy_name):
  """Returns the individual tokens from the policy name.

  Args:
    policy_name: The name of the policy. A policy name has the following syntax:
      [organizations|folders|projects]/{resource_id}/policies/{constraint_name}.
  """
  policy_name_tokens = policy_name.split('/')
  if len(policy_name_tokens) != 4:
    raise exceptions.InvalidInputError(
        "Invalid policy name '{}': Name must be in the form [projects|folders|organizations]/{{resource_id}}/policies/{{constraint_name}}."
        .format(policy_name))
  return policy_name_tokens


def _GetConstraintNameTokens(constraint_name):
  """Returns the individual tokens from the constraint name.

  Args:
    constraint_name: The name of the constraint. A constraint name has the
      following syntax:
        [organizations|folders|projects]/{resource_id}/constraints/{constraint_name}.
  """
  constraint_name_tokens = constraint_name.split('/')
  if len(constraint_name_tokens) != 4:
    raise exceptions.InvalidInputError(
        "Invalid constraint name '{}': Name must be in the form [projects|folders|organizations]/{{resource_id}}/constraints/{{constraint_name}}."
        .format(constraint_name))
  return constraint_name_tokens
