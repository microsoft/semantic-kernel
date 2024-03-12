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
"""Org Policy command utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.command_lib.org_policies import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

CONSTRAINT_PREFIX = 'constraints/'
CUSTOM_CONSTRAINT_PREFIX = 'customConstraints/'
UPDATE_MASK_POLICY_PREFIX = 'policy.'


def GetConstraintFromArgs(args):
  """Returns the constraint from the user-specified arguments.

  A constraint has the following syntax: constraints/{constraint_name}.

  This handles both cases in which the user specifies and does not specify the
  constraint prefix.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  if args.constraint.startswith(CONSTRAINT_PREFIX):
    return args.constraint

  return CONSTRAINT_PREFIX + args.constraint


def GetConstraintNameFromArgs(args):
  """Returns the constraint name from the user-specified arguments.

  This handles both cases in which the user specifies and does not specify the
  constraint prefix.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  if args.constraint.startswith(CONSTRAINT_PREFIX):
    return args.constraint[len(CONSTRAINT_PREFIX):]

  return args.constraint


def GetCustomConstraintNameFromArgs(args):
  """Returns the custom constraint name from the user-specified arguments.

  This handles both cases in which the user specifies and does not specify the
  custom constraint prefix.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  if args.custom_constraint.startswith(CUSTOM_CONSTRAINT_PREFIX):
    return args.custom_constraint[len(CUSTOM_CONSTRAINT_PREFIX):]

  return args.custom_constraint


def GetResourceFromArgs(args):
  """Returns the resource from the user-specified arguments.

  A resource has the following syntax:
  [organizations|folders|projects]/{resource_id}.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  resource_id = args.organization or args.folder or args.project

  if args.organization:
    resource_type = 'organizations'
  elif args.folder:
    resource_type = 'folders'
  else:
    resource_type = 'projects'

  return '{}/{}'.format(resource_type, resource_id)


def GetPolicyNameFromArgs(args):
  """Returns the policy name from the user-specified arguments.

  A policy name has the following syntax:
  [organizations|folders|projects]/{resource_id}/policies/{constraint_name}.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  resource = GetResourceFromArgs(args)
  constraint_name = GetConstraintNameFromArgs(args)

  return '{}/policies/{}'.format(resource, constraint_name)


def GetCustomConstraintFromArgs(args):
  """Returns the CustomConstraint from the user-specified arguments.

  A CustomConstraint has the following syntax:
  organizations/{organization_id}/customConstraints/{constraint_name}.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  organization_id = args.organization
  constraint_name = GetCustomConstraintNameFromArgs(args)

  return 'organizations/{}/customConstraints/{}'.format(organization_id,
                                                        constraint_name)


def GetUpdateMaskFromArgs(args):
  """Returns the update-mask from the user-specified arguments.

  This handles both cases in which the user specifies and does not specify the
  policy prefix for partial update of spec or dry_run_spec fields.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  if args.update_mask is None:
    return args.update_mask
  elif args.update_mask.startswith(UPDATE_MASK_POLICY_PREFIX):
    return args.update_mask
  elif (args.update_mask == 'spec' or args.update_mask == 'dry_run_spec' or
        args.update_mask == 'dryRunSpec'):
    return UPDATE_MASK_POLICY_PREFIX + args.update_mask
  return args.update_mask


def _GetPolicyMessageName(release_track):
  """Returns the organization policy message name based on the release_track."""
  api_version = org_policy_service.GetApiVersion(release_track).capitalize()
  return 'GoogleCloudOrgpolicy' + api_version + 'Policy'


def GetMessageFromFile(filepath, release_track):
  """Returns a message populated from the JSON or YAML file on the specified filepath.

  Args:
    filepath: str, A local path to an object specification in JSON or YAML
      format.
    release_track: calliope.base.ReleaseTrack, Release track of the command.
  """
  file_contents = files.ReadFileContents(filepath)

  try:
    yaml_obj = yaml.load(file_contents)
    json_str = json.dumps(yaml_obj)
  except yaml.YAMLParseError:
    json_str = file_contents

  org_policy_messages = org_policy_service.OrgPolicyMessages(release_track)
  message = getattr(org_policy_messages, _GetPolicyMessageName(release_track))
  try:
    return encoding.JsonToMessage(message, json_str)
  except Exception as e:
    raise exceptions.InvalidInputError('Unable to parse file [{}]: {}.'.format(
        filepath, e))


def GetCustomConstraintMessageFromFile(filepath, release_track):
  """Returns a message populated from the JSON or YAML file on the specified filepath.

  Args:
    filepath: str, A local path to an object specification in JSON or YAML
      format.
    release_track: calliope.base.ReleaseTrack, Release track of the command.
  """
  file_contents = files.ReadFileContents(filepath)

  try:
    yaml_obj = yaml.load(file_contents)
    json_str = json.dumps(yaml_obj)
  except yaml.YAMLParseError:
    json_str = file_contents

  org_policy_messages = org_policy_service.OrgPolicyMessages(release_track)
  message = getattr(org_policy_messages,
                    'GoogleCloudOrgpolicyV2CustomConstraint')
  try:
    return encoding.JsonToMessage(message, json_str)
  except Exception as e:
    raise exceptions.InvalidInputError('Unable to parse file [{}]: {}.'.format(
        filepath, e))


def RemoveAllowedValuesFromPolicy(policy, args, release_track):
  """Removes the specified allowed values from all policy rules containing the specified condition.

  It searches for and removes the specified values from the
  lists of allowed values on those rules. Any modified rule with empty lists
  of allowed values and denied values after this operation is deleted.

  Args:
    policy: messages.GoogleCloudOrgpolicy{api_version}Policy, The policy to be
      updated.
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
    release_track: calliope.base.ReleaseTrack, Release track of the command.

  Returns:
    The updated policy.
  """
  new_policy = copy.deepcopy(policy)
  if not new_policy.spec.rules:
    return policy

  # Remove the specified values from the list of allowed values for each rule.
  specified_values = set(args.value)
  for rule_to_update in new_policy.spec.rules:
    if rule_to_update.values is not None:
      rule_to_update.values.allowedValues = [
          value for value in rule_to_update.values.allowedValues
          if value not in specified_values
      ]

  return _DeleteRulesWithEmptyValues(new_policy, release_track)


def RemoveDeniedValuesFromPolicy(policy, args, release_track):
  """Removes the specified denied values from all policy rules.

  It searches for and removes the specified values from the
  lists of denied values on those rules. Any modified rule with empty lists
  of allowed values and denied values after this operation is deleted.

  Args:
    policy: messages.GoogleCloudOrgpolicy{api_version}Policy, The policy to be
      updated.
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
    release_track: calliope.base.ReleaseTrack, Release track of the command.

  Returns:
    The updated policy.
  """
  new_policy = copy.deepcopy(policy)
  if not new_policy.spec.rules:
    return policy

  # Remove the specified values from the list of denied values for each rule.
  specified_values = set(args.value)
  for rule_to_update in new_policy.spec.rules:
    if rule_to_update.values is not None:
      rule_to_update.values.deniedValues = [
          value for value in rule_to_update.values.deniedValues
          if value not in specified_values
      ]

  return _DeleteRulesWithEmptyValues(new_policy, release_track)


def _DeleteRulesWithEmptyValues(policy, release_track):
  """Delete any rule with empty lists of allowed values and denied values and no other field set.

  Args:
    policy: messages.GoogleCloudOrgpolicy{api_version}Policy, The policy to be
      updated.
    release_track: calliope.base.ReleaseTrack, Release track of the command.

  Returns:
    The updated policy.
  """
  new_policy = copy.deepcopy(policy)
  org_policy_api = org_policy_service.OrgPolicyApi(release_track)

  values = org_policy_api.BuildPolicySpecPolicyRuleStringValues()
  matching_empty_rule = org_policy_api.BuildPolicySpecPolicyRule(values=values)

  new_policy.spec.rules = [
      rule for rule in new_policy.spec.rules if rule != matching_empty_rule
  ]

  return new_policy


def CreateRuleOnPolicy(policy, release_track, condition_expression=None):
  """Creates a rule on the policy that contains the specified condition expression.

  In the case that condition_expression is None, a rule without a condition is
  created.

  Args:
    policy: messages.GoogleCloudOrgpolicy{api_version}Policy, The policy object
      to be updated.
    release_track: release track of the command
    condition_expression: str, The condition expression to create a new rule
      with.

  Returns:
    The rule that was created as well as the new policy that includes this
    rule.
  """
  org_policy_api = org_policy_service.OrgPolicyApi(release_track)

  new_policy = copy.deepcopy(policy)

  condition = None
  if condition_expression is not None:
    condition = org_policy_api.messages.GoogleTypeExpr(
        expression=condition_expression)

  new_rule = org_policy_api.BuildPolicySpecPolicyRule(condition=condition)
  new_policy.spec.rules.append(new_rule)

  return new_rule, new_policy
