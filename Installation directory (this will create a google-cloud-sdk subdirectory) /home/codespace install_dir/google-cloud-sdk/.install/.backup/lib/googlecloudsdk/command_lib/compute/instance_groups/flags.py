# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute instance groups commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
import textwrap
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups.managed import flags as mig_flags
from googlecloudsdk.command_lib.util import completers
import six


STATEFUL_IP_DEFAULT_INTERFACE_NAME = 'nic0'


class RegionalInstanceGroupManagersCompleter(
    compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RegionalInstanceGroupManagersCompleter, self).__init__(
        collection='compute.regionInstanceGroupManagers',
        list_command=('compute instance-groups managed list --uri '
                      '--filter=region:*'),
        **kwargs)


class ZonalInstanceGroupManagersCompleter(
    compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ZonalInstanceGroupManagersCompleter, self).__init__(
        collection='compute.instanceGroupManagers',
        list_command=('compute instance-groups managed list --uri '
                      '--filter=zone:*'),
        **kwargs)


class InstanceGroupManagersCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(InstanceGroupManagersCompleter, self).__init__(
        completers=[RegionalInstanceGroupManagersCompleter,
                    ZonalInstanceGroupManagersCompleter],
        **kwargs)


class AutoDeleteFlag(enum.Enum):
  """CLI flag values for `auto-delete' flag."""

  NEVER = 'never'
  ON_PERMANENT_INSTANCE_DELETION = 'on-permanent-instance-deletion'

  def GetAutoDeleteEnumValue(self, base_enum):
    return base_enum(self.name)

  @staticmethod
  def ValidateAutoDeleteFlag(flag_value, flag_name):
    values = [
        auto_delete_flag_value.value
        for auto_delete_flag_value in AutoDeleteFlag
    ]
    if flag_value not in values:
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='Value for [auto-delete] must be [never] or '
          '[on-permanent-instance-deletion], not [{0}]'.format(flag_value))
    return AutoDeleteFlag(flag_value)

  @staticmethod
  def ValidatorWithFlagName(flag_name):
    def Validator(flag_value):
      return AutoDeleteFlag.ValidateAutoDeleteFlag(flag_value, flag_name)
    return Validator


def MakeZonalInstanceGroupArg(plural=False):
  return flags.ResourceArgument(
      resource_name='instance group',
      completer=compute_completers.InstanceGroupsCompleter,
      plural=plural,
      zonal_collection='compute.instanceGroups',
      zone_explanation=flags.ZONE_PROPERTY_EXPLANATION)


def MakeZonalInstanceGroupManagerArg(plural=False):
  return flags.ResourceArgument(
      name='INSTANCE_GROUP_MANAGER',
      resource_name='managed instance group',
      completer=ZonalInstanceGroupManagersCompleter,
      plural=plural,
      zonal_collection='compute.instanceGroupManagers',
      zone_explanation=flags.ZONE_PROPERTY_EXPLANATION)

MULTISCOPE_INSTANCE_GROUP_ARG = flags.ResourceArgument(
    resource_name='instance group',
    completer=compute_completers.InstanceGroupsCompleter,
    zonal_collection='compute.instanceGroups',
    regional_collection='compute.regionInstanceGroups',
    zone_explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT,
    region_explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)

MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG = flags.ResourceArgument(
    resource_name='managed instance group',
    completer=InstanceGroupManagersCompleter,
    zonal_collection='compute.instanceGroupManagers',
    regional_collection='compute.regionInstanceGroupManagers',
    zone_explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT,
    region_explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)

MULTISCOPE_INSTANCE_GROUP_MANAGERS_ARG = flags.ResourceArgument(
    resource_name='managed instance group',
    plural=True,
    name='names',
    completer=InstanceGroupManagersCompleter,
    zonal_collection='compute.instanceGroupManagers',
    regional_collection='compute.regionInstanceGroupManagers',
    zone_explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT,
    region_explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)


def AddGroupArg(parser):
  parser.add_argument(
      'group',
      help='The name of the instance group.')


def AddNamedPortsArgs(parser):
  """Adds flags for handling named ports."""
  parser.add_argument(
      '--named-ports',
      required=True,
      type=arg_parsers.ArgList(),
      metavar='NAME:PORT',
      help="""\
          The comma-separated list of key:value pairs representing
          the service name and the port that it is running on.

          To clear the list of named ports pass empty list as flag value.
          For example:

            $ {command} example-instance-group --named-ports ""
          """)


def AddScopeArgs(parser, multizonal):
  """Adds flags for group scope."""
  if multizonal:
    scope_parser = parser.add_mutually_exclusive_group()
    flags.AddRegionFlag(
        scope_parser,
        resource_type='instance group',
        operation_type='set named ports for',
        explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
    flags.AddZoneFlag(
        scope_parser,
        resource_type='instance group',
        operation_type='set named ports for',
        explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)
  else:
    flags.AddZoneFlag(
        parser,
        resource_type='instance group',
        operation_type='set named ports for')


def AddZonesFlag(parser):
  """Add flags for choosing zones for regional managed instance group."""
  parser.add_argument(
      '--zones',
      metavar='ZONE',
      help="""\
          If this flag is specified a regional managed instance group will be
          created. The managed instance group will be in the same region as
          specified zones and will spread instances in it between specified
          zones.

          All zones must belong to the same region. You may specify --region
          flag but it must be the region to which zones belong. This flag is
          mutually exclusive with --zone flag.""",
      type=arg_parsers.ArgList(min_length=1),
      completer=compute_completers.ZonesCompleter,
      default=[])


def ValidateManagedInstanceGroupScopeArgs(args, resources):
  """Validate arguments specifying scope of the managed instance group."""
  ignored_required_params = {'project': 'fake'}
  if args.zones and args.zone:
    raise exceptions.ConflictingArgumentsException('--zone', '--zones')
  zone_names = []
  for zone in args.zones:
    zone_ref = resources.Parse(
        zone, collection='compute.zones', params=ignored_required_params)
    zone_names.append(zone_ref.Name())

  zone_regions = set([utils.ZoneNameToRegionName(z) for z in zone_names])
  if len(zone_regions) > 1:
    raise exceptions.InvalidArgumentException(
        '--zones', 'All zones must be in the same region.')
  elif len(zone_regions) == 1 and args.region:
    zone_region = zone_regions.pop()
    region_ref = resources.Parse(args.region, collection='compute.regions',
                                 params=ignored_required_params)
    region = region_ref.Name()
    if zone_region != region:
      raise exceptions.InvalidArgumentException(
          '--zones', 'Specified zones not in specified region.')


def ValidateStatefulDisksDict(stateful_disks, flag_name):
  """Validate device-name and auto-delete flags in a stateful disk."""
  device_names = set()
  for stateful_disk in stateful_disks or []:
    if not stateful_disk.get('device-name'):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name, message='[device-name] is required')
    if stateful_disk.get('device-name') in device_names:
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='[device-name] `{0}` is not unique in the collection'.format(
              stateful_disk.get('device-name')))
    device_names.add(stateful_disk.get('device-name'))


def ValidateStatefulIPDicts(stateful_ips, flag_name):
  """Validate enabled, interface-name and auto-delete flags in a stateful IP."""
  interface_names = set()
  for stateful_ip in stateful_ips or []:
    # One of: interface-name, enabled is required.
    if (not (stateful_ip.get('interface-name')
             or 'enabled' in stateful_ip)):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message=(
              'one of: [interface-name], [enabled] is required.'))

    interface_name = stateful_ip.get('interface-name',
                                     STATEFUL_IP_DEFAULT_INTERFACE_NAME)

    # Don't accept multiple flags affecting the same interface.
    if interface_name in interface_names:
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message=
          '[interface-name] `{0}` is not unique in the collection'.format(
              interface_name))
    interface_names.add(interface_name)


def ValidateManagedInstanceGroupStatefulDisksProperties(args):
  ValidateStatefulDisksDict(args.stateful_disk, '--stateful-disk')


def ValidateManagedInstanceGroupStatefulIPsProperties(args):
  ValidateStatefulIPDicts(args.stateful_internal_ip, '--stateful-internal-ip')
  ValidateStatefulIPDicts(args.stateful_external_ip, '--stateful-external-ip')


def GetInstanceGroupManagerArg(zones_flag=False, region_flag=True):
  """Returns ResourceArgument for working with instance group managers."""
  if zones_flag:
    extra_region_info_about_zones_flag = (
        '\n\nIf you specify `--zones` flag this flag must be unspecified '
        'or specify the region to which the zones you listed belong.'
    )
    region_explanation = (flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT +
                          extra_region_info_about_zones_flag)
  else:
    region_explanation = flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT
  if region_flag:
    regional_collection = 'compute.regionInstanceGroupManagers'
  else:
    regional_collection = None
  return flags.ResourceArgument(
      resource_name='managed instance group',
      completer=InstanceGroupManagersCompleter,
      zonal_collection='compute.instanceGroupManagers',
      regional_collection=regional_collection,
      zone_explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT,
      region_explanation=region_explanation)


def CreateGroupReference(client, resources, args):
  resource_arg = GetInstanceGroupManagerArg()
  default_scope = compute_scope.ScopeEnum.ZONE
  scope_lister = flags.GetDefaultScopeLister(client)
  return resource_arg.ResolveAsResource(
      args, resources, default_scope=default_scope,
      scope_lister=scope_lister)


_LIST_INSTANCES_FORMAT = """\
        table(name:label=NAME,
              instance.scope().segment(0):label=ZONE,
              instanceStatus:label=STATUS,
              instanceHealth[0].detailedHealthState:label=HEALTH_STATE,
              currentAction:label=ACTION,
              version.instanceTemplate.basename():label=INSTANCE_TEMPLATE,
              version.name:label=VERSION_NAME,
              lastAttempt.errors.errors.map().format(
                "Error {0}: {1}", code, message).list(separator=", ")
                :label=LAST_ERROR
        )"""

_LIST_INSTANCES_FORMAT_BETA = """\
        table(name:label=NAME,
              instance.scope().segment(0):label=ZONE,
              instanceStatus:label=STATUS,
              instanceHealth[0].detailedHealthState:label=HEALTH_STATE,
              currentAction:label=ACTION,
              preservedState():label=PRESERVED_STATE,
              version.instanceTemplate.basename():label=INSTANCE_TEMPLATE,
              version.name:label=VERSION_NAME,
              lastAttempt.errors.errors.map().format(
                "Error {0}: {1}", code, message).list(separator=", ")
                :label=LAST_ERROR
        )"""

_LIST_INSTANCES_FORMAT_ALPHA = """\
        table(name:label=NAME,
              instance.scope().segment(0):label=ZONE,
              instanceStatus:label=STATUS,
              instanceHealth[0].detailedHealthState:label=HEALTH_STATE,
              currentAction:label=ACTION,
              preservedState():label=PRESERVED_STATE,
              version.instanceTemplate.basename():label=INSTANCE_TEMPLATE,
              version.name:label=VERSION_NAME,
              lastAttempt.errors.errors.map().format(
                "Error {0}: {1}", code, message).list(separator=", ")
                :label=LAST_ERROR
        )"""

_RELEASE_TRACK_TO_LIST_INSTANCES_FORMAT = {
    base.ReleaseTrack.GA: _LIST_INSTANCES_FORMAT,
    base.ReleaseTrack.BETA: _LIST_INSTANCES_FORMAT_BETA,
    base.ReleaseTrack.ALPHA: _LIST_INSTANCES_FORMAT_ALPHA,
}


def _TransformPreservedState(instance):
  """Transform for the PRESERVED_STATE field in the table output.

  PRESERVED_STATE is generated from the fields preservedStateFromPolicy and
  preservedStateFromConfig fields in the managedInstance message.

  Args:
    instance: instance dictionary for transform

  Returns:
    Preserved state status as one of ('POLICY', 'CONFIG', 'POLICY,CONFIG')
  """
  preserved_state_value = ''
  if ('preservedStateFromPolicy' in instance and
      instance['preservedStateFromPolicy']):
    preserved_state_value += 'POLICY,'
  if ('preservedStateFromConfig' in instance and
      instance['preservedStateFromConfig']):
    preserved_state_value += 'CONFIG'
  if preserved_state_value.endswith(','):
    preserved_state_value = preserved_state_value[:-1]
  return preserved_state_value


def AddListInstancesOutputFormat(parser, release_track=base.ReleaseTrack.GA):
  parser.display_info.AddTransforms({
      'preservedState': _TransformPreservedState,
  })
  parser.display_info.AddFormat(
      _RELEASE_TRACK_TO_LIST_INSTANCES_FORMAT[release_track])


# Rename ot HELP_BASE
STATEFUL_DISKS_HELP_BASE = """
      Disks considered stateful by the instance group. Managed instance groups
      preserve and reattach stateful disks on VM autohealing, update, and
      recreate events.
      """

STATEFUL_DISKS_HELP_INSTANCE_CONFIGS = STATEFUL_DISKS_HELP_BASE + """
      You can also attach and preserve disks, not defined in the group's
      instance template, to a given instance.

      The same disk can be attached to more than one instance but only in
      read-only mode.
      """

STATEFUL_DISKS_HELP_INSTANCE_CONFIGS_UPDATE = (
    STATEFUL_DISKS_HELP_INSTANCE_CONFIGS + """
      Use this argument multiple times to update multiple disks.

      If stateful disk with given `device-name` exists in current instance
      configuration, its properties will be replaced by the newly provided ones.
      In other case new stateful disk definition will be added to the instance
      configuration.
      """)

STATEFUL_DISK_DEVICE_NAME_ARG_HELP = """
      *device-name*::: Name under which disk is or will be attached.
      """

STATEFUL_DISK_SOURCE_ARG_HELP = """
      *source*::: Optional argument used to specify the URI of an existing
      persistent disk to attach under specified `device-name`.
      """

STATEFUL_DISK_MODE_ARG_HELP = """
      *mode*::: Specifies the mode of the disk to attach. Supported options are
      `ro` for read-only and `rw` for read-write. If omitted when source is
      specified, `rw` is used as a default. `mode` can only be specified if
      `source` is given.
      """

STATEFUL_DISK_AUTO_DELETE_ARG_HELP = """
      *auto-delete*::: (Optional) Specifies the auto deletion policy of the
      stateful disk. The following options are available:
      - ``never'': (Default) Never delete this disk. Instead, detach the disk
          when its instance is deleted.
      - ``on-permanent-instance-deletion'': Delete the stateful disk when the
          instance that it's attached to is permanently deleted from the group;
          for example, when the instance is deleted manually or when the group
          size is decreased.
      """


STATEFUL_METADATA_HELP = """
      Additional metadata to be made available to the guest operating system
      in addition to the metadata defined in the instance template.

      Stateful metadata may be used to define a key/value pair specific for
      the one given instance to differentiate it from the other instances in
      the managed instance group.

      Stateful metadata key/value pairs are preserved on instance recreation,
      autohealing, updates, and any other lifecycle transitions of the
      instance.

      Stateful metadata have priority over the metadata defined in the
      instance template. This means that stateful metadata that is defined for a
      key that already exists in the instance template overrides the instance
      template value.

      Each metadata entry is a key/value pair separated by an equals sign.
      Metadata keys must be unique and less than 128 bytes in length. Multiple
      entries can be passed to this flag, e.g.,
      ``{argument_name} key-1=value-1,key-2=value-2,key-3=value-3''.
      """

STATEFUL_METADATA_HELP_UPDATE = """
      If stateful metadata with the given key exists in current instance
      configuration, its value will be overridden with the newly provided one.
      If the key does not exist in the current instance configuration, a new
      key/value pair will be added.
      """

STATEFUL_IPS_HELP_BASE = """
      Managed instance groups preserve stateful IPs on VM autohealing, update,
      and recreate events.
      """

STATEFUL_IPS_HELP_TEMPLATE = """
      Use this argument multiple times to update more IPs.

      If a stateful {ip_type} IP with the given interface name already exists in
      the current instance configuration, its properties are replaced by the
      newly provided ones. Otherwise, a new stateful {ip_type} IP definition
      is added to the instance configuration.
      """

STATEFUL_IPS_HELP_INSTANCE_CONFIGS = STATEFUL_IPS_HELP_BASE + """
      You can preserve the IP address that's specified in a network interface
      for a specific managed instance, even if that network interface is not
      defined in the group's instance template.
      """

STATEFUL_IPS_HELP_INSTANCE_CONFIGS_UPDATE = (
    STATEFUL_IPS_HELP_INSTANCE_CONFIGS + """
      Use this argument multiple times to update multiple IPs.

      If a stateful IP with the given network interface name exists in the
      current per-instance configuration, its properties are replaced by
      the newly provided ones. Otherwise, a new stateful IP definition is
      added to the per-instance configuration.
      """)


STATEFUL_IP_ENABLED_ARG_HELP = """
      *enabled*::: Marks the IP address as stateful. The network interface
      named ``nic0'' is assumed by default when ``interface-name'' is not
      specified. This flag can be omitted when ``interface-name'' is provided
      explicitly.
      """


STATEFUL_IP_INTERFACE_NAME_ARG_WITH_ENABLED_HELP = """
      *interface-name*::: Marks the IP address from this network interface as
      stateful. This flag can be omitted when ``enabled'' is provided.
      """


STATEFUL_IP_INTERFACE_NAME_ARG_WITH_ADDRESS_HELP = """
      *interface-name*::: (Optional) Network interface name. If omitted,
      the default network interface named ``nic0'' is assumed.
      """

STATEFUL_IP_ADDRESS_ARG_HELP_INFIX = """
      + Address: URL of a static IP address reservation. For example:
      ``projects/example-project/regions/us-east1/addresses/example-ip-name''.

      + Literal: For example: ``130.211.181.55''.

      If the provided IP address is not yet reserved, the managed instance group
      automatically creates the corresponding IP address reservation. If the
      provided IP address is reserved, the group assigns the reservation to
      the instance.
      """


STATEFUL_IP_ADDRESS_ARG_HELP = """
        *address*::: Static IP address to assign to the instance in one of
        the following formats:
        """ + STATEFUL_IP_ADDRESS_ARG_HELP_INFIX

STATEFUL_IP_ADDRESS_ARG_OPTIONAL_HELP = """
      *address*::: (Optional) Static IP address to assign to the instance in
      one of the following formats:
      """ + STATEFUL_IP_ADDRESS_ARG_HELP_INFIX + """
      The ``address'' flag is optional if an address is already defined in
      the instance's per-instance configuration. Otherwise it is required.

      If omitted, the currently configured address remains unchanged.
      """

STATEFUL_IP_AUTO_DELETE_ARG_HELP = """
      *auto-delete*::: (Optional) Prescribes what should happen to an associated
      static Address resource when a VM instance is permanently deleted.
      Regardless of the value of the delete rule, stateful IP addresses are
      always preserved on instance autohealing, update, and recreation
      operations. The following options are available:
      - ``never'': (Default) Never delete the static IP address. Instead,
          unassign the address when its instance is permanently deleted and
          keep the address reserved.
      - ``on-permanent-instance-deletion'': Delete the static IP
          address reservation when the instance that it's assigned to is
          permanently deleted from the instance group; for example, when the
          instance is deleted manually or when the group size is decreased.
      """


def AddMigCreateStatefulFlags(parser):
  """Adding stateful flags for disks and names to the parser."""
  stateful_disks_help = textwrap.dedent(STATEFUL_DISKS_HELP_BASE + """
      Use this argument multiple times to attach more disks.

      *device-name*::: (Required) Device name of the disk to mark stateful.
      """ + STATEFUL_DISK_AUTO_DELETE_ARG_HELP)
  parser.add_argument(
      '--stateful-disk',
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'auto-delete': AutoDeleteFlag.ValidatorWithFlagName(
                  '--stateful_disk'),
          }),
      action='append',
      help=stateful_disks_help,
  )


def AddMigCreateStatefulIPsFlags(parser):
  """Adding stateful IPs flags to the parser."""
  stateful_internal_ips_help = textwrap.dedent(
      """
      Internal IPs considered stateful by the instance group. {}
      Use this argument multiple times to make more internal IPs stateful.

      At least one of the following is required:
      {}
      {}

      Additional arguments:
      {}
      """.format(STATEFUL_IPS_HELP_BASE,
                 STATEFUL_IP_ENABLED_ARG_HELP,
                 STATEFUL_IP_INTERFACE_NAME_ARG_WITH_ENABLED_HELP,
                 STATEFUL_IP_AUTO_DELETE_ARG_HELP))
  parser.add_argument(
      '--stateful-internal-ip',
      type=arg_parsers.ArgDict(
          allow_key_only=True,
          spec={
              'enabled': None,
              'interface-name': str,
              'auto-delete': AutoDeleteFlag.ValidatorWithFlagName(
                  '--stateful-internal-ip'),
          }),
      action='append',
      help=stateful_internal_ips_help,
  )

  stateful_external_ips_help = textwrap.dedent(
      """
      External IPs considered stateful by the instance group. {}
      Use this argument multiple times to make more external IPs stateful.

      At least one of the following is required:
      {}
      {}

      Additional arguments:
      {}
      """.format(STATEFUL_IPS_HELP_BASE,
                 STATEFUL_IP_ENABLED_ARG_HELP,
                 STATEFUL_IP_INTERFACE_NAME_ARG_WITH_ENABLED_HELP,
                 STATEFUL_IP_AUTO_DELETE_ARG_HELP))
  parser.add_argument(
      '--stateful-external-ip',
      type=arg_parsers.ArgDict(
          allow_key_only=True,
          spec={
              'enabled': None,
              'interface-name': str,
              'auto-delete': AutoDeleteFlag.ValidatorWithFlagName(
                  '--stateful-external-ip'),
          }),
      action='append',
      help=stateful_external_ips_help,
  )


def _AddMigStatefulInstanceConfigsInstanceArg(parser):
  parser.add_argument(
      '--instance',
      required=True,
      help="""
        URI/name of an existing instance in the managed instance group.
      """)


def AddMigStatefulFlagsForUpdateInstanceConfigs(parser):
  """Add args for per-instance configs update command."""
  _AddMigStatefulInstanceConfigsInstanceArg(parser)

  # Add stateful disk update args
  stateful_disk_argument_name = '--stateful-disk'
  disk_help_text = textwrap.dedent(
      (STATEFUL_DISKS_HELP_INSTANCE_CONFIGS_UPDATE +
       STATEFUL_DISK_DEVICE_NAME_ARG_HELP + STATEFUL_DISK_SOURCE_ARG_HELP +
       STATEFUL_DISK_MODE_ARG_HELP + STATEFUL_DISK_AUTO_DELETE_ARG_HELP))
  parser.add_argument(
      stateful_disk_argument_name,
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'source':
                  str,
              'mode':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName(
                      stateful_disk_argument_name)
          }),
      action='append',
      help=disk_help_text,
  )
  # Add remove disk args
  parser.add_argument(
      '--remove-stateful-disks',
      metavar='DEVICE_NAME',
      type=arg_parsers.ArgList(min_length=1),
      help=('Remove stateful configuration for the specified disks from the '
            'instance\'s configuration.'),
  )

  # Add stateful metadata args
  stateful_metadata_argument_name = '--stateful-metadata'
  metadata_help_text = textwrap.dedent(
      (STATEFUL_METADATA_HELP + STATEFUL_METADATA_HELP_UPDATE).format(
          argument_name=stateful_metadata_argument_name))
  parser.add_argument(
      stateful_metadata_argument_name,
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      action=arg_parsers.StoreOnceAction,
      metavar='KEY=VALUE',
      help=textwrap.dedent(metadata_help_text))
  parser.add_argument(
      '--remove-stateful-metadata',
      metavar='KEY',
      type=arg_parsers.ArgList(min_length=1),
      help=('Remove stateful configuration for the specified metadata keys '
            'from the instance\'s configuration.'),
  )


def _AddMigStatefulIPsFlags(parser,
                            ip_argument_name, ip_help_text,
                            remove_ip_argument_name, remove_ip_help_text):
  """Add args for per-instance configs update command."""
  parser.add_argument(
      ip_argument_name,
      type=arg_parsers.ArgDict(
          spec={
              'interface-name':
                  str,
              'address':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName(ip_argument_name)
          }),
      action='append',
      help=ip_help_text,
  )
  parser.add_argument(
      remove_ip_argument_name,
      metavar='KEY',
      type=arg_parsers.ArgList(min_length=1),
      help=remove_ip_help_text,
  )


def AddMigStatefulIPsFlagsForUpdateInstanceConfigs(parser):
  """Add args for per-instance configs update command."""
  ip_help_text = textwrap.dedent(
      (STATEFUL_IPS_HELP_INSTANCE_CONFIGS_UPDATE +
       STATEFUL_IP_INTERFACE_NAME_ARG_WITH_ADDRESS_HELP +
       STATEFUL_IP_ADDRESS_ARG_OPTIONAL_HELP +
       STATEFUL_IP_AUTO_DELETE_ARG_HELP))
  remove_ip_help_text = """
      List of all stateful IP network interface names to remove from
      the instance's per-instance configuration.
      """
  _AddMigStatefulIPsFlags(parser,
                          '--stateful-internal-ip', ip_help_text,
                          '--remove-stateful-internal-ips', remove_ip_help_text)
  _AddMigStatefulIPsFlags(parser,
                          '--stateful-external-ip', ip_help_text,
                          '--remove-stateful-external-ips', remove_ip_help_text)


def AddMigStatefulFlagsForInstanceConfigs(parser):
  """Adding stateful flags for creating instance configs."""
  _AddMigStatefulInstanceConfigsInstanceArg(parser)

  # Add stateful disk args
  stateful_disk_argument_name = '--stateful-disk'
  stateful_disks_help = textwrap.dedent(
      (STATEFUL_DISKS_HELP_INSTANCE_CONFIGS + """
        Use this argument multiple times to attach and preserve multiple disks.
      """ + STATEFUL_DISK_DEVICE_NAME_ARG_HELP + STATEFUL_DISK_SOURCE_ARG_HELP +
       STATEFUL_DISK_MODE_ARG_HELP + STATEFUL_DISK_AUTO_DELETE_ARG_HELP))
  parser.add_argument(
      stateful_disk_argument_name,
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'source':
                  str,
              'mode':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName(
                      stateful_disk_argument_name)
          }),
      action='append',
      help=stateful_disks_help,
  )

  # Add stateful metadata args
  stateful_metadata_argument_name = '--stateful-metadata'
  metadata_help_text = textwrap.dedent(
      STATEFUL_METADATA_HELP.format(
          argument_name=stateful_metadata_argument_name))
  parser.add_argument(
      stateful_metadata_argument_name,
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      action=arg_parsers.StoreOnceAction,
      metavar='KEY=VALUE',
      help=metadata_help_text)


def AddMigStatefulIPsFlagsForInstanceConfigs(parser):
  """Adding stateful IPs flags for creating instance configs."""
  # Add stateful internal IP args
  stateful_ip_help = textwrap.dedent(
      """
      {}
      Use this argument multiple times to attach and preserve multiple IPs.

      {}
      {}
      {}
      """.format(STATEFUL_IPS_HELP_INSTANCE_CONFIGS,
                 STATEFUL_IP_INTERFACE_NAME_ARG_WITH_ADDRESS_HELP,
                 STATEFUL_IP_ADDRESS_ARG_HELP,
                 STATEFUL_IP_AUTO_DELETE_ARG_HELP))

  stateful_internal_ip_argument_name = '--stateful-internal-ip'
  parser.add_argument(
      stateful_internal_ip_argument_name,
      type=arg_parsers.ArgDict(
          spec={
              'interface-name':
                  str,
              'address':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName(
                      stateful_internal_ip_argument_name)
          }),
      action='append',
      help=stateful_ip_help,
  )

  # Add stateful external IP args
  stateful_external_ip_argument_name = '--stateful-external-ip'
  parser.add_argument(
      stateful_external_ip_argument_name,
      type=arg_parsers.ArgDict(
          spec={
              'interface-name':
                  str,
              'address':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName(
                      stateful_external_ip_argument_name)
          }),
      action='append',
      help=stateful_ip_help,
  )


def AddCreateInstancesFlags(parser):
  """Adding stateful flags for creating and updating instance configs."""
  parser.add_argument(
      '--instance',
      required=True,
      help="""Name of the new instance to create.""")
  parser.add_argument(
      '--stateful-disk',
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'source':
                  str,
              'mode':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName('--stateful-disk'),
          }),
      action='append',
      help=textwrap.dedent(STATEFUL_DISKS_HELP_INSTANCE_CONFIGS),
  )
  stateful_metadata_argument_name = '--stateful-metadata'
  parser.add_argument(
      stateful_metadata_argument_name,
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      action=arg_parsers.StoreOnceAction,
      metavar='KEY=VALUE',
      help=textwrap.dedent(
          STATEFUL_METADATA_HELP.format(
              argument_name=stateful_metadata_argument_name)))

  stateful_ips_help_text_template = textwrap.dedent(
      STATEFUL_IPS_HELP_BASE
      + STATEFUL_IPS_HELP_TEMPLATE
      + STATEFUL_IP_INTERFACE_NAME_ARG_WITH_ADDRESS_HELP
      + STATEFUL_IP_ADDRESS_ARG_HELP
      + STATEFUL_IP_AUTO_DELETE_ARG_HELP
  )

  stateful_internal_ip_flag_name = '--stateful-internal-ip'
  parser.add_argument(
      stateful_internal_ip_flag_name,
      type=arg_parsers.ArgDict(
          spec={
              'interface-name': str,
              'address': str,
              'auto-delete': AutoDeleteFlag.ValidatorWithFlagName(
                  stateful_internal_ip_flag_name
              ),
          }
      ),
      action='append',
      help=stateful_ips_help_text_template.format(ip_type='internal'),
  )

  stateful_external_ip_flag_name = '--stateful-external-ip'
  parser.add_argument(
      stateful_external_ip_flag_name,
      type=arg_parsers.ArgDict(
          spec={
              'interface-name': str,
              'address': str,
              'auto-delete': AutoDeleteFlag.ValidatorWithFlagName(
                  stateful_external_ip_flag_name
              ),
          }
      ),
      action='append',
      help=stateful_ips_help_text_template.format(ip_type='external'),
  )


def AddMigStatefulUpdateInstanceFlag(parser):
  """Add flags for applying updates on PIC change."""
  parser.add_argument(
      '--update-instance',
      default=True,
      action='store_true',
      help="""
          Apply the configuration changes immediately to the instance. If you
          disable this flag, the managed instance group will apply the
          configuration update when you next recreate or update the instance.

          Example: say you have an instance with a disk attached to it and you
          created a stateful configuration for the disk. If you decide to
          delete the stateful configuration for the disk and you provide this
          flag, the group immediately refreshes the instance and removes the
          stateful configuration for the disk. Similarly if you have attached
          a new disk or changed its definition, with this flag the group
          immediately refreshes the instance with the new configuration.""")
  parser.add_argument(
      '--instance-update-minimal-action',
      choices=mig_flags.InstanceActionChoicesWithNone(),
      default='none',
      help="""
          Perform at least this action on the instance while updating, if
          `--update-instance` is set to `true`.""")


def ValidateMigStatefulDiskFlagForInstanceConfigs(stateful_disks,
                                                  flag_name,
                                                  for_update=False,
                                                  need_disk_source=False):
  """Validates the values of stateful disk flags for instance configs."""
  device_names = set()
  for stateful_disk in stateful_disks or []:
    if not stateful_disk.get('device-name'):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name, message='[device-name] is required')

    if stateful_disk.get('device-name') in device_names:
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='[device-name] `{0}` is not unique in the collection'.format(
              stateful_disk.get('device-name')))
    device_names.add(stateful_disk.get('device-name'))

    mode_value = stateful_disk.get('mode')
    if mode_value and mode_value not in ('rw', 'ro'):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='Value for [mode] must be [rw] or [ro], not [{0}]'.format(
              mode_value))

    if need_disk_source and not stateful_disk.get('source'):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='[source] is required for all stateful disks')

    if not for_update and mode_value and not stateful_disk.get('source'):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='[mode] can be set then and only then when [source] is given')


def ValidateMigStatefulIpFlagForInstanceConfigs(flag_name, stateful_ips,
                                                current_addresses):
  """Validates the values of stateful IP flags for instance configs."""
  interface_names = set()
  for stateful_ip in (stateful_ips or []):
    interface_name = stateful_ip.get('interface-name',
                                     STATEFUL_IP_DEFAULT_INTERFACE_NAME)
    if not ('address' in stateful_ip
            or interface_name in current_addresses):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name, message='[address] is required')

    if interface_name in interface_names:
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='[interface-name] `{0}` is not unique in the collection'
          .format(interface_name))
    interface_names.add(interface_name)


def ValidateMigStatefulDisksRemovalFlagForInstanceConfigs(disks_to_remove,
                                                          disks_to_update):
  remove_stateful_disks_set = set(disks_to_remove or [])
  for stateful_disk_to_update in disks_to_update or []:
    if stateful_disk_to_update.get('device-name') in remove_stateful_disks_set:
      raise exceptions.InvalidArgumentException(
          parameter_name='--remove-stateful-disks',
          message=('the same [device-name] `{0}` cannot be updated and'
                   ' removed in one command call'.format(
                       stateful_disk_to_update.get('device-name'))))


def ValidateMigStatefulMetadataRemovalFlagForInstanceConfigs(entries_to_remove,
                                                             entries_to_update):
  remove_stateful_metadata_set = set(entries_to_remove or [])
  update_stateful_metadata_set = set(entries_to_update.keys())
  keys_intersection = remove_stateful_metadata_set.intersection(
      update_stateful_metadata_set)
  if keys_intersection:
    raise exceptions.InvalidArgumentException(
        parameter_name='--remove-stateful-metadata',
        message=('the same metadata key(s) `{0}` cannot be updated and'
                 ' removed in one command call'.format(
                     ', '.join(keys_intersection))))


def ValidateMigStatefulIpsRemovalFlagForInstanceConfigs(flag_name,
                                                        ips_to_remove,
                                                        ips_to_update):
  remove_ips_set = set(ips_to_remove or [])
  for ip_to_update in ips_to_update or []:
    if ip_to_update.get('interface-name') in remove_ips_set:
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message=('the same [interface-name] `{0}` cannot be updated and'
                   ' removed in one command call'.format(
                       ip_to_update.get('interface-name'))))


def ValidateMigStatefulFlagsForInstanceConfigs(args,
                                               for_update=False,
                                               need_disk_source=False):
  """Validates the values of stateful flags for instance configs."""
  ValidateMigStatefulDiskFlagForInstanceConfigs(args.stateful_disk,
                                                '--stateful-disk',
                                                for_update, need_disk_source)

  if for_update:
    ValidateMigStatefulDisksRemovalFlagForInstanceConfigs(
        disks_to_remove=args.remove_stateful_disks,
        disks_to_update=args.stateful_disk)
    ValidateMigStatefulMetadataRemovalFlagForInstanceConfigs(
        entries_to_remove=args.remove_stateful_metadata,
        entries_to_update=args.stateful_metadata)


def ValidateMigStatefulIPFlagsForInstanceConfigs(args,
                                                 current_internal_addresses,
                                                 current_external_addresses,
                                                 for_update=False):
  """Validates the values of stateful flags for instance configs, with IPs."""
  ValidateMigStatefulIpFlagForInstanceConfigs('--stateful-internal-ip',
                                              args.stateful_internal_ip,
                                              current_internal_addresses)
  ValidateMigStatefulIpFlagForInstanceConfigs('--stateful-external-ip',
                                              args.stateful_external_ip,
                                              current_external_addresses)
  if for_update:
    ValidateMigStatefulIpsRemovalFlagForInstanceConfigs(
        flag_name='--remove-stateful-internal-ips',
        ips_to_remove=args.remove_stateful_internal_ips,
        ips_to_update=args.stateful_internal_ip)
    ValidateMigStatefulIpsRemovalFlagForInstanceConfigs(
        flag_name='--remove-stateful-external-ips',
        ips_to_remove=args.remove_stateful_external_ips,
        ips_to_update=args.stateful_external_ip)


def AddDescriptionFlag(parser, for_update=False):
  """Add --description to the parser."""
  parser.add_argument(
      '--description',
      help='An optional description for this group.' +
      (' To clear the description, set the value to an empty string.'
       if for_update
       else ''))


def AddMigUpdateStatefulFlags(parser):
  """Add --stateful-disk and --remove-stateful-disks to the parser."""
  stateful_disks_help = textwrap.dedent(STATEFUL_DISKS_HELP_BASE + """
      Use this argument multiple times to update more disks.

      If a stateful disk with the given device name already exists in the
      current instance configuration, its properties will be replaced by the
      newly provided ones. Otherwise, a new stateful disk definition will be
      added to the instance configuration.

      *device-name*::: (Required) Device name of the disk to mark stateful.
      """ + STATEFUL_DISK_AUTO_DELETE_ARG_HELP)
  stateful_disk_flag_name = '--stateful-disk'
  parser.add_argument(
      stateful_disk_flag_name,
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName(stateful_disk_flag_name)
          }),
      action='append',
      help=stateful_disks_help,
  )
  parser.add_argument(
      '--remove-stateful-disks',
      metavar='DEVICE_NAME',
      type=arg_parsers.ArgList(min_length=1),
      help='Remove stateful configuration for the specified disks.',
  )


def AddMigUpdateStatefulFlagsIPs(parser):
  """Add stateful IPs flags to the parser."""
  stateful_ips_help_text_template = textwrap.dedent(
      STATEFUL_IPS_HELP_BASE +
      STATEFUL_IPS_HELP_TEMPLATE +
      """
      At least one of the following is required:
      {}
      {}

      Additional arguments:
      {}
      """.format(STATEFUL_IP_ENABLED_ARG_HELP,
                 STATEFUL_IP_INTERFACE_NAME_ARG_WITH_ENABLED_HELP,
                 STATEFUL_IP_AUTO_DELETE_ARG_HELP))

  stateful_internal_ip_flag_name = '--stateful-internal-ip'
  parser.add_argument(
      stateful_internal_ip_flag_name,
      type=arg_parsers.ArgDict(
          allow_key_only=True,
          spec={
              'enabled': None,
              'interface-name': str,
              'auto-delete': AutoDeleteFlag.ValidatorWithFlagName(
                  stateful_internal_ip_flag_name)
          }),
      action='append',
      help=stateful_ips_help_text_template.format(ip_type='internal'),
  )

  stateful_external_ip_flag_name = '--stateful-external-ip'
  parser.add_argument(
      stateful_external_ip_flag_name,
      type=arg_parsers.ArgDict(
          allow_key_only=True,
          spec={
              'enabled': None,
              'interface-name': str,
              'auto-delete': AutoDeleteFlag.ValidatorWithFlagName(
                  stateful_external_ip_flag_name)
          }),
      action='append',
      help=stateful_ips_help_text_template.format(ip_type='external'),
  )

  remove_stateful_ips_help_text_template = """
      Remove stateful configuration for the specified interfaces for
      {ip_type} IPs.
      """
  parser.add_argument(
      '--remove-stateful-internal-ips',
      metavar='INTERFACE_NAME',
      type=arg_parsers.ArgList(min_length=1),
      help=remove_stateful_ips_help_text_template.format(ip_type='internal'),
  )
  parser.add_argument(
      '--remove-stateful-external-ips',
      metavar='INTERFACE_NAME',
      type=arg_parsers.ArgList(min_length=1),
      help=remove_stateful_ips_help_text_template.format(ip_type='external'),
  )


def ValidateUpdateStatefulPolicyParams(args, current_stateful_policy):
  """Check stateful properties of update request."""
  current_device_names = set(
      managed_instance_groups_utils.GetDeviceNamesFromStatefulPolicy(
          current_stateful_policy))
  update_disk_names = []
  if args.stateful_disk:
    ValidateStatefulDisksDict(args.stateful_disk, '--stateful-disk')
    update_disk_names = [
        stateful_disk.get('device-name') for stateful_disk in args.stateful_disk
    ]
  if args.remove_stateful_disks:
    if any(
        args.remove_stateful_disks.count(x) > 1
        for x in args.remove_stateful_disks):
      raise exceptions.InvalidArgumentException(
          parameter_name='update',
          message=(
              'When removing device names from Stateful Policy, please provide '
              'each name exactly once.'))

  update_set = set(update_disk_names)
  remove_set = set(args.remove_stateful_disks or [])
  intersection = update_set.intersection(remove_set)

  if intersection:
    raise exceptions.InvalidArgumentException(
        parameter_name='update',
        message=
        ('You cannot simultaneously add and remove the same device names {} to '
         'Stateful Policy.'.format(six.text_type(intersection))))
  not_current_device_names = remove_set - current_device_names
  if not_current_device_names:
    raise exceptions.InvalidArgumentException(
        parameter_name='update',
        message=('Disks [{}] are not currently set as stateful, '
                 'so they cannot be removed from Stateful Policy.'.format(
                     six.text_type(not_current_device_names))))


def _ValidateUpdateStatefulPolicyParamsWithIPsCommon(current_interface_names,
                                                     update_flag_name,
                                                     remove_flag_name,
                                                     update_ips,
                                                     remove_ips,
                                                     ip_type_name):
  """Check stateful properties of update request."""
  update_interface_names = []
  if update_ips:
    ValidateStatefulIPDicts(update_ips, update_flag_name)
    for stateful_ip in update_ips:
      update_interface_names.append(
          stateful_ip.get('interface-name', STATEFUL_IP_DEFAULT_INTERFACE_NAME))

  remove_interface_names = remove_ips or []

  if any(
      remove_interface_names.count(x) > 1
      for x in remove_interface_names):
    raise exceptions.InvalidArgumentException(
        parameter_name='update',
        message=(
            'When removing stateful {} IPs from Stateful Policy, please '
            'provide each network interface name exactly once.'.format(
                ip_type_name)))

  update_set = set(update_interface_names)
  remove_set = set(remove_interface_names)
  intersection = update_set.intersection(remove_set)

  if intersection:
    raise exceptions.InvalidArgumentException(
        parameter_name='update',
        message=
        ('You cannot simultaneously add and remove the same interface {} to '
         'stateful {} IPs in Stateful Policy.'.format(
             six.text_type(intersection), ip_type_name)))
  not_current_interface_names = remove_set - current_interface_names
  if not_current_interface_names:
    raise exceptions.InvalidArgumentException(
        parameter_name='update',
        message=('Interfaces [{}] are not currently set as stateful {} IPs, '
                 'so they cannot be removed from Stateful Policy.'.format(
                     six.text_type(not_current_interface_names), ip_type_name)))


def _ValidateUpdateStatefulPolicyParamsWithInternalIPs(args,
                                                       current_stateful_policy):
  """Check stateful internal IPs properties of update request."""
  current_interface_names = set(
      managed_instance_groups_utils
      .GetInterfaceNamesFromStatefulPolicyForInternalIPs(
          current_stateful_policy))
  _ValidateUpdateStatefulPolicyParamsWithIPsCommon(
      current_interface_names,
      '--stateful-internal-ip', '--remove-stateful-internal-ips',
      args.stateful_internal_ip, args.remove_stateful_internal_ips, 'internal')


def _ValidateUpdateStatefulPolicyParamsWithExternalIPs(args,
                                                       current_stateful_policy):
  """Check stateful external IPs properties of update request."""
  current_interface_names = set(
      managed_instance_groups_utils
      .GetInterfaceNamesFromStatefulPolicyForExternalIPs(
          current_stateful_policy))
  _ValidateUpdateStatefulPolicyParamsWithIPsCommon(
      current_interface_names,
      '--stateful-external-ip', '--remove-stateful-external-ips',
      args.stateful_external_ip, args.remove_stateful_external_ips, 'external')


def ValidateUpdateStatefulPolicyParamsWithIPs(args, current_stateful_policy):
  """Check stateful properties of update request."""
  _ValidateUpdateStatefulPolicyParamsWithInternalIPs(args,
                                                     current_stateful_policy)
  _ValidateUpdateStatefulPolicyParamsWithExternalIPs(args,
                                                     current_stateful_policy)
