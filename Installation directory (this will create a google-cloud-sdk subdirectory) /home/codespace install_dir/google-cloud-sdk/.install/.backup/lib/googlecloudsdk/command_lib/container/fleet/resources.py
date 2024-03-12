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
"""Functions for resource arguments in fleet commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.container.fleet import api_util
from googlecloudsdk.command_lib.container.fleet import util as cmd_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

_LOCATION_RE = re.compile('/locations/([a-z0-9-]+)/')


def PromptForMembership(memberships=None,
                        flag='--membership',
                        message='Please specify a membership:\n',
                        cancel=True):
  """Prompt the user for a membership from a list of memberships in the fleet.

  This method is referenced by fleet and feature commands as a fallthrough
  for getting the memberships when required.

  Args:
    memberships: List of memberships to prompt from
    flag: The name of the membership flag, used in the error message
    message: The message given to the user describing the prompt.
    cancel: Whether to include a "cancel" option.

  Returns:
    The membership specified by the user (str), or None if unable to prompt.

  Raises:
    OperationCancelledError if the prompt is cancelled by user
    RequiredArgumentException if the console is unable to prompt
  """
  if not console_io.CanPrompt():
    raise calliope_exceptions.RequiredArgumentException(
        flag, ('Cannot prompt a console for membership. Membership is '
               'required. Please specify `{}` to select at '
               'least one membership.'.format(flag)))
  if memberships is None:
    memberships, unreachable = api_util.ListMembershipsFull()
    if unreachable:
      raise exceptions.Error(
          ('Locations {} are currently unreachable. Please specify '
           'memberships using `--location` or the full resource name '
           '(projects/*/locations/*/memberships/*)').format(unreachable))
  if not memberships:
    raise exceptions.Error('No Memberships available in the fleet.')
  idx = console_io.PromptChoice(
      MembershipPartialNames(memberships),
      message=message,
      cancel_option=cancel)
  return memberships[idx] if idx is not None else None


# For CLI output (e.g. prompts), the LOCATION/ID format
# (e.g. us-central1/my-membership) is more readable than
# the full resource name
def MembershipPartialNames(memberships):
  """Converts a list of full membership names to LOCATION/ID format."""
  return [util.MembershipPartialName(m) for m in memberships]


def _LocationAttributeConfig(help_text=''):
  """Create location attributes in resource argument.

  Args:
    help_text: If set, overrides default help text for `--location`

  Returns:
    Location resource argument parameter config
  """
  fallthroughs = [
      deps.ArgFallthrough('--location'),
      deps.PropertyFallthrough(properties.VALUES.gkehub.location),
  ]
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text=help_text if help_text else ('Location for the {resource}.'),
      fallthroughs=fallthroughs)


def _BasicAttributeConfig(attr_name, help_text=''):
  """Create basic attributes in resource argument.

  Args:
    attr_name: Name of the resource
    help_text: If set, overrides default help text

  Returns:
    Resource argument parameter config
  """
  return concepts.ResourceParameterAttributeConfig(
      name=attr_name,
      help_text=help_text if help_text else ('Name of the {resource}.'))


def AddMembershipResourceArg(parser,
                             api_version='v1',
                             positional=False,
                             plural=False,
                             membership_required=False,
                             flag_override='',
                             membership_help='',
                             location_help=''):
  """Add resource arg for projects/{}/locations/{}/memberships/{}."""
  flag_name = '--membership'
  if flag_override:
    flag_name = flag_override
  elif positional:
    # Flags without '--' prefix are automatically positional
    flag_name = 'MEMBERSHIP_NAME'
  elif plural:
    flag_name = '--memberships'
  spec = concepts.ResourceSpec(
      'gkehub.projects.locations.memberships',
      api_version=api_version,
      resource_name='membership',
      plural_name='memberships',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_LocationAttributeConfig(location_help),
      membershipsId=_BasicAttributeConfig(
          'memberships' if plural else 'membership', membership_help))
  concept_parsers.ConceptParser.ForResource(
      flag_name,
      spec,
      'The group of arguments defining one or more memberships.'
      if plural else 'The group of arguments defining a membership.',
      plural=plural,
      required=membership_required).AddToParser(parser)


def MembershipLocationSpecified(args, flag_override=''):
  """Returns whether a membership location is specified in args."""
  if args.IsSpecified('location'):
    return True
  if args.IsKnownAndSpecified('membership') and _LOCATION_RE.search(
      args.membership) is not None:
    return True
  if args.IsKnownAndSpecified('MEMBERSHIP_NAME') and _LOCATION_RE.search(
      args.MEMBERSHIP_NAME) is not None:
    return True
  if args.IsKnownAndSpecified('memberships') and all(
      [_LOCATION_RE.search(m) is not None for m in args.memberships]):
    return True
  if args.IsKnownAndSpecified(flag_override) and _LOCATION_RE.search(
      args.GetValue(flag_override)) is not None:
    return True
  return False


def SearchMembershipResource(args,
                             flag_override='',
                             filter_cluster_missing=False):
  """Searches the fleet for an ambiguous membership provided in args.

  Only necessary if location is ambiguous, i.e.
  MembershipLocationSpecified(args) is False, or this behavior is necessary for
  backwards compatibility. If flag_override is unset, the argument must be
  called `MEMBERSHIP_NAME` if positional and  `--membership` otherwise. Runs a
  ListMemberships API call to verify the membership exists.

  Args:
    args: arguments provided to a command, including a membership resource arg
    flag_override: a custom membership flag
    filter_cluster_missing: whether to filter out memberships that are missing
    a cluster.

  Returns:
    A membership resource name string
      (e.g. projects/x/locations/y/memberships/z)

  Raises:
    googlecloudsdk.core.exceptions.Error: unable to find the membership
      in the fleet
  """
  if MembershipLocationSpecified(args) and api_util.GetMembership(
      MembershipResourceName(args)):
    return MembershipResourceName(args)
  if args.IsKnownAndSpecified(flag_override):
    arg_membership = getattr(args, flag_override)
  elif args.IsKnownAndSpecified('MEMBERSHIP_NAME'):
    arg_membership = args.MEMBERSHIP_NAME
  elif args.IsKnownAndSpecified('membership'):
    arg_membership = args.membership
  else:
    return None

  all_memberships, unavailable = api_util.ListMembershipsFull(
      filter_cluster_missing=filter_cluster_missing)
  if unavailable:
    raise exceptions.Error(
        ('Locations {} are currently unreachable. Please specify '
         'memberships using `--location` or the full resource name '
         '(projects/*/locations/*/memberships/*)').format(unavailable))
  if not all_memberships:
    raise exceptions.Error('No memberships available in the fleet.')

  # Search all memberships for specified membership
  found = []
  for existing_membership in all_memberships:
    if arg_membership == util.MembershipShortname(existing_membership):
      found.append(existing_membership)
  if not found:
    raise exceptions.Error(
        'Membership {} not found in the fleet.'.format(arg_membership))
  elif len(found) > 1:
    raise AmbiguousMembershipError(arg_membership)
  return found[0]


def SearchMembershipResourcesPlural(args, filter_cluster_missing=False):
  """Searches the fleet for the membership resources provided in args.

  Only necessary if location is ambiguous, i.e.
  MembershipLocationSpecified(args) is
  False. Assumes the argument is called `--membership`, `--memberships` if
  plural, or `MEMBERSHIP_NAME` if positional. Runs ListMemberships API call to
  verify the membership exists.

  Args:
    args: arguments provided to a command, including a membership resource arg
    filter_cluster_missing: whether to filter out memberships that are missing
    a cluster.

  Returns:
    A list of membership resource names
      (e.g. ["projects/x/locations/y/memberships/z"])

  Raises:
    googlecloudsdk.core.exceptions.Error: unable to find a membership
      in the fleet
  """
  if args.IsKnownAndSpecified('memberships'):
    arg_memberships = args.memberships
  else:
    return None

  all_memberships, unavailable = api_util.ListMembershipsFull(
      filter_cluster_missing=filter_cluster_missing)
  if unavailable:
    raise exceptions.Error(
        ('Locations [{}] are currently unreachable. Please specify '
         'memberships using `--location` or the full resource name '
         '(projects/*/locations/*/memberships/*)').format(unavailable))
  if not all_memberships:
    raise exceptions.Error('No memberships available in the fleet.')

  memberships = []
  for arg_membership in arg_memberships:
    # Search all memberships for specified membership
    found = []
    for existing_membership in all_memberships:
      if arg_membership == util.MembershipShortname(existing_membership):
        found.append(existing_membership)
    if not found:
      raise exceptions.Error(
          'Membership {} not found in the fleet.'.format(arg_membership))
    elif len(found) > 1:
      raise AmbiguousMembershipError(arg_membership)
    memberships.append(found[0])
  return memberships


def AmbiguousMembershipError(membership):
  return exceptions.Error(
      ('Multiple memberships named {} found in the fleet. Please use '
       '`--location` or full resource name '
       '(projects/*/locations/*/memberships/*) to specify.').format(membership))


def MembershipResourceName(args, flag_override=''):
  """Gets a membership resource name from a membership resource argument.

  If flag_override is unset, the argument must be `MEMBERSHIP_NAME` if
  positional and `--membership` otherwise.

  Args:
    args: arguments provided to a command, including a membership resource arg
    flag_override: a custom membership flag name

  Returns:
    The membership resource name (e.g. projects/x/locations/y/memberships/z)
  """
  if args.IsKnownAndSpecified(flag_override):
    return args.CONCEPTS.GetValue(flag_override).Parse().RelativeName()
  if args.IsKnownAndSpecified('MEMBERSHIP_NAME'):
    return args.CONCEPTS.membership_name.Parse().RelativeName()
  return args.CONCEPTS.membership.Parse().RelativeName()


def PluralMembershipsResourceNames(args):
  """Gets a list of membership resource names from a --memberships resource arg.

  Args:
    args: arguments provided to a command, including a plural memberships
      resource arg

  Returns:
    A list of membership resource names (e.g.
    projects/x/locations/y/memberships/z)
  """
  return [m.RelativeName() for m in args.CONCEPTS.memberships.Parse()]


def UseRegionalMemberships(track=None):
  """Returns whether regional memberships should be included.

  This will be updated as regionalization is released, and eventually deleted
  when it is fully rolled out.

  Args:
    track: The release track of the command

  Returns:
    A bool, whether regional memberships are supported for the release track in
    the active environment
  """
  return (track is calliope_base.ReleaseTrack.ALPHA) and (
      cmd_util.APIEndpoint() == cmd_util.AUTOPUSH_API)


def InProdRegionalAllowlist(project, track=None):
  """Returns whether project is allowlisted for regional memberships in Prod.

  This will be updated as regionalization is released, and eventually deleted
  when it is fully rolled out.

  Args:
     project: The parent project ID of the membership
    track: The release track of the command

  Returns:
    A bool, whether project is allowlisted for regional memberships in Prod
  """
  prod_regional_allowlist = [
      'gkeconnect-prober',
      'gkeconnect-e2e',
      'gkehub-cep-test',
      'connectgateway-gke-testing',
      'xuebinz-gke',
      'kolber-anthos-testing',
      'anthonytong-hub2',
      'wenjuntoy2',
      'hub-regionalisation-test',  # For Cloud Console UI testing.
      'hub-regionalisation-test-2',  # For Cloud Console UI testing.
      'a4vm-ui-tests-3',  # For Cloud Console UI testing.
      'm4a-ui-playground-1',  # For Cloud Console UI testing.
      'anthos-cl-e2e-tests',
      'a4vm-ui-playground',
      'm4a-ui-playground-1',
  ]
  return track is calliope_base.ReleaseTrack.ALPHA and (
      project in prod_regional_allowlist)


def GetMembershipProjects(memberships):
  """Returns all unique project identifiers of the given membership names.

  ListMemberships should use the same identifier (all number or all ID) in
  membership names. Users can convert their own project identifiers for manually
  entering arguments.

  Args:
    memberships: A list of full membership resource names

  Returns:
    A list of project identifiers in the parents of the memberships

  Raises: googlecloudsdk.core.exceptions.Error if unable to parse any membership
  name
  """
  projects = set()
  for m in memberships:
    match = re.match(r'projects\/(.*)\/locations\/(.*)\/memberships\/(.*)', m)
    if not match:
      raise exceptions.Error('Unable to parse membership {} (expected '
                             'projects/*/locations/*/memberships/*)'.format(m))
    projects.add(match.group(1))
  return list(projects)


def ParseMembershipArg(args, membership_flag='MEMBERSHIP_NAME'):
  """Returns a membership on which to run the command, given the arguments.

  This function is currently only used by the unregister command. This logic
  should be combined with the feature ParseMembership function in a later CL.
  Allows for `MEMBERSHIP_NAME` positional flag.

  Args:
    args: object containing arguments passed as flags with the command
    membership_flag: the membership flag used to pass in the memberhip resource

  Returns:
    membership: A membership resource name string

  Raises:
    exceptions.Error: no memberships were found or memberships are invalid
    calliope_exceptions.RequiredArgumentException: membership was not provided
  """

  # If a membership is provided (positional arg)
  if args.IsKnownAndSpecified(membership_flag):
    if MembershipLocationSpecified(args):
      return MembershipResourceName(args)
    else:
      return SearchMembershipResource(args)

  raise calliope_exceptions.RequiredArgumentException(
      membership_flag, 'membership is required for this command.')


def _DefaultToGlobalLocationAttributeConfig(help_text=''):
  """Create basic attributes that fallthrough location to global in resource argument.

  Args:
    help_text: If set, overrides default help text

  Returns:
    Resource argument parameter config
  """
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      fallthroughs=[
          deps.Fallthrough(
              function=cmd_util.DefaultToGlobal,
              hint='global is the only supported location',
          )
      ],
      help_text=help_text if help_text else ('Name of the {resource}.'),
  )


def AddScopeResourceArg(
    parser,
    flag_name='NAME',
    api_version='v1',
    scope_help='',
    required=False,
    group=None,
):
  """Add resource arg for projects/{}/locations/{}/scopes/{}."""
  spec = concepts.ResourceSpec(
      'gkehub.projects.locations.scopes',
      api_version=api_version,
      resource_name='scope',
      plural_name='scopes',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_DefaultToGlobalLocationAttributeConfig(),
      scopesId=_BasicAttributeConfig('scope', scope_help),
  )
  concept_parsers.ConceptParser.ForResource(
      flag_name,
      spec,
      'The group of arguments defining the Fleet Scope.',
      plural=False,
      required=required,
      group=group,
      # This hides the location flag as we only allow global scope.
      flag_name_overrides={'location': ''},
  ).AddToParser(parser)


def AddScopeNamespaceResourceArg(
    parser,
    flag_name='NAMESPACE',
    api_version='v1',
    namespace_help='',
    required=False,
):
  """Add resource arg for projects/{}/locations/{}/scopes/{}/namespaces/{}."""
  spec = concepts.ResourceSpec(
      'gkehub.projects.locations.scopes.namespaces',
      api_version=api_version,
      resource_name='namespace',
      plural_name='namespaces',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_DefaultToGlobalLocationAttributeConfig(),
      scopesId=_BasicAttributeConfig('scope', 'the'),
      namespacesId=_BasicAttributeConfig('namespace', namespace_help),
  )
  concept_parsers.ConceptParser.ForResource(
      flag_name,
      spec,
      'The group of arguments defining the Fleet Namespace.',
      plural=False,
      required=required,
      # This hides the location flag as we only allow global scope.
      flag_name_overrides={'location': ''},
  ).AddToParser(parser)


def AddScopeRBACResourceArg(parser, api_version='v1', rbacrb_help=''):
  """Add resource arg for projects/{}/locations/{}/scopes/{}/rbacrolebindings/{}."""
  # Flags without '--' prefix are automatically positional
  flag_name = 'NAME'
  spec = concepts.ResourceSpec(
      'gkehub.projects.locations.scopes.rbacrolebindings',
      api_version=api_version,
      resource_name='rbacrolebinding',
      plural_name='rbacrolebindings',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_LocationAttributeConfig(),
      scopesId=_BasicAttributeConfig('scope', ''),
      rbacrolebindingsId=_BasicAttributeConfig('rbacrolebinding', rbacrb_help),
  )
  concept_parsers.ConceptParser.ForResource(
      flag_name,
      spec,
      'The group of arguments defining an RBACRoleBinding.',
      plural=False,
      required=True,
  ).AddToParser(parser)


def AddRBACResourceArg(parser, api_version='v1', rbacrb_help=''):
  """Add resource arg for projects/{}/locations/{}/memberships/{}."""
  # Flags without '--' prefix are automatically positional
  flag_name = 'NAME'
  spec = concepts.ResourceSpec(
      'gkehub.projects.locations.namespaces.rbacrolebindings',
      api_version=api_version,
      resource_name='rbacrolebinding',
      plural_name='rbacrolebindings',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_LocationAttributeConfig(),
      namespacesId=_BasicAttributeConfig('namespace', ''),
      rbacrolebindingsId=_BasicAttributeConfig('rbacrolebinding', rbacrb_help))
  concept_parsers.ConceptParser.ForResource(
      flag_name,
      spec,
      'The group of arguments defining an RBACRoleBinding.',
      plural=False,
      required=True).AddToParser(parser)


def AddUpdateNamespaceLabelsFlags(parser):
  """Adds flags to an argparse parser for updating namespace labels.

  Args:
    parser: The argparse parser to add the flags to.
  """
  _GetUpdateNamespaceLabelsFlag('namespace').AddToParser(parser)
  remove_group = parser.add_mutually_exclusive_group()
  _GetClearNamespaceLabelsFlag('namespace').AddToParser(
      remove_group
  )
  _GetRemoveNamespaceLabelsFlag('namespace').AddToParser(remove_group)


def UpdateScopeLabelsFlags():
  remove_group = calliope_base.ArgumentGroup(mutex=True)
  remove_group.AddArgument(
      _GetClearNamespaceLabelsFlag('scope')
  )
  remove_group.AddArgument(
      _GetRemoveNamespaceLabelsFlag('scope')
  )
  return [
      _GetUpdateNamespaceLabelsFlag('scope'),
      remove_group,
  ]


def AddCreateNamespaceLabelsFlags(parser):
  """Adds flags to an argparse parser for creating namespace labels.

  Args:
    parser: The argparse parser to add the flags to.
  """
  _GetCreateNamespaceLabelsFlag('namespace').AddToParser(parser)


def CreateScopeLabelsFlags():
  return [_GetCreateNamespaceLabelsFlag('scope')]


def _GetClearNamespaceLabelsFlag(resource_type):
  labels_name = 'namespace-labels'
  return calliope_base.Argument(
      '--clear-{}'.format(labels_name),
      action='store_true',
      help="""\
          Remove all {resource_type}-level labels from the cluster namespace. If `--update-{labels}` is also specified then
          `--clear-{labels}` is applied first.

          For example, to remove all labels:

              $ {{command}} {resource_type}_name --clear-{labels}

          To remove all existing {resource_type}-level labels and create two new labels,
          ``foo'' and ``baz'':

              $ {{command}} {resource_type}_name --clear-{labels} --update-{labels} foo=bar,baz=qux
          """.format(labels=labels_name, resource_type=resource_type))


def _GetRemoveNamespaceLabelsFlag(resource_type):
  labels_name = 'namespace-labels'
  return calliope_base.Argument(
      '--remove-{}'.format(labels_name),
      metavar='KEY',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help="""\
      List of {resource_type}-level label keys to remove in the cluster namespace. If a label does not exist it is
      silently ignored. If `--update-{labels}` is also specified then
      `--update-{labels}` is applied first.
      """.format(labels=labels_name, resource_type=resource_type))


def _GetUpdateNamespaceLabelsFlag(resource_type):
  """Makes a base.Argument for the `--update-namespace-labels` flag."""
  labels_name = 'namespace-labels'
  return calliope_base.Argument(
      '--update-{}'.format(labels_name),
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help="""\
      List of {resource_type}-level label KEY=VALUE pairs to update in the cluster namespace. If a
      label exists, its value is modified. Otherwise, a new label is'
      created.""".format(resource_type=resource_type))


def _GetCreateNamespaceLabelsFlag(resource_type):
  labels_name = 'namespace-labels'
  return calliope_base.Argument(
      '--{}'.format(labels_name),
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help="""\
      List of {resource_type}-level label KEY=VALUE pairs to add.
      """.format(resource_type=resource_type))


def RBACResourceName(args):
  """Gets an RBACRoleBinding resource name from a resource argument.

  Assumes the argument is called NAME.

  Args:
    args: arguments provided to a command, including an rbacRB resource arg

  Returns:
    The rbacRB resource name (e.g.
    projects/x/locations/global/namespaces/y/rbacrolebindings/z
    projects/x/locations/global/scopes/y/rbacrolebindings/z)
  """
  return args.CONCEPTS.name.Parse().RelativeName()


def AddMembershipBindingResourceArg(parser, api_version='v1', binding_help=''):
  """Add resource arg for projects/{}/locations/{}/memberships/{}/bindings/{}."""
  # Flags without '--' prefix are automatically positional
  flag_name = 'BINDING'
  spec = concepts.ResourceSpec(
      'gkehub.projects.locations.memberships.bindings',
      api_version=api_version,
      resource_name='binding',
      plural_name='bindings',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_LocationAttributeConfig(),
      membershipsId=_BasicAttributeConfig('membership', ''),
      bindingsId=_BasicAttributeConfig('binding', binding_help))
  concept_parsers.ConceptParser.ForResource(
      flag_name,
      spec,
      'The group of arguments defining a Membership Binding.',
      plural=False,
      required=True).AddToParser(parser)


def MembershipBindingResourceName(args):
  """Gets a Membership-Binding resource name from a resource argument.

  Assumes the argument is called BINDING.

  Args:
    args: arguments provided to a command, including a Binding resource arg

  Returns:
    The Binding resource name (e.g.
    projects/x/locations/l/memberships/y/bindings/z)
  """
  return args.CONCEPTS.binding.Parse().RelativeName()


def AddRolloutResourceArg(parser, api_version='v1'):
  """Add resource arg for projects/{}/locations/{}/rollouts/{}."""
  # Flags without '--' prefix are automatically positional
  spec = concepts.ResourceSpec(
      'gkehub.projects.locations.rollouts',
      api_version=api_version,
      resource_name='rollout',
      plural_name='rollouts',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_DefaultToGlobalLocationAttributeConfig(),
      rolloutsId=_BasicAttributeConfig('rollout'),
  )
  concept_parsers.ConceptParser.ForResource(
      name='rollout',
      resource_spec=spec,
      group_help='The group of arguments defining a Fleet Rollout.',
      plural=False,
      required=True,
      # This hides the location flag as we only allow global scope.
      flag_name_overrides={'location': ''},
  ).AddToParser(parser)
