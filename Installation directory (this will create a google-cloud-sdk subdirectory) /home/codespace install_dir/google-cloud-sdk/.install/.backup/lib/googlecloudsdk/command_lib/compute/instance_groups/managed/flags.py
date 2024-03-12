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
"""Flags for the compute instance groups managed commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import re
from typing import Any

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util.apis import arg_utils

INSTANCE_TEMPLATE_ARG = compute_flags.ResourceArgument(
    '--template',
    resource_name='instance template',
    required=True,
    plural=False,
    scope_flags_usage=compute_flags.ScopeFlagsUsage.DONT_USE_SCOPE_FLAGS,
    global_collection='compute.instanceTemplates',
    regional_collection='compute.regionInstanceTemplates',
    short_help="""
    Specifies the instance template to use when creating new instances.
    An instance template is either a global or regional resource.
    """,
)

DEFAULT_CREATE_OR_LIST_FORMAT = """\
    table(
      name,
      location():label=LOCATION,
      location_scope():label=SCOPE,
      baseInstanceName,
      size,
      targetSize,
      instanceTemplate.basename(),
      autoscaled
    )
"""


def AddTypeArg(parser):
  parser.add_argument(
      '--type',
      choices={
          'opportunistic':
              'Do not proactively replace VMs. Create new VMs and delete old '
              'ones on resizes of the group and when you target specific VMs '
              'to be updated or recreated.',
          'proactive': 'Replace instances proactively.',
      },
      default='proactive',
      category=base.COMMONLY_USED_FLAGS,
      help='Desired update type.')


def AddMaxSurgeArg(parser):
  parser.add_argument(
      '--max-surge',
      type=str,
      help=('Maximum additional number of instances that '
            'can be created during the update process. '
            'This can be a fixed number (e.g. 5) or '
            'a percentage of size to the managed instance '
            'group (e.g. 10%). Defaults to 0 if the managed '
            'instance group has stateful configuration, or to '
            'the number of zones in which it operates otherwise.'))


def AddMaxUnavailableArg(parser):
  parser.add_argument(
      '--max-unavailable',
      type=str,
      help=('Maximum number of instances that can be '
            'unavailable during the update process. '
            'This can be a fixed number (e.g. 5) or '
            'a percentage of size to the managed instance '
            'group (e.g. 10%). Defaults to the number of zones '
            'in which the managed instance group operates.'))


def AddMinReadyArg(parser):
  parser.add_argument(
      '--min-ready',
      type=arg_parsers.Duration(lower_bound='0s'),
      help=('Minimum time for which a newly created instance '
            'should be ready to be considered available. For example `10s` '
            'for 10 seconds. See $ gcloud topic datetimes for information '
            'on duration formats.'))


def AddReplacementMethodFlag(parser):
  parser.add_argument(
      '--replacement-method',
      choices={
          'substitute':
              'Delete old instances and create instances with new names.',
          'recreate':
              'Recreate instances and preserve the instance names. '
              'The instance IDs and creation timestamps might change.',
      },
      help='Type of replacement method. Specifies what action will be taken '
      'to update instances. Defaults to ``recreate`` if the managed instance '
      'group has stateful configuration, or to ``substitute`` otherwise.')


def AddForceArg(parser):
  parser.add_argument(
      '--force',
      action='store_true',
      help=('If set, accepts any original or new version '
            'configurations without validation.'))


def InstanceActionChoicesWithoutNone(flag_prefix=''):
  """Return possible instance action choices without NONE value."""
  return collections.OrderedDict([
      ('refresh',
       ('Apply the new configuration without stopping VMs, if possible. For '
        'example, use ``refresh`` to apply changes that only affect metadata '
        'or additional disks.')),
      ('restart',
       ('Apply the new configuration without replacing VMs, if possible. For '
        'example, stopping VMs and starting them again is sufficient to apply '
        'changes to machine type.')),
      ('replace', ('Replace old VMs according to the '
                   '--{flag_prefix}replacement-method flag.').format(
                       flag_prefix=flag_prefix))
  ])


def InstanceActionChoicesWithNone(flag_prefix=''):
  """Return possible instance action choices with NONE value."""
  return _CombineOrderedChoices({'none': 'No action'},
                                InstanceActionChoicesWithoutNone(flag_prefix))


def _CombineOrderedChoices(choices1, choices2):
  merged = collections.OrderedDict([])
  merged.update(choices1.items())
  merged.update(choices2.items())
  return merged


def AddMinimalActionArg(parser, choices_with_none=True, default=None):
  choices = (InstanceActionChoicesWithNone() if choices_with_none
             else InstanceActionChoicesWithoutNone())
  parser.add_argument(
      '--minimal-action',
      choices=choices,
      default=default,
      help="""Use this flag to minimize disruption as much as possible or to
        apply a more disruptive action than is strictly necessary.
        The MIG performs at least this action on each instance while
        updating. If the update requires a more disruptive action than
        the one specified here, then the more disruptive action is
        performed. If you omit this flag, the update uses the
        ``minimal-action'' value from the MIG\'s update policy, unless it
        is not set in which case the default is ``replace''.""")


def AddMostDisruptiveActionArg(parser, choices_with_none=True, default=None):
  choices = (InstanceActionChoicesWithNone() if choices_with_none
             else InstanceActionChoicesWithoutNone())
  parser.add_argument(
      '--most-disruptive-allowed-action',
      choices=choices,
      default=default,
      help="""Use this flag to prevent an update if it requires more disruption
        than you can afford. At most, the MIG performs the specified
        action on each instance while updating. If the update requires
        a more disruptive action than the one specified here, then
        the update fails and no changes are made. If you omit this flag,
        the update uses the ``most-disruptive-allowed-action'' value from
        the MIG\'s update policy, unless it is not set in which case
        the default is ``replace''.""")


def AddUpdateInstancesArgs(parser):
  """Add args for the update-instances command."""
  instance_selector_group = parser.add_group(required=True, mutex=True)
  instance_selector_group.add_argument(
      '--instances',
      type=arg_parsers.ArgList(min_length=1),
      metavar='INSTANCE',
      required=False,
      help='Names of instances to update.')
  instance_selector_group.add_argument(
      '--all-instances',
      required=False,
      action='store_true',
      help='Update all instances in the group.')
  AddMinimalActionArg(parser, True, 'none')
  AddMostDisruptiveActionArg(parser, True, 'replace')


def AddGracefulValidationArg(parser):
  help_text = """Specifies whether the request should proceed even if the
    request includes instances that are not members of the group or that are
    already being deleted or abandoned. By default, if you omit this flag and
    such an instance is specified in the request, the operation fails. The
    operation always fails if the request contains a badly formatted instance
    name or a reference to an instance that exists in a zone or region other
    than the group's zone or region."""
  parser.add_argument(
      '--skip-instances-on-validation-error',
      action='store_true',
      help=help_text)


def GetCommonPerInstanceCommandOutputFormat(with_validation_error=False):
  if with_validation_error:
    return """
        table(project(),
              zone(),
              instanceName:label=INSTANCE,
              status,
              validationError:label=VALIDATION_ERROR)"""
  else:
    return """
        table(project(),
              zone(),
              instanceName:label=INSTANCE,
              status)"""


INSTANCE_REDISTRIBUTION_TYPES = ['NONE', 'PROACTIVE']


def AddMigUpdatePolicyFlags(parser, support_min_ready_flag=False):
  """Add flags required for setting update policy attributes."""
  group = parser.add_group(
      required=False,
      mutex=False,
      help='Parameters for setting update policy for this managed instance '
           'group.'
  )
  _AddUpdatePolicyTypeFlag(group)
  _AddUpdatePolicyMaxUnavailableFlag(group)
  _AddUpdatePolicyMaxSurgeFlag(group)
  _AddUpdatePolicyMinimalActionFlag(group)
  _AddUpdatePolicyMostDisruptiveActionFlag(group)
  _AddUpdatePolicyReplacementMethodFlag(group)
  if support_min_ready_flag:
    _AddUpdatePolicyMinReadyFlag(group)


def _AddUpdatePolicyTypeFlag(group):
  """Add --update-policy-type flag to the parser."""
  help_text = ('Specifies the type of update process. You can specify either '
               '``proactive`` so that the managed instance group proactively '
               'executes actions in order to bring VMs to their target '
               'versions or ``opportunistic`` so that no action is '
               'proactively executed but the update will be performed as part '
               'of other actions.')
  choices = {
      'opportunistic':
          'Do not proactively replace VMs. Create new VMs and delete old ones '
          'on resizes of the group and when you target specific VMs to be '
          'updated or recreated.',
      'proactive': 'Replace VMs proactively.',
  }
  group.add_argument(
      '--update-policy-type',
      metavar='UPDATE_TYPE',
      type=lambda x: x.lower(),
      choices=choices,
      help=help_text)


def _AddUpdatePolicyMaxUnavailableFlag(group):
  group.add_argument(
      '--update-policy-max-unavailable',
      metavar='MAX_UNAVAILABLE',
      type=str,
      help=('Maximum number of VMs that can be unavailable during the update '
            'process. This can be a fixed number (e.g. 5) or a percentage of '
            'size to the managed instance group (e.g. 10%). Defaults to the '
            'number of zones in which the managed instance group operates.'))


def _AddUpdatePolicyMaxSurgeFlag(group):
  group.add_argument(
      '--update-policy-max-surge',
      metavar='MAX_SURGE',
      type=str,
      help=(
          'Maximum additional number of VMs that can be created during the '
          'update process. This can be a fixed number (e.g. 5) or a percentage '
          'of size to the managed instance group (e.g. 10%).'))


def _AddUpdatePolicyMinReadyFlag(group):
  group.add_argument(
      '--update-policy-min-ready',
      metavar='MIN_READY',
      type=arg_parsers.Duration(lower_bound='0s'),
      help=('Minimum time for which a newly created VM should be ready to be '
            'considered available. For example `10s` for 10 seconds. See '
            '$ gcloud topic datetimes for information on duration formats.'))


def _AddUpdatePolicyMinimalActionFlag(group):
  group.add_argument(
      '--update-policy-minimal-action',
      choices=InstanceActionChoicesWithNone(flag_prefix='update-policy-'),
      help=('Use this flag to minimize disruption as much as possible or to '
            'apply a more disruptive action than is strictly necessary. '
            'The MIG performs at least this action on each VM while '
            'updating. If the update requires a more disruptive action than '
            'the one specified here, then the more disruptive action is '
            'performed. '))


def _AddUpdatePolicyMostDisruptiveActionFlag(group):
  group.add_argument(
      '--update-policy-most-disruptive-action',
      choices=InstanceActionChoicesWithNone(flag_prefix='update-policy-'),
      help=('Use this flag to prevent an update if it requires more disruption '
            'than you can afford. At most, the MIG performs the specified '
            'action on each VM while updating. If the update requires '
            'a more disruptive action than the one specified here, then '
            'the update fails and no changes are made.'))


def _AddUpdatePolicyReplacementMethodFlag(group):
  group.add_argument(
      '--update-policy-replacement-method',
      choices={
          'substitute': 'Delete old VMs and create VMs with new names.',
          'recreate': 'Recreate VMs and preserve the VM names. '
                      'The VM IDs and creation timestamps might change.',
      },
      help=('Type of replacement method. Specifies what action will be taken '
            'to update VMs.'))


def AddMigInstanceRedistributionTypeFlag(parser):
  """Add --instance-redistribution-type flag to the parser."""
  help_text = """\
      Specifies the type of the instance redistribution policy. An instance
      redistribution type lets you enable or disable automatic instance
      redistribution across zones to meet the group's target distribution shape.

      An instance redistribution type can be specified only for a non-autoscaled
      regional managed instance group. By default it is set to ``proactive''.
      """
  choices = {
      'none':
          'The managed instance group does not redistribute instances across '
          'zones.',
      'proactive':
          'The managed instance group proactively redistributes instances to '
          'meet its target distribution.'
  }

  parser.add_argument(
      '--instance-redistribution-type',
      metavar='TYPE',
      type=lambda x: x.lower(),
      choices=choices,
      help=help_text)


def AddMigDistributionPolicyTargetShapeFlag(parser):
  """Add --target-distribution-shape flag to the parser."""
  help_text = """\
      Specifies how a regional managed instance group distributes its instances
      across zones within the region. The default shape is ``even''.
    """
  choices = {
      'even': (
          'The group schedules VM instance creation and deletion to achieve '
          'and maintain an even number of managed instances across the '
          'selected zones. The distribution is even when the number of managed'
          ' instances does not differ by more than 1 between any two zones. '
          'Recommended for highly available serving workloads.'
      ),
      'balanced': (
          'The group prioritizes acquisition of resources, scheduling VMs in '
          'zones where resources are available while distributing VMs as '
          'evenly as possible across selected zones to minimize the impact of '
          'zonal failure. Recommended for highly available serving or batch '
          'workloads that do not require autoscaling.'
      ),
      'any': (
          'The group picks zones for creating VM instances to fulfill the '
          'requested number of VMs within present resource constraints and to '
          'maximize utilization of unused zonal reservations. Recommended for '
          'batch workloads that do not require high availability.'
      ),
      'any-single-zone': (
          'The group schedules all instances within a single zone. The zone '
          'is chosen based on hardware support, current resources '
          'availability, and matching reservations. The group might not be '
          'able to create the requested number of VMs in case of zonal '
          'resource availability constraints. Recommended for workloads '
          'requiring extensive communication between VMs.'
      ),
  }

  parser.add_argument(
      '--target-distribution-shape',
      metavar='SHAPE',
      type=arg_utils.EnumNameToChoice,
      choices=choices,
      help=help_text)


def AddFlagsForUpdateAllInstancesConfig(parser):
  """Adds args for all-instances' config update command."""
  # Add  metadata args
  metadata_argument_name = '--metadata'
  metadata_help_text = ("Add metadata to the group's all instances "
                        "configuration.")
  parser.add_argument(
      metadata_argument_name,
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      action=arg_parsers.StoreOnceAction,
      metavar='KEY=VALUE',
      help=metadata_help_text)
  # Add labels args
  labels_argument_name = '--labels'
  metadata_help_text = "Add labels to the group's all instances configuration."
  parser.add_argument(
      labels_argument_name,
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      action=arg_parsers.StoreOnceAction,
      metavar='KEY=VALUE',
      help=metadata_help_text)


def AddFlagsForDeleteAllInstancesConfig(parser):
  """Adds args for all-instances' config delete command."""
  # Add  metadata args
  metadata_argument_name = '--metadata'
  parser.add_argument(
      metadata_argument_name,
      metavar='KEY',
      type=arg_parsers.ArgList(min_length=1),
      help="Remove metadata keys from the group's all instances configuration."
  )
  # Add labels args
  labels_argument_name = '--labels'
  parser.add_argument(
      labels_argument_name,
      metavar='KEY',
      type=arg_parsers.ArgList(min_length=1),
      help="Remove labels keys from the group's all instances configuration.")


def ValidateRegionalMigFlagsUsage(args, regional_flags_dests, igm_ref):
  """For zonal MIGs validate that user did not supply any RMIG-specific flags.

  Can be safely called from GA track for all flags, unknowns are ignored.

  Args:
    args: provided arguments.
    regional_flags_dests: list of RMIG-specific flag dests (names of the
      attributes used to store flag values in args).
    igm_ref: resource reference of the target IGM.
  """
  if igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
    return
  for dest in regional_flags_dests:
    if args.IsKnownAndSpecified(dest):
      flag_name = args.GetFlag(dest)
      error_message = ('Flag %s may be specified for regional managed instance '
                       'groups only.') % flag_name
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name, message=error_message)


def AddMigListManagedInstancesResultsFlag(parser):
  """Add --list-managed-instances-results flag to the parser."""
  help_text = """\
      Pagination behavior for the group's listManagedInstances API method.
      This flag does not affect the group's gcloud or console list-instances
      behavior. By default it is set to ``pageless''.
    """
  choices = {
      'pageless':
          'Pagination is disabled for the group\'s listManagedInstances API '
          'method. maxResults and pageToken query parameters are ignored and '
          'all instances are returned in a single response.',
      'paginated':
          'Pagination is enabled for the group\'s listManagedInstances API '
          'method. maxResults and pageToken query parameters are respected.',
  }

  parser.add_argument(
      '--list-managed-instances-results',
      metavar='MODE',
      type=lambda x: x.lower(),
      choices=choices,
      help=help_text)


def AddMigForceUpdateOnRepairFlags(parser):
  """Adding force update on repair flag to the parser."""
  help_text = """
      Specifies whether to apply the group's latest configuration when
      repairing a VM. If you updated the group's instance template or
      per-instance configurations after the VM was created, then these changes
      are applied when VM is repaired. If this flag is disabled with
      ``-no-force-update-on-repair'', then updates are applied in accordance
      with the group's update policy type. By default, this flag is disabled.
    """
  parser.add_argument(
      '--force-update-on-repair',
      action=arg_parsers.StoreTrueFalseAction,
      help=help_text)


def AddMigDefaultActionOnVmFailure(parser):
  """Add default action on VM failure to the parser."""
  help_text = """\
      Specifies the action that a MIG performs on a failed or an unhealthy VM.
      A VM is marked as unhealthy when the application running on that VM
      fails a health check.
      By default, the value of the flag is set to ``repair''."""
  choices = {
      'repair':
          'MIG automatically repairs a failed or an unhealthy VM.',
      'do-nothing':
          'MIG does not repair a failed or an unhealthy VM.',
  }

  parser.add_argument(
      '--default-action-on-vm-failure',
      metavar='ACTION_ON_VM_FAILURE',
      type=arg_utils.EnumNameToChoice,
      choices=choices,
      help=help_text)


def AddStandbyPolicyFlags(parser):
  """Add flags required for setting standby policy."""
  standby_policy_mode_choices = {
      'manual': (
          'MIG does not automatically resume or start VMs in the standby pool'
          ' when the group scales out.'
      ),
      'scale-out-pool': (
          'MIG automatically resumes or starts VMs in the standby pool when the'
          ' group scales out, and replenishes the standby pool afterwards.'
      ),
  }
  parser.add_argument(
      '--standby-policy-mode',
      type=str,
      choices=standby_policy_mode_choices,
      help=("""\
          Defines how a MIG resumes or starts VMs from a standby pool when the\
          group scales out. The default mode is ``manual''.
      """),
  )
  parser.add_argument(
      '--standby-policy-initial-delay',
      type=int,
      help=(
          'Specifies the number of seconds that the MIG should wait before'
          ' suspending or stopping a VM. The initial delay gives the'
          ' initialization script the time to prepare your VM for a quick scale'
          ' out.'
      ),
  )
  parser.add_argument(
      '--suspended-size',
      type=int,
      help='Specifies the target size of suspended VMs in the group.',
  )
  parser.add_argument(
      '--stopped-size',
      type=int,
      help='Specifies the target size of stopped VMs in the group.',
  )


def AddMigResourceManagerTagsFlags(parser):
  """Adds resource manager tag related flags."""
  parser.add_argument(
      '--resource-manager-tags',
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE',
      action=arg_parsers.UpdateAction,
      help="""\
      Specifies a list of resource manager tags to apply to the managed instance group.
      """,
  )


def AddInstanceFlexibilityPolicyArgs(
    parser: Any,
) -> None:
  """Adds instance flexibility policy args."""
  parser.add_argument(
      '--instance-selection-machine-types',
      type=arg_parsers.ArgList(),
      metavar='MACHINE_TYPE',
      help=(
          'Primary machine types to use for the Compute Engine instances that'
          ' will be created with the managed instance group. If not provided,'
          ' machine type specified in the instance template will be used.'
      ),
  )
  parser.add_argument(
      '--instance-selection',
      help=(
          'Named selection of machine types with an optional rank. '
          'eg. --instance-selection="name=instance-selection-1,machine-type=e2-standard-8,machine-type=t2d-standard-8,rank=0"'
      ),
      metavar='name=NAME,machine-type=MACHINE_TYPE[,machine-type=MACHINE_TYPE...][,rank=RANK]',
      type=ArgMultiValueDict(),
      action=arg_parsers.FlattenAction(),
  )


class ArgMultiValueDict:
  """Converts argument values into multi-valued mappings.

  Values for the repeated keys are collected in a list.
  """

  def __init__(self):
    ops = '='
    key_op_value_pattern = '([^{ops}]+)([{ops}]?)(.*)'.format(ops=ops)
    self._key_op_value = re.compile(key_op_value_pattern, re.DOTALL)

  def __call__(self, arg_value):
    arg_list = [item.strip() for item in arg_value.split(',')]
    arg_dict = collections.OrderedDict()
    for arg in arg_list:
      match = self._key_op_value.match(arg)
      if not match:
        raise arg_parsers.ArgumentTypeError(
            'Invalid flag value [{0}]'.format(arg)
        )
      key, _, value = (
          match.group(1).strip(),
          match.group(2),
          match.group(3).strip(),
      )
      arg_dict.setdefault(key, []).append(value)
    return arg_dict
