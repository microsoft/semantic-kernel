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
"""Flags and helpers for compute instances bulk commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags as maintenance_flags
from googlecloudsdk.command_lib.util.args import labels_util


def AddDiskArgsForBulk(parser):
  """Adds arguments related to disks for bulk insert."""

  disk_device_name_help = instances_flags.GetDiskDeviceNameHelp(
      container_mount_enabled=False)
  instances_flags.AddBootDiskArgs(parser, enable_kms=True)

  disk_arg_spec = {
      'name': str,
      'boot': arg_parsers.ArgBoolean(),
      'device-name': str,
      'scope': str,
  }

  disk_help = """
      Attaches persistent disks to the instances. The disks
      specified must already exist.

      *name*::: The disk to attach to the instances.

      *boot*::: If ``yes'', indicates that this is a boot disk. The
      virtual machines will use the first partition of the disk for
      their root file systems. The default value for this is ``no''.

      *device-name*::: {}

      *scope*::: Can be `zonal` or `regional`. If ``zonal'', the disk is
      interpreted as a zonal disk in the same zone as the instance (default).
      If ``regional'', the disk is interpreted as a regional disk in the same
      region as the instance. The default value for this is ``zonal''.
      """.format(disk_device_name_help)

  parser.add_argument(
      '--disk',
      type=arg_parsers.ArgDict(spec=disk_arg_spec),
      action='append',
      help=disk_help)


def ValidateBulkDiskFlags(args,
                          enable_source_snapshot_csek=False,
                          enable_image_csek=False):
  """Validates the values of all disk-related flags."""
  for disk in args.disk or []:
    if 'name' not in disk:
      raise exceptions.InvalidArgumentException(
          '--disk',
          '[name] is missing in [--disk]. [--disk] value must be of the form '
          '[{0}].'.format(instances_flags.DISK_METAVAR))

  instances_flags.ValidateDiskBootFlags(args, enable_kms=True)
  instances_flags.ValidateCreateDiskFlags(
      args,
      enable_snapshots=True,
      enable_source_snapshot_csek=enable_source_snapshot_csek,
      enable_image_csek=enable_image_csek)


def MakeBulkSourceInstanceTemplateArg():
  return compute_flags.ResourceArgument(
      name='--source-instance-template',
      resource_name='instance template',
      completer=compute_completers.InstanceTemplatesCompleter,
      required=False,
      global_collection='compute.instanceTemplates',
      short_help=('The name of the instance template that the instance will '
                  'be created from. Users can override fields by specifying '
                  'other flags.'))


def AddDistributionTargetShapeArgs(parser):
  """Adds bulk creation target shape arguments to parser."""
  choices_text = {
      'ANY_SINGLE_ZONE':
          'Enforces VM placement in one allowed zone. Use this to avoid '
          'cross-zone network egress or to reduce network latency. This is the '
          'default value.',
      'BALANCED':
          'Allows distribution of VMs in zones where resources are available '
          'while distributing VMs as evenly as possible across selected zones '
          'to minimize the impact of zonal failures. Recommended for highly '
          'available serving or batch workloads.',
      'ANY': 'Allows creating VMs in multiple zones if one zone cannot '
             'accommodate all the requested VMs. The resulting distribution '
             'shapes can vary.'
  }
  parser.add_argument(
      '--target-distribution-shape',
      metavar='SHAPE',
      type=lambda x: x.upper(),
      choices=choices_text,
      help="""
        Specifies whether and how to distribute VMs across multiple zones in a
        region or to enforce placement of VMs in a single zone.
        The default shape is `ANY_SINGLE_ZONE`.
      """)


def AddBulkCreateArgs(
    parser,
    add_zone_region_flags,
    support_max_count_per_zone,
    support_custom_hostnames,
):
  """Adds bulk creation specific arguments to parser."""
  parser.add_argument(
      '--count',
      type=int,
      help="""
      Number of Compute Engine virtual machines to create. If specified, and
      `--predefined-names` is specified, count must equal the amount of names
      provided to `--predefined-names`. If not specified,
      the number of virtual machines created will equal the number of names
      provided to `--predefined-names`.
    """)
  parser.add_argument(
      '--min-count',
      type=int,
      help="""
        The minimum number of Compute Engine virtual machines that must be
        successfully created for the operation to be considered a success. If
        the operation successfully creates as many virtual machines as
        specified here they will be persisted, otherwise the operation rolls
        back and deletes all created virtual machines. If not specified, this
        value is equal to `--count`.""")

  name_group = parser.add_group(mutex=True, required=True)
  name_group.add_argument(
      '--predefined-names',
      type=arg_parsers.ArgList(),
      metavar='INSTANCE_NAME',
      help="""
        List of predefined names for the Compute Engine virtual machines being
        created. If `--count` is specified alongside this flag, provided count
        must equal the amount of names provided to this flag. If `--count` is
        not specified, the number of virtual machines
        created will equal the number of names provided.
      """)
  name_group.add_argument(
      '--name-pattern',
      help="""
        Name pattern for generating instance names. Specify a pattern with a
        single sequence of hash (#) characters that will be replaced with
        generated sequential numbers of instances. E.g. name pattern of
        'instance-###' will generate instance names 'instance-001',
        'instance-002', and so on, until the number of virtual machines
        specified using `--count` is reached. If instances matching name pattern
        exist, the new instances will be assigned names to avoid clashing with
        the existing ones. E.g. if there exists `instance-123`, the new
        instances will start at `instance-124` and increment from there.
      """)
  if add_zone_region_flags:
    location = parser.add_group(required=True, mutex=True)
    location.add_argument(
        '--region',
        help="""
        Region in which to create the Compute Engine virtual machines. Compute
        Engine will select a zone in which to create all virtual machines.
    """)
    location.add_argument(
        '--zone',
        help="""
        Zone in which to create the Compute Engine virtual machines.

        A list of zones can be fetched by running:

            $ gcloud compute zones list

        To unset the property, run:

            $ gcloud config unset compute/zone

        Alternatively, the zone can be stored in the environment variable
        CLOUDSDK_COMPUTE_ZONE.
     """)
  parser.add_argument(
      '--location-policy',
      metavar='ZONE=POLICY',
      type=arg_parsers.ArgDict(),
      help="""
        Policy for which zones to include or exclude during bulk instance creation
        within a region. Policy is defined as a list of key-value pairs, with the
        key being the zone name, and value being the applied policy. Available
        policies are `allow` and `deny`. Default for zones if left unspecified is `allow`.

        Example:

          gcloud compute instances bulk create --name-pattern=example-###
            --count=5 --region=us-east1
            --location-policy=us-east1-b=allow,us-east1-c=deny
      """,
  )
  if support_max_count_per_zone:
    parser.add_argument(
        '--max-count-per-zone',
        metavar='ZONE=MAX_COUNT_PER_ZONE',
        type=arg_parsers.ArgDict(),
        help="""
          Maximum number of instances per zone specified as key-value pairs. The zone name is the key and the max count per zone
          is the value in that zone.

          Example:

            gcloud compute instances bulk create --name-pattern=example-###
              --count=5 --region=us-east1
              --max-count-per-zone=us-east1-b=2,us-east-1-c=1
        """,
    )
  if support_custom_hostnames:
    parser.add_argument(
        '--per-instance-hostnames',
        metavar='INSTANCE_NAME=INSTANCE_HOSTNAME',
        type=arg_parsers.ArgDict(key_type=str, value_type=str),
        help="""
          Specify the hostname of the instance to be created. The specified
          hostname must be RFC1035 compliant. If hostname is not specified, the
          default hostname is [INSTANCE_NAME].c.[PROJECT_ID].internal when using
          the global DNS, and [INSTANCE_NAME].[ZONE].c.[PROJECT_ID].internal
          when using zonal DNS.
        """,
    )


def AddBulkCreateNetworkingArgs(
    parser, support_no_address=False, support_network_queue_count=False
):
  """Adds Networking Args for Bulk Create Command."""

  multiple_network_interface_cards_spec = {
      'network': str,
      'subnet': str,
  }

  def ValidateNetworkTier(network_tier_input):
    network_tier = network_tier_input.upper()
    if network_tier in constants.NETWORK_TIER_CHOICES_FOR_INSTANCE:
      return network_tier
    else:
      raise exceptions.InvalidArgumentException(
          '--network-interface', 'Invalid value for network-tier')

  multiple_network_interface_cards_spec['network-tier'] = ValidateNetworkTier
  multiple_network_interface_cards_spec['nic-type'] = (
      instances_flags.ValidateNetworkInterfaceNicType)

  network_interface_help = """\
      Adds a network interface to the instance. Mutually exclusive with any
      of these flags: *--network*, *--network-tier*, *--subnet*.
      This flag can be repeated to specify multiple network interfaces.

      *network*::: Specifies the network that the interface will be part of.
      If subnet is also specified it must be subnetwork of this network. If
      neither is specified, this defaults to the "default" network.

      *network-tier*::: Specifies the network tier of the interface.
      ``NETWORK_TIER'' must be one of: `PREMIUM`, `STANDARD`. The default
      value is `PREMIUM`.

      *subnet*::: Specifies the subnet that the interface will be part of.
      If network key is also specified this must be a subnetwork of the
      specified network.

      *nic-type*::: Specifies the  Network Interface Controller (NIC) type for
      the interface. ``NIC_TYPE'' must be one of: `GVNIC`, `VIRTIO_NET`.
  """

  if support_no_address:
    multiple_network_interface_cards_spec['no-address'] = None
    network_interface_help += """
      *no-address*::: If specified the interface will have no external IP.
      If not specified instances will get ephemeral IPs.
      """

  if support_network_queue_count:
    multiple_network_interface_cards_spec['queue-count'] = int
    network_interface_help += """
      *queue-count*::: Specifies the networking queue count for this interface.
      Both Rx and Tx queues will be set to this number. If it's not specified, a
      default queue count will be assigned. See
      https://cloud.google.com/compute/docs/network-bandwidth#rx-tx for
      more details.
    """

  parser.add_argument(
      '--network-interface',
      type=arg_parsers.ArgDict(
          spec=multiple_network_interface_cards_spec,
          allow_key_only=True,
      ),
      action='append',  # pylint:disable=protected-access
      metavar='PROPERTY=VALUE',
      help=network_interface_help)


def AddCommonBulkInsertArgs(
    parser,
    release_track,
    deprecate_maintenance_policy=False,
    support_min_node_cpu=False,
    support_erase_vss=False,
    snapshot_csek=False,
    image_csek=False,
    support_display_device=False,
    support_local_ssd_size=False,
    support_numa_node_count=False,
    support_visible_core_count=False,
    support_max_run_duration=False,
    support_enable_target_shape=False,
    add_zone_region_flags=True,
    support_confidential_compute_type=False,
    support_confidential_compute_type_tdx=False,
    support_no_address_in_networking=False,
    support_max_count_per_zone=False,
    support_network_queue_count=False,
    support_performance_monitoring_unit=False,
    support_custom_hostnames=False,
    support_storage_pool=False,
    support_specific_then_x_affinity=False,
    support_ipv6_only=False,
):
  """Register parser args common to all tracks."""
  metadata_utils.AddMetadataArgs(parser)
  AddDiskArgsForBulk(parser)
  instances_flags.AddCreateDiskArgs(
      parser,
      enable_kms=True,
      enable_snapshots=True,
      source_snapshot_csek=snapshot_csek,
      image_csek=image_csek,
      include_name=False,
      support_boot=True,
      support_storage_pool=support_storage_pool)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAcceleratorArgs(parser)
  instances_flags.AddMachineTypeArgs(parser)
  instances_flags.AddMaintenancePolicyArgs(
      parser, deprecate=deprecate_maintenance_policy)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddProvisioningModelVmArgs(parser)
  instances_flags.AddNetworkPerformanceConfigsArgs(parser)
  instances_flags.AddInstanceTerminationActionVmArgs(parser)
  instances_flags.AddServiceAccountAndScopeArgs(
      parser,
      False,
      extra_scopes_help='However, if neither `--scopes` nor `--no-scopes` are '
      'specified and the project has no default service '
      'account, then the instance will be created with no '
      'scopes. Note that the level of access that a service '
      'account has is determined by a combination of access '
      'scopes and IAM roles so you must configure both '
      'access scopes and IAM roles for the service account '
      'to work properly.')
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddNoAddressArg(parser)
  instances_flags.AddNetworkArgs(parser)
  instances_flags.AddNetworkTierArgs(parser, instance=True)
  AddBulkCreateNetworkingArgs(
      parser,
      support_no_address_in_networking,
      support_network_queue_count=support_network_queue_count,
  )

  instances_flags.AddImageArgs(parser, enable_snapshots=True)
  instances_flags.AddShieldedInstanceConfigArgs(parser)
  instances_flags.AddNestedVirtualizationArgs(parser)
  instances_flags.AddThreadsPerCoreArgs(parser)
  instances_flags.AddEnableUefiNetworkingArgs(parser)
  instances_flags.AddResourceManagerTagsArgs(parser)
  if support_numa_node_count:
    instances_flags.AddNumaNodeCountArgs(parser)

  if support_display_device:
    instances_flags.AddDisplayDeviceArg(parser)

  instances_flags.AddReservationAffinityGroup(
      parser,
      group_text='Specifies the reservation for the instance.',
      affinity_text='The type of reservation for the instance.',
      support_specific_then_x_affinity=support_specific_then_x_affinity)

  maintenance_flags.AddResourcePoliciesArgs(parser, 'added to', 'instance')

  if support_min_node_cpu:
    instances_flags.AddMinNodeCpuArg(parser)

  instances_flags.AddLocationHintArg(parser)

  if support_erase_vss:
    compute_flags.AddEraseVssSignature(
        parser, 'source snapshots or source machine'
        ' image')

  labels_util.AddCreateLabelsFlags(parser)

  parser.add_argument(
      '--description', help='Specifies a textual description of the instances.')

  base.ASYNC_FLAG.AddToParser(parser)
  parser.display_info.AddFormat(
      'multi(instances:format="table(name,zone.basename())")')

  if support_visible_core_count:
    instances_flags.AddVisibleCoreCountArgs(parser)

  if support_local_ssd_size:
    instances_flags.AddLocalSsdArgsWithSize(parser)
  else:
    instances_flags.AddLocalSsdArgs(parser)

  if support_max_run_duration:
    instances_flags.AddMaxRunDurationVmArgs(parser)

  if support_enable_target_shape:
    AddDistributionTargetShapeArgs(parser)

  instances_flags.AddStackTypeArgs(parser, support_ipv6_only)
  instances_flags.AddMinCpuPlatformArgs(parser, release_track)
  instances_flags.AddPublicDnsArgs(parser, instance=True)
  instances_flags.AddConfidentialComputeArgs(
      parser,
      support_confidential_compute_type,
      support_confidential_compute_type_tdx)
  instances_flags.AddPostKeyRevocationActionTypeArgs(parser)
  AddBulkCreateArgs(
      parser,
      add_zone_region_flags,
      support_max_count_per_zone,
      support_custom_hostnames,
  )

  if support_performance_monitoring_unit:
    instances_flags.AddPerformanceMonitoringUnitArgs(parser)


def ValidateBulkCreateArgs(args):
  """Validates args for bulk create."""
  if args.IsSpecified('name_pattern') and not args.IsSpecified('count'):
    raise exceptions.RequiredArgumentException(
        '--count',
        """The `--count` argument must be specified when the `--name-pattern` argument is specified."""
    )
  if args.IsSpecified('location_policy') and (args.IsSpecified('zone') or
                                              not args.IsSpecified('region')):
    raise exceptions.RequiredArgumentException(
        '--region',
        """The `--region` argument must be used alongside the `--location-policy` argument and not `--zone`."""
    )


def ValidateBulkTargetShapeArgs(args):
  """Validates target shape arg for bulk create."""
  if args.IsSpecified('target_distribution_shape') and (
      args.IsSpecified('zone') or not args.IsSpecified('region')):
    raise exceptions.RequiredArgumentException(
        '--region',
        """The `--region` argument must be used alongside the `--target_distribution_shape` argument and not `--zone`."""
    )


def ValidateLocationPolicyArgs(args):
  """Validates args supplied to --location-policy."""
  if args.IsSpecified('location_policy'):
    for zone, policy in args.location_policy.items():
      zone_split = zone.split('-')
      if len(zone_split) != 3 or (
          len(zone_split[2]) != 1 or
          not zone_split[2].isalpha()) or not zone_split[1][-1].isdigit():
        raise exceptions.InvalidArgumentException(
            '--location-policy', 'Key [{}] must be a zone.'.format(zone))

      if policy not in ['allow', 'deny']:
        raise exceptions.InvalidArgumentException(
            '--location-policy',
            'Value [{}] must be one of [allow, deny]'.format(policy))


def ValidateMaxCountPerZoneArgs(args):
  """Validates args supplied to --max-count-per-zone."""
  if args.IsKnownAndSpecified('max_count_per_zone'):
    for zone, count in args.max_count_per_zone.items():
      if not ValidateZone(zone):
        raise exceptions.InvalidArgumentException(
            '--max-count-per-zone', 'Key [{}] must be a zone.'.format(zone)
        )
      if not ValidateNaturalCount(count):
        raise exceptions.InvalidArgumentException(
            '--max-count-per-zone',
            'Value [{}] must be a positive natural number.'.format(count),
        )


def ValidateCustomHostnames(args):
  """Validates args supplied to --per-instance-hostnames."""
  if args.IsKnownAndSpecified('per_instance_hostnames'):
    if not args.IsKnownAndSpecified('predefined_names'):
      raise exceptions.RequiredArgumentException(
          '--per-instance-hostnames',
          """The `--per-instance-hostnames` argument must be used alongside the `--predefined-names` argument.""",
      )
    for instance_name, _ in args.per_instance_hostnames.items():
      if instance_name not in args.predefined_names:
        raise exceptions.InvalidArgumentException(
            '--per-instance-hostnames',
            'Instance [{}] missing in predefined_names. Instance names from'
            ' --per-instance-hostnames must be included in --predefined-names'
            ' flag.'.format(instance_name),
        )


def ValidateZone(zone):
  """Validates if zone is valid."""
  return (
      len(zone) < 64 and re.compile(r'^\w+-\w+\d+-\w+').match(zone) is not None
  )


def ValidateNaturalCount(count):
  """Validates if count is positive natural number."""
  return re.compile(r'^[1-9]\d*').match(count) is not None


def ValidateBulkInsertArgs(
    args,
    support_enable_target_shape,
    support_source_snapshot_csek,
    support_image_csek,
    support_max_run_duration,
    support_max_count_per_zone,
    support_custom_hostnames,
):
  """Validates all bulk and instance args."""
  ValidateBulkCreateArgs(args)
  if support_enable_target_shape:
    ValidateBulkTargetShapeArgs(args)
  ValidateLocationPolicyArgs(args)
  if support_max_count_per_zone:
    ValidateMaxCountPerZoneArgs(args)
  if support_custom_hostnames:
    ValidateCustomHostnames(args)
  ValidateBulkDiskFlags(
      args,
      enable_source_snapshot_csek=support_source_snapshot_csek,
      enable_image_csek=support_image_csek)
  instances_flags.ValidateImageFlags(args)
  instances_flags.ValidateLocalSsdFlags(args)
  instances_flags.ValidateNicFlags(args)
  instances_flags.ValidateServiceAccountAndScopeArgs(args)
  instances_flags.ValidateAcceleratorArgs(args)
  instances_flags.ValidateNetworkTierArgs(args)
  instances_flags.ValidateReservationAffinityGroup(args)
  instances_flags.ValidateNetworkPerformanceConfigsArgs(args)
  instances_flags.ValidateInstanceScheduling(
      args, support_max_run_duration=support_max_run_duration)
