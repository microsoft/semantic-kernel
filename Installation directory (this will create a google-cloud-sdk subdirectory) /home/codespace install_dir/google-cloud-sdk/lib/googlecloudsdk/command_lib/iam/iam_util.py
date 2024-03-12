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
"""General IAM utilities used by the Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import binascii
import re
import textwrap

from apitools.base.protorpclite import messages as apitools_messages
from apitools.base.py import encoding

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.iam import completers
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
import six

# Kluge for fixing inconsistency in python message
# generation from proto. See b/124063772.
kms_message = core_apis.GetMessagesModule('cloudkms', 'v1')
encoding.AddCustomJsonFieldMapping(
    kms_message.CloudkmsProjectsLocationsEkmConfigGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')
encoding.AddCustomJsonFieldMapping(
    kms_message.CloudkmsProjectsLocationsEkmConnectionsGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')
encoding.AddCustomJsonFieldMapping(
    kms_message.CloudkmsProjectsLocationsKeyRingsGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')

encoding.AddCustomJsonFieldMapping(
    kms_message.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')

encoding.AddCustomJsonFieldMapping(
    kms_message.CloudkmsProjectsLocationsKeyRingsImportJobsGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')
secrets_message = core_apis.GetMessagesModule('secretmanager', 'v1')
encoding.AddCustomJsonFieldMapping(
    secrets_message.SecretmanagerProjectsSecretsGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')
encoding.AddCustomJsonFieldMapping(
    secrets_message.SecretmanagerProjectsLocationsSecretsGetIamPolicyRequest,
    'options_requestedPolicyVersion',
    'options.requestedPolicyVersion',
)

msgs = core_apis.GetMessagesModule('iam', 'v1')
encoding.AddCustomJsonFieldMapping(
    msgs.IamProjectsServiceAccountsGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')

privateca_message = core_apis.GetMessagesModule('privateca', 'v1')
encoding.AddCustomJsonFieldMapping(
    privateca_message.PrivatecaProjectsLocationsCaPoolsGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')
encoding.AddCustomJsonFieldMapping(
    privateca_message
    .PrivatecaProjectsLocationsCertificateTemplatesGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')

clouddeploy_message = core_apis.GetMessagesModule('clouddeploy', 'v1')
encoding.AddCustomJsonFieldMapping(
    clouddeploy_message
    .ClouddeployProjectsLocationsDeliveryPipelinesGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')
encoding.AddCustomJsonFieldMapping(
    clouddeploy_message.ClouddeployProjectsLocationsTargetsGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')
encoding.AddCustomJsonFieldMapping(
    clouddeploy_message
    .ClouddeployProjectsLocationsCustomTargetTypesGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')

binaryauthorization_message_v1alpha2 = core_apis.GetMessagesModule(
    'binaryauthorization', 'v1alpha2')
encoding.AddCustomJsonFieldMapping(
    binaryauthorization_message_v1alpha2
    .BinaryauthorizationProjectsAttestorsGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')
encoding.AddCustomJsonFieldMapping(
    binaryauthorization_message_v1alpha2
    .BinaryauthorizationProjectsPolicyGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')

binaryauthorization_message_v1beta1 = core_apis.GetMessagesModule(
    'binaryauthorization', 'v1beta1')
encoding.AddCustomJsonFieldMapping(
    binaryauthorization_message_v1beta1
    .BinaryauthorizationProjectsAttestorsGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')
encoding.AddCustomJsonFieldMapping(
    binaryauthorization_message_v1beta1
    .BinaryauthorizationProjectsPolicyGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')

binaryauthorization_message_v1 = core_apis.GetMessagesModule(
    'binaryauthorization', 'v1')
encoding.AddCustomJsonFieldMapping(
    binaryauthorization_message_v1
    .BinaryauthorizationProjectsPolicyGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')

run_message_v1 = core_apis.GetMessagesModule('run', 'v1')
encoding.AddCustomJsonFieldMapping(
    run_message_v1.RunProjectsLocationsServicesGetIamPolicyRequest,
    'options_requestedPolicyVersion', 'options.requestedPolicyVersion')

MANAGED_BY = (
    msgs.IamProjectsServiceAccountsKeysListRequest.KeyTypesValueValuesEnum)
CREATE_KEY_TYPES = (
    msgs.CreateServiceAccountKeyRequest.PrivateKeyTypeValueValuesEnum)
KEY_TYPES = (msgs.ServiceAccountKey.PrivateKeyTypeValueValuesEnum)
PUBLIC_KEY_TYPES = (
    msgs.IamProjectsServiceAccountsKeysGetRequest.PublicKeyTypeValueValuesEnum)
STAGE_TYPES = (msgs.Role.StageValueValuesEnum)

SERVICE_ACCOUNTS_COLLECTION = 'iam.projects.serviceAccounts'

SERVICE_ACCOUNT_FORMAT = ('table(displayName:label="DISPLAY NAME", email, '
                          'disabled)')
SERVICE_ACCOUNT_KEY_FORMAT = """
    table(
        name.scope(keys):label=KEY_ID,
        validAfterTime:label=CREATED_AT,
        validBeforeTime:label=EXPIRES_AT,
        disabled:label=DISABLED
    )
"""
CONDITION_FORMAT_EXCEPTION = gcloud_exceptions.InvalidArgumentException(
    'condition',
    'condition must be either `None` or a list of key=value pairs. '
    'If not `None`, `expression` and `title` are required keys.\n'
    'Example: --condition=expression=[expression],title=[title],'
    'description=[description]')

CONDITION_FILE_FORMAT_EXCEPTION = gcloud_exceptions.InvalidArgumentException(
    'condition-from-file',
    'condition-from-file must be a path to a YAML or JSON file containing the '
    'condition. `expression` and `title` are required keys. `description` is '
    'optional. To specify a `None` condition, use --condition=None.')

MAX_LIBRARY_IAM_SUPPORTED_VERSION = 3

_ALL_CONDITIONS = {'All': None}
_NEW_CONDITION = object()
_NONE_CONDITION = {'None': None}


def _IsAllConditions(condition):
  return condition == _ALL_CONDITIONS


class IamEtagReadError(core_exceptions.Error):
  """IamEtagReadError is raised when etag is badly formatted."""


class IamPolicyBindingNotFound(core_exceptions.Error):
  """Raised when the specified IAM policy binding is not found."""


class IamPolicyBindingInvalidError(core_exceptions.Error):
  """Raised when the specified IAM policy binding is invalid."""


class IamPolicyBindingIncompleteError(IamPolicyBindingInvalidError):
  """Raised when the specified IAM policy binding is incomplete."""


def AddMemberFlag(parser, verb, hide_special_member_types, required=True):
  """Create --member flag and add to parser."""
  help_str = ("""\
The principal {verb}. Should be of the form `user|group|serviceAccount:email` or
`domain:domain`.

Examples: `user:test-user@gmail.com`, `group:admins@example.com`,
`serviceAccount:test123@example.domain.com`, or
`domain:example.domain.com`.
      """).format(verb=verb)
  # Adding role bindings for a deleted principal is a very uncommon use case.
  if 'remove' in verb:
    help_str += ("""
Deleted principals have an additional `deleted:` prefix and a `?uid=UID` suffix,
where ``UID'' is a unique identifier for the principal. Example:
`deleted:user:test-user@gmail.com?uid=123456789012345678901`.
      """)
  if not hide_special_member_types:
    help_str += ("""
Some resources also accept the following special values:
* `allUsers` - Special identifier that represents anyone who is on the internet,
   with or without a Google account.
* `allAuthenticatedUsers` - Special identifier that represents anyone who is
   authenticated with a Google account or a service account.
      """)
  parser.add_argument(
      '--member',
      metavar='PRINCIPAL',
      required=required,
      help=help_str,
      suggestion_aliases=['--principal'])


def _ConditionArgDict():
  condition_spec = {
      'expression': str,
      'title': str,
      'description': str,
      'None': None
  }
  return arg_parsers.ArgDict(spec=condition_spec, allow_key_only=True)


def _ConditionHelpText(intro):
  """Get the help text for --condition."""

  help_text = ("""\
{intro}

When using the `--condition` flag, include the following key-value pairs:

*expression*::: (Required) Condition expression that evaluates to True or False.
This uses a subset of Common Expression Language syntax.

If the condition expression includes a comma, use a different delimiter to
separate the key-value pairs. Specify the delimiter before listing the
key-value pairs. For example, to specify a colon (`:`) as the delimiter, do the
following: `--condition=^:^title=TITLE:expression=EXPRESSION`. For more
information, see https://cloud.google.com/sdk/gcloud/reference/topic/escaping.

*title*::: (Required) A short string describing the purpose of the expression.

*description*::: (Optional) Additional description for the expression.
      """).format(intro=intro)
  return help_text


def _AddConditionFlagsForAddBindingToIamPolicy(parser):
  """Create flags for condition and add to parser."""
  condition_intro = """\
A condition to include in the binding. When the condition is explicitly
specified as `None` (`--condition=None`), a binding without a condition is
added. When the condition is specified and is not `None`, `--role` cannot be a
basic role. Basic roles are `roles/editor`, `roles/owner`, and `roles/viewer`.
For more on conditions, refer to the conditions overview guide:
https://cloud.google.com/iam/docs/conditions-overview"""
  help_str_condition = _ConditionHelpText(condition_intro)
  help_str_condition_from_file = """
Path to a local JSON or YAML file that defines the condition.
To see available fields, see the help for `--condition`."""
  condition_group = parser.add_mutually_exclusive_group()
  condition_group.add_argument(
      '--condition',
      type=_ConditionArgDict(),
      metavar='KEY=VALUE',
      help=help_str_condition)

  condition_group.add_argument(
      '--condition-from-file',
      type=arg_parsers.FileContents(),
      help=help_str_condition_from_file)


def _AddConditionFlagsForRemoveBindingFromIamPolicy(parser,
                                                    condition_completer=None):
  """Create flags for condition and add to parser."""
  condition_intro = """\
The condition of the binding that you want to remove. When the condition is
explicitly specified as `None` (`--condition=None`), a binding without a
condition is removed. Otherwise, only a binding with a condition that exactly
matches the specified condition (including the optional description) is removed.
For more on conditions, refer to the conditions overview guide:
https://cloud.google.com/iam/docs/conditions-overview"""
  help_str_condition = _ConditionHelpText(condition_intro)
  help_str_condition_from_file = """
Path to a local JSON or YAML file that defines the condition.
To see available fields, see the help for `--condition`."""
  help_str_condition_all = """
Remove all bindings with this role and principal, irrespective of any
conditions."""
  condition_group = parser.add_mutually_exclusive_group()
  condition_group.add_argument(
      '--condition',
      type=_ConditionArgDict(),
      metavar='KEY=VALUE',
      completer=condition_completer,
      help=help_str_condition)

  condition_group.add_argument(
      '--condition-from-file',
      type=arg_parsers.FileContents(),
      help=help_str_condition_from_file)

  condition_group.add_argument(
      '--all', action='store_true', help=help_str_condition_all)


def ValidateConditionArgument(condition, exception):
  if 'None' in condition:
    if ('expression' in condition or 'description' in condition or
        'title' in condition):
      raise exception
  else:
    if not condition.get('expression') or not condition.get('title'):
      raise exception


def ValidateMutexConditionAndPrimitiveRoles(condition, role):
  primitive_roles = ['roles/editor', 'roles/owner', 'roles/viewer']
  if (_ConditionIsSpecified(condition) and not _IsNoneCondition(condition) and
      role in primitive_roles):
    raise IamPolicyBindingInvalidError(
        'Binding with a condition and a basic role is not allowed. '
        'Basic roles are `roles/editor`, `roles/owner`, '
        'and `roles/viewer`.')


def ValidateAndExtractConditionMutexRole(args):
  """Extract IAM condition from arguments and validate conditon/role mutex."""
  condition = ValidateAndExtractCondition(args)
  ValidateMutexConditionAndPrimitiveRoles(condition, args.role)
  return condition


def ValidateAndExtractCondition(args):
  """Extract IAM condition from arguments."""
  condition = None
  if args.IsSpecified('condition'):
    ValidateConditionArgument(args.condition, CONDITION_FORMAT_EXCEPTION)
    condition = args.condition
  if args.IsSpecified('condition_from_file'):
    condition = ParseYamlOrJsonCondition(args.condition_from_file)
  return condition


def AddArgForPolicyFile(parser):
  """Adds the IAM policy file argument to the given parser.

  Args:
    parser: An argparse.ArgumentParser-like object to which we add the argss.

  Raises:
    ArgumentError if one of the arguments is already defined in the parser.
  """
  parser.add_argument(
      'policy_file',
      metavar='POLICY_FILE',
      help="""\
        Path to a local JSON or YAML formatted file containing a valid policy.

        The output of the `get-iam-policy` command is a valid file, as is any
        JSON or YAML file conforming to the structure of a
        [Policy](https://cloud.google.com/iam/reference/rest/v1/Policy).
        """)


def AddArgsForAddIamPolicyBinding(parser,
                                  role_completer=None,
                                  add_condition=False,
                                  hide_special_member_types=False):
  """Adds the IAM policy binding arguments for role and members.

  Args:
    parser: An argparse.ArgumentParser-like object to which we add the argss.
    role_completer: A command_lib.iam.completers.IamRolesCompleter class to
      complete the `--role` flag value.
    add_condition: boolean, If true, add the flags for condition.
    hide_special_member_types: boolean. If true, help text for member does not
      include special values `allUsers` and `allAuthenticatedUsers`.

  Raises:
    ArgumentError if one of the arguments is already defined in the parser.
  """

  help_text = """
    Role name to assign to the principal. The role name is the complete path of
    a predefined role, such as `roles/logging.viewer`, or the role ID for a
    custom role, such as `organizations/{ORGANIZATION_ID}/roles/logging.viewer`.
  """

  parser.add_argument(
      '--role', required=True, completer=role_completer, help=help_text)
  AddMemberFlag(parser, 'to add the binding for', hide_special_member_types)
  if add_condition:
    _AddConditionFlagsForAddBindingToIamPolicy(parser)


# TODO(b/114447521): implement a completer for condition
def AddArgsForRemoveIamPolicyBinding(parser,
                                     role_completer=None,
                                     add_condition=False,
                                     condition_completer=None,
                                     hide_special_member_types=False):
  """Adds the IAM policy binding arguments for role and members.

  Args:
    parser: An argparse.ArgumentParser-like object to which we add the args.
    role_completer: A command_lib.iam.completers.IamRolesCompleter class to
      complete the --role flag value.
    add_condition: boolean, If true, add the flags for condition.
    condition_completer: A completer to complete the condition flag value.
    hide_special_member_types: boolean. If true, help text for member does not
      include special values `allUsers` and `allAuthenticatedUsers`.

  Raises:
    ArgumentError if one of the arguments is already defined in the parser.
  """
  parser.add_argument(
      '--role',
      required=True,
      completer=role_completer,
      help='The role to remove the principal from.')
  AddMemberFlag(parser, 'to remove the binding for', hide_special_member_types)
  if add_condition:
    _AddConditionFlagsForRemoveBindingFromIamPolicy(
        parser, condition_completer=condition_completer)


def AddBindingToIamPolicy(binding_message_type, policy, member, role):
  """Given an IAM policy, add new bindings as specified by args.

  An IAM binding is a pair of role and member. Check if the arguments passed
  define both the role and member attribute, create a binding out of their
  values, and append it to the policy.

  Args:
    binding_message_type: The protorpc.Message of the Binding to create
    policy: IAM policy to which we want to add the bindings.
    member: The member to add to IAM policy.
    role: The role the member should have.

  Returns:
    boolean, whether or not the policy was updated.
  """

  # First check all bindings to see if the member is already in a binding with
  # the same role.
  # A policy can have multiple bindings with the same role. This is why we need
  # to explicitly do this as a separate, first, step and check all bindings.
  for binding in policy.bindings:
    if binding.role == role:
      if member in binding.members:
        return False  # Nothing to do. Member already has the role.

  # Second step: check to see if a binding already exists with the same role and
  # add the member to this binding. This is to not create new bindings with
  # the same role.
  for binding in policy.bindings:
    if binding.role == role:
      binding.members.append(member)
      return True

  # Third step: no binding was found that has the same role. Create a new one.
  policy.bindings.append(
      binding_message_type(members=[member], role='{0}'.format(role)))
  return True


def _IsNoneCondition(condition):
  """When user specify --condition=None."""
  return condition is not None and 'None' in condition


def _ConditionIsSpecified(condition):
  """When --condition is specified."""
  return condition is not None


def AddBindingToIamPolicyWithCondition(binding_message_type,
                                       condition_message_type, policy, member,
                                       role, condition):
  """Given an IAM policy, add a new role/member binding with condition.

  An IAM binding is a pair of role and member with an optional condition.
  Check if the arguments passed define both the role and member attribute,
  create a binding out of their values, and append it to the policy.

  Args:
    binding_message_type: The protorpc.Message of the Binding to create.
    condition_message_type: the protorpc.Message of the Expr.
    policy: IAM policy to which we want to add the bindings.
    member: The member of the binding.
    role: The role the member should have.
    condition: The condition of the role/member binding.

  Raises:
    IamPolicyBindingIncompleteError: when user adds a binding without specifying
      --condition to a policy containing conditions in the non-interactive mode.
  """
  if _PolicyContainsCondition(policy) and not _ConditionIsSpecified(condition):
    if not console_io.CanPrompt():
      message = (
          'Adding a binding without specifying a condition to a '
          'policy containing conditions is prohibited in non-interactive '
          'mode. Run the command again with `--condition=None`')
      raise IamPolicyBindingIncompleteError(message)
    condition = _PromptForConditionAddBindingToIamPolicy(policy)
    ValidateConditionArgument(condition, CONDITION_FORMAT_EXCEPTION)
    ValidateMutexConditionAndPrimitiveRoles(condition, role)
  if (not _PolicyContainsCondition(policy) and
      _ConditionIsSpecified(condition) and not _IsNoneCondition(condition)):
    log.warning('Adding binding with condition to a policy without condition '
                'will change the behavior of add-iam-policy-binding and '
                'remove-iam-policy-binding commands.')
  condition = None if _IsNoneCondition(condition) else condition
  _AddBindingToIamPolicyWithCondition(binding_message_type,
                                      condition_message_type, policy, member,
                                      role, condition)


def _ConditionsInPolicy(policy, member=None, role=None):
  """Select conditions in bindings which have the given role and member.

  Search bindings from policy and return their conditions which has the given
  role and member if role and member are given. If member and role are not
  given, return all conditions. Duplicates are not returned.

  Args:
    policy: IAM policy to collect conditions
    member: member which should appear in the binding to select its condition
    role: role which should be the role of binding to select its condition

  Returns:
    A list of conditions got selected
  """
  conditions = {}
  for binding in policy.bindings:
    if (member is None or member in binding.members) and (role is None or
                                                          role == binding.role):
      condition = binding.condition
      conditions[_ConditionToString(condition)] = condition
  contain_none = False
  if 'None' in conditions:
    contain_none = True
    del conditions['None']
  conditions = [(condition_str, condition)
                for condition_str, condition in conditions.items()]
  conditions = sorted(conditions, key=lambda x: x[0])
  if contain_none:
    conditions.append(('None', _NONE_CONDITION))
  return conditions


def _ConditionToString(condition):
  if condition is None:
    return 'None'
  keys = ['expression', 'title', 'description']
  key_values = []
  for key in keys:
    if getattr(condition, key) is not None:
      key_values.append('{key}={value}'.format(
          key=key.upper(), value=getattr(condition, key)))
  return ', '.join(key_values)


def PromptChoicesForAddBindingToIamPolicy(policy):
  """The choices in a prompt for condition when adding binding to policy.

  All conditions in the policy will be returned. Two more choices (i.e.
  `None` and `Specify a new condition`) are appended.
  Args:
    policy: the IAM policy which the binding is added to.

  Returns:
    a list of conditions appearing in policy plus the choices of `None` and
    `Specify a new condition`.
  """
  conditions = _ConditionsInPolicy(policy)
  if conditions and conditions[-1][0] != 'None':
    conditions.append(('None', _NONE_CONDITION))
  conditions.append(('Specify a new condition', _NEW_CONDITION))
  return conditions


def PromptChoicesForRemoveBindingFromIamPolicy(policy, member, role):
  """The choices in a prompt for condition when removing binding from policy.

  Args:
    policy: the IAM policy which the binding is removed from.
    member: the member of the binding to be removed.
    role: the role of the binding to be removed.

  Returns:
    a list of conditions from the policy whose bindings contain the given member
    and role.
  """
  conditions = _ConditionsInPolicy(policy, member, role)
  if conditions:
    conditions.append(('all conditions', _ALL_CONDITIONS))
  return conditions


def _ToDictCondition(condition):
  if isinstance(condition, dict):
    return condition
  return_condition = {}
  for key in ('expression', 'title', 'description'):
    return_condition[key] = getattr(condition, key)
  return return_condition


def _PromptForConditionAddBindingToIamPolicy(policy):
  """Prompt user for a condition when adding binding."""
  prompt_message = ('The policy contains bindings with conditions, '
                    'so specifying a condition is required when adding a '
                    'binding. Please specify a condition.')
  conditions = PromptChoicesForAddBindingToIamPolicy(policy)
  condition_keys = [c[0] for c in conditions]

  condition_index = console_io.PromptChoice(
      condition_keys, prompt_string=prompt_message)
  if condition_index == len(conditions) - 1:
    return _PromptForNewCondition()
  return _ToDictCondition(conditions[condition_index][1])


def _PromptForConditionRemoveBindingFromIamPolicy(policy, member, role):
  """Prompt user for a condition when removing binding."""
  conditions = PromptChoicesForRemoveBindingFromIamPolicy(policy, member, role)
  if not conditions:
    raise IamPolicyBindingNotFound(
        'Policy binding with the specified principal '
        'and role not found!')
  prompt_message = ('The policy contains bindings with conditions, '
                    'so specifying a condition is required when removing a '
                    'binding. Please specify a condition.')
  condition_keys = [c[0] for c in conditions]

  condition_index = console_io.PromptChoice(
      condition_keys, prompt_string=prompt_message)
  if condition_index == len(conditions) - 1:
    return _ALL_CONDITIONS
  return _ToDictCondition(conditions[condition_index][1])


def _PromptForNewCondition():
  prompt_message = (
      'Condition is either `None` or a list of key=value pairs. '
      'If not `None`, `expression` and `title` are required keys.\n'
      'Example: --condition=expression=[expression],title=[title],'
      'description=[description].\nSpecify the condition')
  condition_string = console_io.PromptWithDefault(prompt_message)
  condition_dict = _ConditionArgDict()(condition_string)
  return condition_dict


def _EqualConditions(binding_condition, input_condition):
  if binding_condition is None and input_condition is None:
    return True
  if binding_condition is None or input_condition is None:
    return False
  return (binding_condition.expression == input_condition.get('expression') and
          binding_condition.title == input_condition.get('title') and
          binding_condition.description == input_condition.get('description'))


def _AddBindingToIamPolicyWithCondition(binding_message_type,
                                        condition_message_type, policy, member,
                                        role, condition):
  """Given an IAM policy, add a new role/member binding with condition."""
  for binding in policy.bindings:
    if binding.role == role and _EqualConditions(
        binding_condition=binding.condition, input_condition=condition):
      if member not in binding.members:
        binding.members.append(member)
      return

  condition_message = None
  if condition is not None:
    condition_message = condition_message_type(
        expression=condition.get('expression'),
        title=condition.get('title'),
        description=condition.get('description'))
  policy.bindings.append(
      binding_message_type(
          members=[member], role='{}'.format(role),
          condition=condition_message))


def RemoveBindingFromIamPolicyWithCondition(policy,
                                            member,
                                            role,
                                            condition,
                                            all_conditions=False):
  """Given an IAM policy, remove bindings as specified by the args.

  An IAM binding is a pair of role and member with an optional condition.
  Check if the arguments passed define both the role and member attribute,
  search the policy for a binding that contains this role, member and condition,
  and remove it from the policy.

  Args:
    policy: IAM policy from which we want to remove bindings.
    member: The member to remove from the IAM policy.
    role: The role of the member should be removed from.
    condition: The condition of the binding to be removed.
    all_conditions: If true, all bindings with the specified member and role
      will be removed, regardless of the condition.

  Raises:
    IamPolicyBindingNotFound: If specified binding is not found.
    IamPolicyBindingIncompleteError: when user removes a binding without
      specifying --condition to a policy containing conditions in the
      non-interactive mode.
  """
  if not all_conditions and _PolicyContainsCondition(
      policy) and not _ConditionIsSpecified(condition):
    if not console_io.CanPrompt():
      message = (
          'Removing a binding without specifying a condition from a '
          'policy containing conditions is prohibited in non-interactive '
          'mode. Run the command again with `--condition=None` to remove a '
          'binding without condition or run command with `--all` to remove all '
          'bindings of the specified principal and role.')
      raise IamPolicyBindingIncompleteError(message)
    condition = _PromptForConditionRemoveBindingFromIamPolicy(
        policy, member, role)

  if all_conditions or _IsAllConditions(condition):
    _RemoveBindingFromIamPolicyAllConditions(policy, member, role)
  else:
    condition = None if _IsNoneCondition(condition) else condition
    _RemoveBindingFromIamPolicyWithCondition(policy, member, role, condition)


def _RemoveBindingFromIamPolicyAllConditions(policy, member, role):
  """Remove all member/role bindings from policy regardless of condition."""
  conditions_removed = False
  for binding in policy.bindings:
    if role == binding.role and member in binding.members:
      binding.members.remove(member)
      conditions_removed = True
  if not conditions_removed:
    raise IamPolicyBindingNotFound(
        'Policy bindings with the specified principal '
        'and role not found!')
  policy.bindings[:] = [b for b in policy.bindings if b.members]


def _RemoveBindingFromIamPolicyWithCondition(policy, member, role, condition):
  """Remove the member/role binding with the condition from policy."""
  for binding in policy.bindings:
    if (role == binding.role and _EqualConditions(
        binding_condition=binding.condition, input_condition=condition) and
        member in binding.members):
      binding.members.remove(member)
      break
  else:
    raise IamPolicyBindingNotFound(
        'Policy binding with the specified principal, '
        'role, and condition not found!')
  policy.bindings[:] = [b for b in policy.bindings if b.members]


def _PolicyContainsCondition(policy):
  """Investigate if policy has bindings with condition.

  Given an IAM policy and return True if the policy contains any binding
  which has a condition. Return False otherwise.

  Args:
    policy: IAM policy.

  Returns:
    True if policy has bindings with conditions, otherwise False.
  """
  for binding in policy.bindings:
    if binding.condition:
      return True
  return False


def BindingInPolicy(policy, member, role):
  """Returns True if policy contains the specified binding."""
  for binding in policy.bindings:
    if binding.role == role and member in binding.members:
      return True
  return False


def RemoveBindingFromIamPolicy(policy, member, role):
  """Given an IAM policy, remove bindings as specified by the args.

  An IAM binding is a pair of role and member. Check if the arguments passed
  define both the role and member attribute, search the policy for a binding
  that contains this role and member, and remove it from the policy.

  Args:
    policy: IAM policy from which we want to remove bindings.
    member: The member to remove from the IAM policy.
    role: The role the member should be removed from.

  Raises:
    IamPolicyBindingNotFound: If specified binding is not found.
  """

  # First, remove the member from any binding that has the given role.
  # A server policy can have duplicates.
  for binding in policy.bindings:
    if binding.role == role and member in binding.members:
      binding.members.remove(member)
      break
  else:
    message = 'Policy binding with the specified principal and role not found!'
    raise IamPolicyBindingNotFound(message)

  # Second, remove any empty bindings.
  policy.bindings[:] = [b for b in policy.bindings if b.members]


def ConstructUpdateMaskFromPolicy(policy_file_path):
  """Construct a FieldMask based on input policy.

  Args:
    policy_file_path: Path to the JSON or YAML IAM policy file.

  Returns:
    a FieldMask containing policy fields to be modified, based on which fields
    are present in the input file.
  """
  policy_file = files.ReadFileContents(policy_file_path)
  # Since json is a subset of yaml, parse file as yaml.
  policy = yaml.load(policy_file)

  # The IAM update mask should only contain top level fields. Sort the fields
  # for testing purposes.
  return ','.join(sorted(policy.keys()))


def ParsePolicyFile(policy_file_path, policy_message_type):
  """Construct an IAM Policy protorpc.Message from a JSON/YAML formatted file.

  Args:
    policy_file_path: Path to the JSON or YAML IAM policy file.
    policy_message_type: Policy message type to convert JSON or YAML to.

  Returns:
    a protorpc.Message of type policy_message_type filled in from the JSON or
    YAML policy file.
  Raises:
    BadFileException if the JSON or YAML file is malformed.
  """
  policy, unused_mask = ParseYamlOrJsonPolicyFile(policy_file_path,
                                                  policy_message_type)

  if not policy.etag:
    msg = ('The specified policy does not contain an "etag" field '
           'identifying a specific version to replace. Changing a '
           'policy without an "etag" can overwrite concurrent policy '
           'changes.')
    console_io.PromptContinue(
        message=msg, prompt_string='Replace existing policy', cancel_on_no=True)
  return policy


def ParsePolicyFileWithUpdateMask(policy_file_path, policy_message_type):
  """Construct an IAM Policy protorpc.Message from a JSON/YAML formatted file.

  Also contructs a FieldMask based on input policy.
  Args:
    policy_file_path: Path to the JSON or YAML IAM policy file.
    policy_message_type: Policy message type to convert JSON or YAML to.

  Returns:
    a tuple of (policy, updateMask) where policy is a protorpc.Message of type
    policy_message_type filled in from the JSON or YAML policy file and
    updateMask is a FieldMask containing policy fields to be modified, based on
    which fields are present in the input file.
  Raises:
    BadFileException if the JSON or YAML file is malformed.
    IamEtagReadError if the etag is badly formatted.
  """
  policy, update_mask = ParseYamlOrJsonPolicyFile(policy_file_path,
                                                  policy_message_type)

  if not policy.etag:
    msg = ('The specified policy does not contain an "etag" field '
           'identifying a specific version to replace. Changing a '
           'policy without an "etag" can overwrite concurrent policy '
           'changes.')
    console_io.PromptContinue(
        message=msg, prompt_string='Replace existing policy', cancel_on_no=True)
  return (policy, update_mask)


def ParseYamlOrJsonPolicyFile(policy_file_path, policy_message_type):
  """Create an IAM Policy protorpc.Message from a YAML or JSON formatted file.

  Returns the parsed policy object and FieldMask derived from input dict.
  Args:
    policy_file_path: Path to the YAML or JSON IAM policy file.
    policy_message_type: Policy message type to convert YAML to.

  Returns:
    a tuple of (policy, updateMask) where policy is a protorpc.Message of type
    policy_message_type filled in from the JSON or YAML policy file and
    updateMask is a FieldMask containing policy fields to be modified, based on
    which fields are present in the input file.
  Raises:
    BadFileException if the YAML or JSON file is malformed.
    IamEtagReadError if the etag is badly formatted.
  """
  policy_to_parse = yaml.load_path(policy_file_path)
  try:
    policy = encoding.PyValueToMessage(policy_message_type, policy_to_parse)
    update_mask = ','.join(sorted(policy_to_parse.keys()))
  except (AttributeError) as e:
    # Raised when the input file is not properly formatted YAML policy file.
    raise gcloud_exceptions.BadFileException(
        'Policy file [{0}] is not a properly formatted YAML or JSON '
        'policy file. {1}'.format(policy_file_path, six.text_type(e)))
  except (apitools_messages.DecodeError, binascii.Error) as e:
    # DecodeError is raised when etag is badly formatted (not proper Base64)
    raise IamEtagReadError(
        'The etag of policy file [{0}] is not properly formatted. {1}'.format(
            policy_file_path, six.text_type(e)))
  return (policy, update_mask)


def ParseYamlOrJsonCondition(
    condition_file_content,
    file_format_exception=CONDITION_FILE_FORMAT_EXCEPTION):
  """Create a condition of IAM policy binding from content of YAML or JSON file.

  Args:
    condition_file_content: string, the content of a YAML or JSON file
      containing a condition.
    file_format_exception: InvalidArgumentException, the exception to throw when
      condition file is incorrectly formatted.

  Returns:
    a dictionary representation of the condition.
  """

  condition = yaml.load(condition_file_content)
  ValidateConditionArgument(condition, file_format_exception)
  return condition


def ParseYamlToRole(file_path, role_message_type):
  """Construct an IAM Role protorpc.Message from a Yaml formatted file.

  Args:
    file_path: Path to the Yaml IAM Role file.
    role_message_type: Role message type to convert Yaml to.

  Returns:
    a protorpc.Message of type role_message_type filled in from the Yaml
    role file.
  Raises:
    BadFileException if the Yaml file is malformed or does not exist.
  """
  role_to_parse = yaml.load_path(file_path)
  if 'stage' in role_to_parse:
    role_to_parse['stage'] = role_to_parse['stage'].upper()
  try:
    role = encoding.PyValueToMessage(role_message_type, role_to_parse)
  except (AttributeError) as e:
    # Raised when the YAML file is not properly formatted YAML role file.
    raise gcloud_exceptions.BadFileException(
        'Role file {0} is not a properly formatted YAML role file. {1}'.format(
            file_path, six.text_type(e)))
  except (apitools_messages.DecodeError, binascii.Error) as e:
    # DecodeError is raised when etag is badly formatted (not proper Base64)
    raise IamEtagReadError(
        'The etag of role file {0} is not properly formatted. {1}'.format(
            file_path, six.text_type(e)))
  return role


def ParseYamlToTrustStore(yaml_dict):
  """Construct a TrustStore protorpc.Message from the content of a Yaml file.

  Args:
    yaml_dict: YAML file content to parse.

  Returns:
    a TrustStore from the parsed YAML file.
  Raises:
    DecodeError if the Yaml file content could not be parsed.
  """
  config = messages_util.DictToMessageWithErrorCheck(yaml_dict, msgs.X509)
  return config.trustStore


def GetDetailedHelpForSetIamPolicy(collection,
                                   example_id='',
                                   example_see_more='',
                                   additional_flags='',
                                   use_an=False):
  """Returns a detailed_help for a set-iam-policy command.

  Args:
    collection: Name of the command collection (ex: "project", "dataset")
    example_id: Collection identifier to display in a sample command
        (ex: "my-project", '1234')
    example_see_more: Optional "See ... for details" message. If not specified,
      includes a default reference to IAM managing-policies documentation
    additional_flags: str, additional flags to include in the example command
      (after the command name and before the ID of the resource).
     use_an: If True, uses "an" instead of "a" for the article preceding uses of
       the collection.

  Returns:
    a dict with boilerplate help text for the set-iam-policy command
  """
  if not example_id:
    example_id = 'example-' + collection

  if not example_see_more:
    example_see_more = """
          See https://cloud.google.com/iam/docs/managing-policies for details
          of the policy file format and contents."""

  additional_flags = additional_flags + ' ' if additional_flags else ''
  a = 'an' if use_an else 'a'
  return {
      'brief':
          'Set IAM policy for {0} {1}.'.format(a, collection),
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          textwrap.dedent("""\
          The following command will read an IAM policy from 'policy.json' and
          set it for {a} {collection} with '{id}' as the identifier:

            $ {{command}} {flags}{id} policy.json

          {see_more}""".format(
              collection=collection,
              id=example_id,
              see_more=example_see_more,
              flags=additional_flags,
              a=a))
  }


def GetDetailedHelpForAddIamPolicyBinding(collection,
                                          example_id,
                                          role='roles/editor',
                                          use_an=False,
                                          condition=False):
  """Returns a detailed_help for an add-iam-policy-binding command.

  Args:
    collection: Name of the command collection (ex: "project", "dataset")
    example_id: Collection identifier to display in a sample command
        (ex: "my-project", '1234')
    role: The sample role to use in the documentation. The default of
      'roles/editor' is usually sufficient, but if your command group's users
      would more likely use a different role, you can override it here.
    use_an: If True, uses "an" instead of "a" for the article preceding uses of
      the collection.
    condition: If True, add help text for condition.

  Returns:
    a dict with boilerplate help text for the add-iam-policy-binding command
  """
  a = 'an' if use_an else 'a'
  note = ('See https://cloud.google.com/iam/docs/managing-policies for details '
          'of policy role and principal types.')
  detailed_help = {
      'brief':
          'Add IAM policy binding for {0} {1}.'.format(a, collection),
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """To add an IAM policy binding for the role of '{role}' for the user
'test-user@gmail.com' on {a} {collection} with identifier
'{example_id}', run:

  $ {{command}} {example_id} --member='user:test-user@gmail.com' --role='{role}'

To add an IAM policy binding for the role of '{role}' to the service
account 'test-proj1@example.domain.com', run:

  $ {{command}} {example_id} --member='serviceAccount:test-proj1@example.domain.com' --role='{role}'

To add an IAM policy binding for the role of '{role}' for all
authenticated users on {a} {collection} with identifier
'{example_id}', run:

  $ {{command}} {example_id} --member='allAuthenticatedUsers' --role='{role}'
  """.format(collection=collection, example_id=example_id, role=role, a=a)
  }
  if condition:
    detailed_help['EXAMPLES'] = detailed_help['EXAMPLES'] + """\n
To add an IAM policy binding that expires at the end of the year 2018 for the
role of '{role}' and the user 'test-user@gmail.com' on {a} {collection} with
identifier '{example_id}', run:

  $ {{command}} {example_id} --member='user:test-user@gmail.com' --role='{role}' --condition='expression=request.time < timestamp("2019-01-01T00:00:00Z"),title=expires_end_of_2018,description=Expires at midnight on 2018-12-31'
  """.format(
      collection=collection, example_id=example_id, role=role, a=a)
  detailed_help['EXAMPLES'] = '\n'.join([detailed_help['EXAMPLES'], note])
  return detailed_help


def GetDetailedHelpForRemoveIamPolicyBinding(collection,
                                             example_id,
                                             role='roles/editor',
                                             use_an=False,
                                             condition=False):
  """Returns a detailed_help for a remove-iam-policy-binding command.

  Args:
    collection: Name of the command collection (ex: "project", "dataset")
    example_id: Collection identifier to display in a sample command
        (ex: "my-project", '1234')
    role: The sample role to use in the documentation. The default of
      'roles/editor' is usually sufficient, but if your command group's users
      would more likely use a different role, you can override it here.
    use_an: If True, uses "an" instead of "a" for the article preceding uses of
      the collection.
    condition: If True, add help text for condition.

  Returns:
    a dict with boilerplate help text for the remove-iam-policy-binding command
  """
  a = 'an' if use_an else 'a'
  note = (
      'See https://cloud.google.com/iam/docs/managing-policies for details'
      ' of policy role and member types.'
  )
  detailed_help = {
      'brief':
          'Remove IAM policy binding for {0} {1}.'.format(a, collection),
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
To remove an IAM policy binding for the role of '{role}' for the
user 'test-user@gmail.com' on {collection} with identifier
'{example_id}', run:

  $ {{command}} {example_id} --member='user:test-user@gmail.com' --role='{role}'

To remove an IAM policy binding for the role of '{role}' from all
authenticated users on {collection} '{example_id}', run:

  $ {{command}} {example_id} --member='allAuthenticatedUsers' --role='{role}'
  """.format(collection=collection, example_id=example_id, role=role)
  }
  if condition:
    detailed_help['EXAMPLES'] = detailed_help['EXAMPLES'] + """\n
To remove an IAM policy binding with a condition of
expression='request.time < timestamp("2019-01-01T00:00:00Z")',
title='expires_end_of_2018', and description='Expires at midnight on 2018-12-31'
for the role of '{role}' for the user 'test-user@gmail.com' on {collection}
with identifier '{example_id}', run:

  $ {{command}} {example_id} --member='user:test-user@gmail.com' --role='{role}' --condition='expression=request.time < timestamp("2019-01-01T00:00:00Z"),title=expires_end_of_2018,description=Expires at midnight on 2018-12-31'

To remove all IAM policy bindings regardless of the condition for the role of
'{role}' and for the user 'test-user@gmail.com' on {collection} with
identifier '{example_id}', run:

  $ {{command}} {example_id} --member='user:test-user@gmail.com' --role='{role}' --all
  """.format(
      collection=collection, example_id=example_id, role='roles/browser')
  detailed_help['EXAMPLES'] = '\n'.join([detailed_help['EXAMPLES'], note])
  return detailed_help


def GetHintForServiceAccountResource(action='act on'):
  """Returns a hint message for commands treating service account as a resource.

  Args:
    action: the action to take on the service account resource (with necessary
      prepositions), such as 'add iam policy bindings to'.
  """

  return ('When managing IAM roles, you can treat a service account either as '
          'a resource or as an identity. This command is to {action} a '
          'service account resource. There are other gcloud commands to '
          'manage IAM policies for other types of resources. For example, to '
          'manage IAM policies on a project, use the `$ gcloud projects` '
          'commands.'.format(action=action))


def ManagedByFromString(managed_by):
  """Parses a string into a MANAGED_BY enum.

  MANAGED_BY is an enum of who manages a service account key resource. IAM
  will rotate any SYSTEM_MANAGED keys by default.

  Args:
    managed_by: A string representation of a MANAGED_BY. Can be one of *user*,
      *system* or *any*.

  Returns:
    A KeyTypeValueValuesEnum (MANAGED_BY) value.
  """
  if managed_by == 'user':
    return [MANAGED_BY.USER_MANAGED]
  elif managed_by == 'system':
    return [MANAGED_BY.SYSTEM_MANAGED]
  elif managed_by == 'any':
    return []
  else:
    return [MANAGED_BY.KEY_TYPE_UNSPECIFIED]


def KeyTypeFromString(key_str):
  """Parses a string into a KeyType enum.

  Args:
    key_str: A string representation of a KeyType. Can be either *p12* or
      *json*.

  Returns:
    A PrivateKeyTypeValueValuesEnum value.
  """
  if key_str == 'p12':
    return KEY_TYPES.TYPE_PKCS12_FILE
  elif key_str == 'json':
    return KEY_TYPES.TYPE_GOOGLE_CREDENTIALS_FILE
  else:
    return KEY_TYPES.TYPE_UNSPECIFIED


def KeyTypeToString(key_type):
  """Get a string version of a KeyType enum.

  Args:
    key_type: An enum of either KEY_TYPES or CREATE_KEY_TYPES.

  Returns:
    The string representation of the key_type, such that
    parseKeyType(keyTypeToString(x)) is a no-op.
  """
  if (key_type == KEY_TYPES.TYPE_PKCS12_FILE or
      key_type == CREATE_KEY_TYPES.TYPE_PKCS12_FILE):
    return 'p12'
  elif (key_type == KEY_TYPES.TYPE_GOOGLE_CREDENTIALS_FILE or
        key_type == CREATE_KEY_TYPES.TYPE_GOOGLE_CREDENTIALS_FILE):
    return 'json'
  else:
    return 'unspecified'


def KeyTypeToCreateKeyType(key_type):
  """Transforms between instances of KeyType enums.

  Transforms KeyTypes into CreateKeyTypes.

  Args:
    key_type: A ServiceAccountKey.PrivateKeyTypeValueValuesEnum value.

  Returns:
    A IamProjectsServiceAccountKeysCreateRequest.PrivateKeyTypeValueValuesEnum
    value.
  """
  # For some stupid reason, HTTP requests generates different enum types for
  # each instance of an enum in the proto buffer. What's worse is that they're
  # not equal to one another.
  if key_type == KEY_TYPES.TYPE_PKCS12_FILE:
    return CREATE_KEY_TYPES.TYPE_PKCS12_FILE
  elif key_type == KEY_TYPES.TYPE_GOOGLE_CREDENTIALS_FILE:
    return CREATE_KEY_TYPES.TYPE_GOOGLE_CREDENTIALS_FILE
  else:
    return CREATE_KEY_TYPES.TYPE_UNSPECIFIED


def KeyTypeFromCreateKeyType(key_type):
  """The inverse of *toCreateKeyType*."""
  if key_type == CREATE_KEY_TYPES.TYPE_PKCS12_FILE:
    return KEY_TYPES.TYPE_PKCS12_FILE
  elif key_type == CREATE_KEY_TYPES.TYPE_GOOGLE_CREDENTIALS_FILE:
    return KEY_TYPES.TYPE_GOOGLE_CREDENTIALS_FILE
  else:
    return KEY_TYPES.TYPE_UNSPECIFIED


def ProjectToProjectResourceName(project):
  """Turns a project id into a project resource name."""
  return 'projects/{0}'.format(project)


def EmailToAccountResourceName(email):
  """Turns an email into a service account resource name."""
  return 'projects/-/serviceAccounts/{0}'.format(email)


def EmailAndKeyToResourceName(email, key):
  """Turns an email and key id into a key resource name."""
  return 'projects/-/serviceAccounts/{0}/keys/{1}'.format(email, key)


def EmailAndIdentityBindingToResourceName(email, identity_binding):
  """Turns an email and identity binding id into a key resource name."""
  return 'projects/-/serviceAccounts/{0}/identityBindings/{1}'.format(
      email, identity_binding)


def GetKeyIdFromResourceName(name):
  """Gets the key id from a resource name. No validation is done."""
  return name.split('/')[5]


def PublicKeyTypeFromString(key_str):
  """Parses a string into a PublicKeyType enum.

  Args:
    key_str: A string representation of a PublicKeyType. Can be either *pem* or
      *raw*.

  Returns:
    A PublicKeyTypeValueValuesEnum value.
  """
  if key_str == 'pem':
    return PUBLIC_KEY_TYPES.TYPE_X509_PEM_FILE
  return PUBLIC_KEY_TYPES.TYPE_RAW_PUBLIC_KEY


def StageTypeFromString(stage_str):
  """Parses a string into a stage enum.

  Args:
    stage_str: A string representation of a StageType. Can be *alpha* or *beta*
      or *ga* or *deprecated* or *disabled*.

  Returns:
    A StageValueValuesEnum value.
  """
  lower_stage_str = stage_str.lower()
  stage_dict = {
      'alpha': STAGE_TYPES.ALPHA,
      'beta': STAGE_TYPES.BETA,
      'ga': STAGE_TYPES.GA,
      'deprecated': STAGE_TYPES.DEPRECATED,
      'disabled': STAGE_TYPES.DISABLED
  }
  if lower_stage_str not in stage_dict:
    raise gcloud_exceptions.InvalidArgumentException(
        'stage',
        'The stage should be one of ' + ','.join(sorted(stage_dict)) + '.')
  return stage_dict[lower_stage_str]


def VerifyParent(organization, project, attribute='custom roles'):
  """Verify the parent name."""
  if organization is None and project is None:
    raise gcloud_exceptions.RequiredArgumentException(
        '--organization or --project',
        'Should specify the project or organization name for {0}.'.format(
            attribute))
  if organization and project:
    raise gcloud_exceptions.ConflictingArgumentsException(
        'organization', 'project')


def GetRoleName(organization,
                project,
                role,
                attribute='custom roles',
                parameter_name='ROLE_ID'):
  """Gets the Role name from organization Id and role Id."""
  if role.startswith('roles/'):
    if project or organization:
      raise gcloud_exceptions.InvalidArgumentException(
          parameter_name,
          'The role id that starts with \'roles/\' only stands for predefined '
          'role. Should not specify the project or organization for predefined '
          'roles')
    return role

  if role.startswith('projects/') or role.startswith('organizations/'):
    raise gcloud_exceptions.InvalidArgumentException(
        parameter_name, 'The role id should not include any \'projects/\' or '
        '\'organizations/\' prefix.')
  if '/' in role:
    raise gcloud_exceptions.InvalidArgumentException(
        parameter_name, 'The role id should not include any \'/\' character.')
  VerifyParent(organization, project, attribute)
  if organization:
    return 'organizations/{0}/roles/{1}'.format(organization, role)
  return 'projects/{0}/roles/{1}'.format(project, role)


def GetParentName(organization, project, attribute='custom roles'):
  """Gets the Role parent name from organization name or project name."""
  VerifyParent(organization, project, attribute)
  if organization:
    return 'organizations/{0}'.format(organization)
  return 'projects/{0}'.format(project)


def GetFullResourceName(resource_ref):
  """Convert a full resource URL to a full resource name (FRN).

  See https://cloud.google.com/iam/docs/full-resource-names.

  Args:
    resource_ref: googlecloudsdk.core.resources.Resource.

  Returns:
    str: Full resource name of the resource
  """
  full_name = resource_ref.SelfLink()
  full_name = re.sub(r'\w+://', '//', full_name)  # no protocol at the start
  full_name = re.sub(r'/v[0-9]+[0-9a-zA-Z]*/', '/', full_name)  # no version

  universe_domain_property = properties.VALUES.core.universe_domain
  universe_domain = universe_domain_property.Get()
  if universe_domain_property.default != universe_domain:
    # FRNs use the same format in all universes.
    full_name = full_name.replace(universe_domain,
                                  universe_domain_property.default, 1)

  if full_name.startswith('//www.'):
    # Convert '//www.googleapis.com/compute/' to '//compute.googleapis.com/'
    splitted_list = full_name.split('/')
    service = full_name.split('/')[3]
    splitted_list.pop(3)
    full_name = '/'.join(splitted_list)
    full_name = full_name.replace('//www.', '//{0}.'.format(service))
  return full_name


def ServiceAccountsUriFunc(resource):
  """Transforms a service account resource into a URL string.

  Args:
    resource: The ServiceAccount object

  Returns:
    URL to the service account
  """

  ref = resources.REGISTRY.Parse(
      resource.uniqueId, {'projectsId': resource.projectId},
      collection=SERVICE_ACCOUNTS_COLLECTION)
  return ref.SelfLink()


def AddServiceAccountNameArg(parser, action='to act on'):
  """Adds the IAM service account name argument that supports tab completion.

  Args:
    parser: An argparse.ArgumentParser-like object to which we add the args.
    action: Action to display in the help message. Should be something like 'to
      act on' or a relative phrase like 'whose policy to get'.

  Raises:
    ArgumentError if one of the arguments is already defined in the parser.
  """

  parser.add_argument(
      'service_account',
      metavar='SERVICE_ACCOUNT',
      type=GetIamAccountFormatValidator(),
      completer=completers.IamServiceAccountCompleter,
      help=('The service account {}. The account should be '
            'formatted either as a numeric service account ID '
            'or as an email, like this: '
            '123456789876543212345 or '
            'my-iam-account@somedomain.com.'.format(action)))


def AddServiceAccountRecommendArg(parser, action):
  """Adds optional recommend argument to the parser.

  Args:
    parser: An argparse.ArgumentParser-like object to which we add the args.
    action: Action to display in the help message. Should be something like
      'deletion' or a noun that describes the action being performed.

  Raises:
    ArgumentError if the argument is already defined in the parser.
  """
  parser.add_argument(
      '--recommend',
      metavar='BOOLEAN_VALUE',
      type=arg_parsers.ArgBoolean(),
      default=False,
      required=False,
      help=(
          'If true, checks Active Assist recommendation for the risk level of '
          'service account {}, and issues a warning in the prompt. Optional '
          'flag is set to false by default. For details see '
          'https://cloud.google.com/recommender/'
          'docs/change-risk-recommendations'
      ).format(action),
  )


def LogSetIamPolicy(name, kind):
  log.status.Print('Updated IAM policy for {} [{}].'.format(kind, name))


def GetIamAccountFormatValidator():
  """Checks that provided iam account identifier is valid."""
  return arg_parsers.RegexpValidator(
      # Overly broad on purpose but catches most common issues.
      r'^(.+@.+\..+|[0-9]+)$',
      'Not a valid service account identifier. It should be either a '
      'numeric string representing the unique_id or an email of the form: '
      'my-iam-account@somedomain.com or '
      'my-iam-account@PROJECT_ID.iam.gserviceaccount.com')


def GetIamOutputFileValidator():
  """Checks if the output file is writable."""

  def IsWritable(value):
    # If output is stdout ('-') then it is writable.
    if value == '-':
      return value
    try:
      with files.FileWriter(value, private=True) as f:
        f.close()
        return value
    except files.Error as e:
      raise gcloud_exceptions.BadFileException(e)

  return IsWritable


def SetRoleStageIfAlpha(role):
  """Set the role stage to Alpha if None.

  Args:
    role: A protorpc.Message of type Role.
  """
  if role.stage is None:
    role.stage = StageTypeFromString('alpha')


def GetResourceReference(project, organization):
  """Get the resource reference of a project or organization.

  Args:
    project: A project name string.
    organization: An organization id string.

  Returns:
    The resource reference of the given project or organization.
  """
  if project:
    return resources.REGISTRY.Parse(
        project, collection='cloudresourcemanager.projects')
  else:
    return resources.REGISTRY.Parse(
        organization, collection='cloudresourcemanager.organizations')


def TestingPermissionsWarning(permissions):
  """Prompt a warning for TESTING permissions with a 'y/n' question.

  Args:
    permissions: A list of permissions that need to be warned.
  """
  if permissions:
    msg = ('Note: permissions [' + ', '.join(permissions) +
           '] are in \'TESTING\' stage which means '
           'the functionality is not mature and they can go away in the '
           'future. This can break your workflows, so do not use them in '
           'production systems!')
    console_io.PromptContinue(
        message=msg,
        prompt_string='Are you sure you want to make this change?',
        cancel_on_no=True)


def ApiDisabledPermissionsWarning(permissions):
  """Prompt a warning for API diabled permissions.

  Args:
    permissions: A list of permissions that need to be warned.
  """
  if permissions:
    msg = (
        'API is not enabled for permissions: [' + ', '.join(permissions) +
        ']. Please enable the corresponding APIs to use those permissions.\n')
    log.warning(msg)
