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
"""Flags and helpers for the compute VM instances commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import functools
import ipaddress

from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import containers_utils
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import disks_util
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import kms_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.zones import service as zones_service
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources as core_resources

import six

ZONE_PROPERTY_EXPLANATION = """\
If not specified, you might be prompted to select a zone (interactive mode
only). `gcloud` attempts to identify the appropriate zone by searching for
resources in your currently active project. If the zone cannot be determined,
`gcloud` prompts you for a selection with all available Google Cloud Platform
zones.

To avoid prompting when this flag is omitted, the user can set the
``compute/zone'' property:

  $ gcloud config set compute/zone ZONE

A list of zones can be fetched by running:

  $ gcloud compute zones list

To unset the property, run:

  $ gcloud config unset compute/zone

Alternatively, the zone can be stored in the environment variable
``CLOUDSDK_COMPUTE_ZONE''.
"""

MIGRATION_OPTIONS = {
    'MIGRATE': (
        'The instances should be migrated to a new host. This will temporarily '
        'impact the performance of instances during a migration event.'),
    'TERMINATE': 'The instances should be terminated.',
}

LOCAL_SSD_INTERFACES = ['NVME', 'SCSI']

DISK_METAVAR = ('name=NAME [mode={ro,rw}] [device-name=DEVICE_NAME] ')

DISK_METAVAR_ZONAL_OR_REGIONAL = (
    'name=NAME [mode={ro,rw}] [device-name=DEVICE_NAME] '
    '[scope={zonal,regional}]')

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      zone.basename(),
      machineType.machine_type().basename(),
      scheduling.preemptible.yesno(yes=true, no=''),
      networkInterfaces[].networkIP.notnull().list():label=INTERNAL_IP,
      networkInterfaces[].accessConfigs[0].natIP.notnull().list()\
      :label=EXTERNAL_IP,
      status
    )"""

IPV6_INFO_LIST_FORMAT = """\
table(
            name,
            zone.basename(),
            networkInterfaces[].stackType.notnull().list(),
            networkInterfaces[].ipv6AccessConfigs[0].externalIpv6.notnull().list():label=EXTERNAL_IPV6,
            networkInterfaces[].ipv6Address.notnull().list():label=INTERNAL_IPV6)"""

INSTANCE_ARG = compute_flags.ResourceArgument(
    resource_name='instance',
    name='instance_name',
    completer=compute_completers.InstancesCompleter,
    zonal_collection='compute.instances',
    zone_explanation=ZONE_PROPERTY_EXPLANATION)

INSTANCE_ARG_NOT_REQUIRED = compute_flags.ResourceArgument(
    resource_name='instance',
    name='instance_name',
    required=False,
    completer=compute_completers.InstancesCompleter,
    zonal_collection='compute.instances',
    zone_explanation=ZONE_PROPERTY_EXPLANATION)

INSTANCES_ARG = compute_flags.ResourceArgument(
    resource_name='instance',
    name='instance_names',
    completer=compute_completers.InstancesCompleter,
    zonal_collection='compute.instances',
    zone_explanation=ZONE_PROPERTY_EXPLANATION,
    plural=True)

INSTANCES_ARG_FOR_CREATE = compute_flags.ResourceArgument(
    resource_name='instance',
    name='instance_names',
    completer=compute_completers.InstancesCompleter,
    zonal_collection='compute.instances',
    zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
    plural=True)

INSTANCES_ARG_FOR_IMPORT = compute_flags.ResourceArgument(
    resource_name='instance',
    name='instance_name',
    completer=compute_completers.InstancesCompleter,
    zonal_collection='compute.instances',
    zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
    plural=False)

SSH_INSTANCE_RESOLVER = compute_flags.ResourceResolver.FromMap(
    'instance', {compute_scope.ScopeEnum.ZONE: 'compute.instances'})


def GetInstanceZoneScopeLister(compute_client):
  return functools.partial(InstanceZoneScopeLister, compute_client)


def InstanceZoneScopeLister(compute_client, _, underspecified_names):
  """Scope lister for zones of underspecified instances."""
  messages = compute_client.messages
  instance_name = underspecified_names[0]
  project = properties.VALUES.core.project.Get(required=True)
  # TODO(b/33813901): look in cache if possible
  request = (compute_client.apitools_client.instances, 'AggregatedList',
             messages.ComputeInstancesAggregatedListRequest(
                 filter='name eq ^{0}$'.format(instance_name),
                 project=project,
                 maxResults=constants.MAX_RESULTS_PER_PAGE))
  errors = []
  matching_instances = compute_client.MakeRequests([request],
                                                   errors_to_collect=errors)
  zones = []
  if errors:
    # Fall back to displaying all possible zones if can't resolve
    log.debug('Errors fetching filtered aggregate list:\n{}'.format(errors))
    log.status.Print(
        'Error fetching possible zones for instance: [{0}].'.format(
            ', '.join(underspecified_names)))
    zones = zones_service.List(compute_client, project)
  elif not matching_instances:
    # Fall back to displaying all possible zones if can't resolve
    log.debug('Errors fetching filtered aggregate list:\n{}'.format(errors))
    log.status.Print(
        'Unable to find an instance with name [{0}].'.format(instance_name))
    zones = zones_service.List(compute_client, project)
  else:
    for i in matching_instances:
      zone = core_resources.REGISTRY.Parse(
          i.zone, collection='compute.zones', params={'project': project})
      zones.append(messages.Zone(name=zone.Name()))
  return {compute_scope.ScopeEnum.ZONE: zones}


def InstanceArgumentForRoute(required=True):
  return compute_flags.ResourceArgument(
      resource_name='instance',
      name='--next-hop-instance',
      completer=compute_completers.InstancesCompleter,
      required=required,
      zonal_collection='compute.instances',
      zone_explanation=ZONE_PROPERTY_EXPLANATION)


def InstanceArgumentForRouter(required=False, operation_type='added'):
  return compute_flags.ResourceArgument(
      resource_name='instance',
      name='--instance',
      completer=compute_completers.InstancesCompleter,
      required=required,
      zonal_collection='compute.instances',
      short_help='Router appliance instance of the BGP peer being {0}.'.format(
          operation_type),
      zone_explanation=ZONE_PROPERTY_EXPLANATION)


def InstanceArgumentForTargetInstance(required=True):
  return compute_flags.ResourceArgument(
      resource_name='instance',
      name='--instance',
      completer=compute_completers.InstancesCompleter,
      required=required,
      zonal_collection='compute.instances',
      short_help=('The name of the virtual machine instance that will handle '
                  'the traffic.'),
      zone_explanation=(
          'If not specified, it will be set to the same as zone.'))


def InstanceArgumentForTargetPool(action, required=True):
  return compute_flags.ResourceArgument(
      resource_name='instance',
      name='--instances',
      completer=compute_completers.InstancesCompleter,
      required=required,
      zonal_collection='compute.instances',
      short_help=('Specifies a list of instances to {0} the target pool.'
                  .format(action)),
      plural=True,
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)


def MakeSourceInstanceTemplateArg():
  """MakeSourceInstanceTemplateArg.

  Returns:
     compute_flags.ResourceArgument
  """

  return compute_flags.ResourceArgument(
      name='--source-instance-template',
      resource_name='instance template',
      completer=compute_completers.InstanceTemplatesCompleter,
      required=False,
      scope_flags_usage=compute_flags.ScopeFlagsUsage.DONT_USE_SCOPE_FLAGS,
      global_collection='compute.instanceTemplates',
      regional_collection='compute.regionInstanceTemplates',
      short_help=(
          'The name of the instance template that the instance will '
          'be created from. An instance template can be a '
          'global/regional resource.\n\nUsers can also override machine '
          'type and labels. Values of other flags will be ignored and'
          ' `--source-instance-template` will be used instead.'
      ),
  )


def AddMachineImageArg():
  return compute_flags.ResourceArgument(
      name='--source-machine-image',
      resource_name='machine image',
      completer=compute_completers.MachineImagesCompleter,
      required=False,
      global_collection='compute.machineImages',
      short_help=('The name of the machine image that the instance will '
                  'be created from.'))


def AddSourceMachineImageEncryptionKey(parser):
  parser.add_argument(
      '--source-machine-image-csek-key-file',
      metavar='FILE',
      help="""\
      Path to a Customer-Supplied Encryption Key (CSEK) key file, mapping resources to user managed keys which were used to encrypt the source machine-image.
      See {csek_help} for more details.
      """.format(csek_help=csek_utils.CSEK_HELP_URL))


def AddImageArgs(
    parser,
    enable_snapshots=False,
    support_image_family_scope=False,
    enable_instant_snapshots=False,
):
  """Adds arguments related to images for instances and instance-templates."""

  def AddImageHelp():
    """Returns the detailed help for the `--image` flag."""
    return """
          Specifies the boot image for the instances. For each
          instance, a new boot disk will be created from the given
          image. Each boot disk will have the same name as the
          instance. To view a list of public images and projects, run
          `$ gcloud compute images list`. It is best practice to use `--image`
          when a specific version of an image is needed.

          When using this option, ``--boot-disk-device-name'' and
          ``--boot-disk-size'' can be used to override the boot disk's
          device name and size, respectively.
          """

  image_parent_group = parser.add_group()
  image_group = image_parent_group.add_mutually_exclusive_group()
  image_group.add_argument('--image', help=AddImageHelp, metavar='IMAGE')
  image_utils.AddImageProjectFlag(image_parent_group)

  image_group.add_argument(
      '--image-family',
      help="""\
      The image family for the operating system that the boot disk will
      be initialized with. Compute Engine offers multiple Linux
      distributions, some of which are available as both regular and
      Shielded VM images.  When a family is specified instead of an image,
      the latest non-deprecated image associated with that family is
      used. It is best practice to use `--image-family` when the latest
      version of an image is needed.

      By default, ``{default_image_family}'' is assumed for this flag.
      """.format(default_image_family=constants.DEFAULT_IMAGE_FAMILY))
  if enable_snapshots:
    image_group.add_argument(
        '--source-snapshot',
        help="""\
        The name of the source disk snapshot that the instance boot disk
        will be created from. You can provide this as a full URL
        to the snapshot or just the snapshot name. For example, the following
        are valid values:

          * https://compute.googleapis.com/compute/v1/projects/myproject/global/snapshots/snapshot
          * snapshot
        """)
  if enable_instant_snapshots:
    image_group.add_argument(
        '--source-instant-snapshot',
        help="""\
        The name of the source disk instant snapshot that the instance boot disk
        will be created from. You can provide this as a full URL
        to the instant snapshot. For example, the following is a valid value:

          * https://compute.googleapis.com/compute/v1/projects/myproject/zones/my-zone/instantSnapshots/instant-snapshot
        """,
    )
  if support_image_family_scope:
    image_utils.AddImageFamilyScopeFlag(image_parent_group)


def AddCanIpForwardArgs(parser):
  parser.add_argument(
      '--can-ip-forward',
      action='store_true',
      help=('If provided, allows the instances to send and receive packets '
            'with non-matching destination or source IP addresses.'))


def AddPrivateIpv6GoogleAccessArg(parser, api_version):
  messages = apis.GetMessagesModule('compute', api_version)
  GetPrivateIpv6GoogleAccessTypeFlagMapper(messages).choice_arg.AddToParser(
      parser)


def AddMaintenanceInterval():
  return base.Argument(
      '--maintenance-interval',
      type=lambda x: x.upper(),
      choices={
          'PERIODIC': (
              'VMs receive infrastructure and hypervisor updates '
              'on a periodic basis, minimizing the number of'
              ' maintenance operations (live migrations or '
              'terminations) on an individual VM. Security updates'
              ' will still be applied as soon as they are '
              'available.'
          ),
          'RECURRENT': (
              'VMs receive infrastructure and hypervisor updates on a periodic'
              ' basis, minimizing the number of maintenance operations (live'
              ' migrations or terminations) on an individual VM.  This may mean'
              ' a VM will take longer to receive an update than if it was'
              ' configured for AS_NEEDED.  Security updates will'
              ' still be applied as soonas they are available.'
              ' RECURRENT is used for GEN3 and Sliceof Hardware'
              ' VMs.'
          ),
      },
      help="""
      Specifies how infrastructure upgrades should be applied to the VM.
      """,
  )


def AddMaintenanceFreezeDuration():
  return base.Argument(
      '--maintenance-freeze-duration',
      type=arg_parsers.Duration(),
      help="""
        Specifies the amount of hours after instance creation where the instance
        won't be scheduled for maintenance, e.g. `4h`, `2d6h`.
        See $ gcloud topic datetimes for information on duration formats.""")


def AddStableFleetArgs(parser):
  """Add flags related to Stable Fleet."""
  AddMaintenanceInterval().AddToParser(parser)
  AddMaintenanceFreezeDuration().AddToParser(parser)


def GetPrivateIpv6GoogleAccessTypeFlagMapper(messages):
  return arg_utils.ChoiceEnumMapper(
      '--private-ipv6-google-access-type',
      messages.Instance.PrivateIpv6GoogleAccessValueValuesEnum,
      custom_mappings={
          'INHERIT_FROM_SUBNETWORK':
              'inherit-subnetwork',
          'ENABLE_BIDIRECTIONAL_ACCESS_TO_GOOGLE':
              'enable-bidirectional-access',
          'ENABLE_OUTBOUND_VM_ACCESS_TO_GOOGLE':
              'enable-outbound-vm-access'
      },
      help_str='The private IPv6 Google access type for the VM.')


def AddPrivateIpv6GoogleAccessArgForTemplate(parser, api_version):
  messages = apis.GetMessagesModule('compute', api_version)
  GetPrivateIpv6GoogleAccessTypeFlagMapperForTemplate(
      messages).choice_arg.AddToParser(parser)


def GetPrivateIpv6GoogleAccessTypeFlagMapperForTemplate(messages):
  return arg_utils.ChoiceEnumMapper(
      '--private-ipv6-google-access-type',
      messages.InstanceProperties.PrivateIpv6GoogleAccessValueValuesEnum,
      custom_mappings={
          'INHERIT_FROM_SUBNETWORK':
              'inherit-subnetwork',
          'ENABLE_BIDIRECTIONAL_ACCESS_TO_GOOGLE':
              'enable-bidirectional-access',
          'ENABLE_OUTBOUND_VM_ACCESS_TO_GOOGLE':
              'enable-outbound-vm-access'
      },
      help_str='The private IPv6 Google access type for the VM.')


def AddLocalSsdArgs(parser):
  """Adds local SSD argument for instances and instance-templates."""

  parser.add_argument(
      '--local-ssd',
      type=arg_parsers.ArgDict(spec={
          'device-name': str,
          'interface': (lambda x: x.upper()),
      }),
      action='append',
      help="""\
      Attaches a local SSD to the instances.

      *device-name*::: Optional. A name that indicates the disk name
      the guest operating system will see. Can only be specified if
      `interface` is `SCSI`. If omitted, a device name
      of the form ``local-ssd-N'' will be used.

      *interface*::: Optional. The kind of disk interface exposed to the VM
      for this SSD.  Valid values are ``SCSI'' and ``NVME''.  SCSI is
      the default and is supported by more guest operating systems.  NVME
      might provide higher performance.
      """)


def AddLocalNvdimmArgs(parser):
  """Adds local NVDIMM argument for instances and instance-templates."""

  parser.add_argument(
      '--local-nvdimm',
      type=arg_parsers.ArgDict(spec={
          'size': arg_parsers.BinarySize(),
      }),
      action='append',
      help="""\
      Attaches a local NVDIMM to the instances.

      *size*::: Optional. Size of the NVDIMM disk. The value must be a whole
      number followed by a size unit of ``KB'' for kilobyte, ``MB'' for
      megabyte, ``GB'' for gigabyte, or ``TB'' for terabyte. For example,
      ``3TB'' will produce a 3 terabyte disk. Allowed values are: 3TB and 6TB
      and the default is 3 TB.
      """)


def AddLocalSsdArgsWithSize(parser):
  """Adds local SSD argument for instances and instance-templates."""

  # The size argument has been repurposed for Large Local SSD (go/galactus),
  # and is available for select customers only, which is why any help_text
  # is removed.

  parser.add_argument(
      '--local-ssd',
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'interface': (lambda x: x.upper()),
              'size':
                  arg_parsers.BinarySize(
                      lower_bound='375GB', upper_bound='3000GB'),
          }),
      action='append',
      help="""\
      Attaches a local SSD to the instances.

      *device-name*::: Optional. A name that indicates the disk name
      the guest operating system will see. Can only be specified if `interface`
      is `SCSI`. If omitted, a device name
      of the form ``local-ssd-N'' will be used.

      *interface*::: Optional. The kind of disk interface exposed to the VM
      for this SSD.  Valid values are ``SCSI'' and ``NVME''.  SCSI is
      the default and is supported by more guest operating systems.  NVME
      might provide higher performance.

      *size*::: Optional. The only valid value is ``375GB''. Specify the
      ``--local-ssd'' flag multiple times if you need multiple ``375GB'' local
      SSD partitions. You can specify a maximum of 24 local SSDs for a maximum
      of ``9TB'' attached to an instance.
      """)


def GetDiskDeviceNameHelp(container_mount_enabled=False):
  """Helper to get documentation for "device-name" param of disk spec."""
  if container_mount_enabled:
    return (
        'An optional name to display the disk name in the guest operating '
        'system. Must be the same as `name` if used with '
        '`--container-mount-disk`. If omitted, a device name of the form '
        '`persistent-disk-N` is used. If omitted and used with '
        '`--container-mount-disk` (where the `name` of the container mount '
        'disk is the same as in this flag), a device name equal to disk `name` '
        'is used.')
  else:
    return ('An optional name to display the disk name in the guest '
            'operating system. If omitted, a device name of the form '
            '`persistent-disk-N` is used.')


def AddDiskArgs(parser,
                enable_regional_disks=False,
                enable_kms=False,
                container_mount_enabled=False):
  """Adds arguments related to disks for instances and instance-templates."""

  disk_device_name_help = GetDiskDeviceNameHelp(
      container_mount_enabled=container_mount_enabled)

  AddBootDiskArgs(parser, enable_kms)

  disk_arg_spec = {
      'name': str,
      'mode': str,
      'boot': arg_parsers.ArgBoolean(),
      'device-name': str,
      'auto-delete': arg_parsers.ArgBoolean(),
  }

  if enable_regional_disks:
    disk_arg_spec['scope'] = str
    disk_arg_spec['force-attach'] = arg_parsers.ArgBoolean()

  disk_help = """
      Attaches an existing persistent disk to the instances.

      *name*::: The disk to attach to the instances. If you create more than
      one instance, you can only attach a disk in read-only mode. By default,
      you attach a zonal persistent disk located in the same zone of the
      instance. If you want to attach a regional persistent disk, you must
      specify the disk using its URI; for example,
      ``projects/myproject/regions/us-central1/disks/my-regional-disk''.

      *mode*::: The mode of the disk. Supported options are ``ro'' for read-only
      mode and ``rw'' for read-write mode. If omitted, ``rw'' is used as
      a default value. If you use ``rw'' when creating more than one instance,
      you encounter errors.

      *boot*::: If set to ``yes'', you attach a boot disk. The
      virtual machine then uses the first partition of the disk for
      the root file systems. The default value for this is ``no''.

      *device-name*::: {}

      *auto-delete*::: If set to ``yes'', the persistent disk is
      automatically deleted when the instance is deleted. However,
      if you detach the disk from the instance, deleting the instance
      doesn't delete the disk. The default value for this is ``yes''.
      """.format(disk_device_name_help)
  if enable_regional_disks:
    disk_help += """
      *scope*::: Can be `zonal` or `regional`. If ``zonal'', the disk is
      interpreted as a zonal disk in the same zone as the instance (default).
      If ``regional'', the disk is interpreted as a regional disk in the same
      region as the instance. The default value for this is ``zonal''.
      *force-attach*::: If ``yes'',  this persistent disk will force-attached to
      the instance even it is already attached to another instance. The default
      value is 'no'.
      """

  parser.add_argument(
      '--disk',
      type=arg_parsers.ArgDict(spec=disk_arg_spec),
      action='append',
      help=disk_help)


def AddBootDiskArgs(parser, enable_kms=False):
  """Adds boot disk args."""
  parser.add_argument(
      '--boot-disk-device-name',
      help="""\
      The name the guest operating system will see for the boot disk.  This
      option can only be specified if a new boot disk is being created (as
      opposed to mounting an existing persistent disk).
      """)
  parser.add_argument(
      '--boot-disk-size',
      type=arg_parsers.BinarySize(lower_bound='1GB'),
      help="""\
      The size of the boot disk. This option can only be specified if a new
      boot disk is being created (as opposed to mounting an existing
      persistent disk). The value must be a whole number followed by a size
      unit of ``KB'' for kilobyte, ``MB'' for megabyte, ``GB'' for gigabyte,
      or ``TB'' for terabyte. For example, ``10GB'' will produce a 10 gigabyte
      disk. Disk size must be a multiple of 1 GB.  Default size unit is ``GB''.
      """)

  parser.add_argument(
      '--boot-disk-type',
      help="""\
      The type of the boot disk. This option can only be specified if a new boot
      disk is being created (as opposed to mounting an existing persistent
      disk). To get a list of available disk types, run
      `$ gcloud compute disk-types list`.
      """)

  parser.add_argument(
      '--boot-disk-auto-delete',
      action='store_true',
      default=True,
      help='Automatically delete boot disks when their instances are deleted.')

  parser.add_argument(
      '--boot-disk-provisioned-iops',
      type=arg_parsers.BoundedInt(10000, 120000),
      help="""\
      Indicates how many IOPS to provision for the disk. This sets the number
      of I/O operations per second that the disk can handle. Value must be
      between 10,000 and 120,000.
      """)

  parser.add_argument(
      '--boot-disk-provisioned-throughput',
      type=arg_parsers.BoundedInt(),
      help="""\
      Indicates how much throughput to provision for the disk. This sets the
      number of throughput mb per second that the disk can handle.
      """,
  )

  if enable_kms:
    kms_resource_args.AddKmsKeyResourceArg(
        parser, 'disk', boot_disk_prefix=True)


def AddInstanceKmsArgs(parser):
  kms_resource_args.AddKmsKeyResourceArg(
      parser, 'instance', instance_prefix=True)


def AddCreateDiskArgs(
    parser,
    enable_kms=False,
    enable_snapshots=False,
    container_mount_enabled=False,
    source_snapshot_csek=False,
    image_csek=False,
    include_name=True,
    support_boot=False,
    support_multi_writer=False,
    support_replica_zones=True,
    support_storage_pool=False,
    enable_source_instant_snapshots=False,
    enable_confidential_compute=False,
):
  """Adds create-disk argument for instances and instance-templates."""

  disk_device_name_help = GetDiskDeviceNameHelp(
      container_mount_enabled=container_mount_enabled)
  disk_name_extra_help = '' if not container_mount_enabled else (
      ' Must specify this option if attaching the disk '
      'to a container with `--container-mount-disk`.')
  disk_mode_extra_help = '' if not container_mount_enabled else (
      ' It is an error to create a disk in `ro` mode '
      'if attaching it to a container with `--container-mount-disk`.')

  disk_help = """\
      Creates and attaches persistent disks to the instances.

      *name*::: Specifies the name of the disk. This option cannot be
      specified if more than one instance is being created.{disk_name}

      *description*::: Optional textual description for the disk being created.

      *mode*::: Specifies the mode of the disk. Supported options
      are ``ro'' for read-only and ``rw'' for read-write. If
      omitted, ``rw'' is used as a default.{disk_mode}

      *image*::: Specifies the name of the image that the disk will be
      initialized with. A new disk will be created based on the given
      image. To view a list of public images and projects, run
      `$ gcloud compute images list`. It is best practice to use image when
      a specific version of an image is needed. If both image and image-family
      flags are omitted a blank disk will be created.

      *image-family*::: The image family for the operating system that the boot
      disk will be initialized with. Compute Engine offers multiple Linux
      distributions, some of which are available as both regular and
      Shielded VM images.  When a family is specified instead of an image,
      the latest non-deprecated image associated with that family is
      used. It is best practice to use --image-family when the latest
      version of an image is needed.

      *image-project*::: The Google Cloud project against which all image and
      image family references will be resolved. It is best practice to define
      image-project. A full list of available image projects can be generated by
      running `gcloud compute images list`.

        * If specifying one of our public images, image-project must be
          provided.
        * If there are several of the same image-family value in multiple
          projects, image-project must be specified to clarify the image to be
          used.
        * If not specified and either image or image-family is provided, the
          current default project is used.

      *size*::: The size of the disk. The value must be a whole number
      followed by a size unit of ``KB'' for kilobyte, ``MB'' for
      megabyte, ``GB'' for gigabyte, or ``TB'' for terabyte. For
      example, ``10GB'' will produce a 10 gigabyte disk. Disk size must
      be a multiple of 1 GB. If not specified, the default image size
      will be used for the new disk.

      *type*::: The type of the disk. To get a list of available disk
      types, run $ gcloud compute disk-types list. The default disk type
      is ``pd-standard''.

      *device-name*::: {disk_device}

      *provisioned-iops*::: Indicates how many IOPS to provision for the disk.
      This sets the number of I/O operations per second that the disk can
      handle. Value must be between 10,000 and 120,000.

      *provisioned-throughput*::: Indicates how much throughput to provision for
      the disk. This sets the number of throughput mb per second that the disk
      can handle.

      *disk-resource-policy*::: Resource policy to apply to the disk. Specify a full or partial URL. For example:
        * ``https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/resourcePolicies/my-resource-policy''
        * ``projects/my-project/regions/us-central1/resourcePolicies/my-resource-policy''

      For more information, see the following docs:
        * https://cloud.google.com/sdk/gcloud/reference/beta/compute/resource-policies/
        * https://cloud.google.com/compute/docs/disks/scheduled-snapshots

      *auto-delete*::: If ``yes'', this persistent disk will be
      automatically deleted when the instance is deleted. However,
      if the disk is later detached from the instance, this option
      won't apply. The default value for this is ``yes''.

      *architecture*::: Specifies the architecture or processor type that this
      disk can support. For available processor types on Compute Engine, see
      https://cloud.google.com/compute/docs/cpu-platforms.
      """.format(
          disk_name=disk_name_extra_help,
          disk_mode=disk_mode_extra_help,
          disk_device=disk_device_name_help)
  if support_boot:
    disk_help += """
      *boot*::: If ``yes'', indicates that this is a boot disk. The
      instance will use the first partition of the disk for
      its root file system. The default value for this is ``no''.
    """
  if enable_kms:
    disk_help += """
      *kms-key*::: Fully qualified Cloud KMS cryptokey name that will
      protect the {resource}.

      This can either be the fully qualified path or the name.

      The fully qualified Cloud KMS cryptokey name format is:
      ``projects/<kms-project>/locations/<kms-location>/keyRings/<kms-keyring>/
      cryptoKeys/<key-name>''.

      If the value is not fully qualified then kms-location, kms-keyring, and
      optionally kms-project are required.

      See {kms_help} for more details.

      *kms-project*::: Project that contains the Cloud KMS cryptokey that will
      protect the {resource}.

      If the project is not specified then the project where the {resource} is
      being created will be used.

      If this flag is set then key-location, kms-keyring, and kms-key
      are required.

      See {kms_help} for more details.

      *kms-location*::: Location of the Cloud KMS cryptokey to be used for
      protecting the {resource}.

      All Cloud KMS cryptokeys are reside in a 'location'.
      To get a list of possible locations run 'gcloud kms locations list'.
      If this flag is set then kms-keyring and kms-key are required.
      See {kms_help} for more details.

      *kms-keyring*::: The keyring which contains the Cloud KMS cryptokey that
      will protect the {resource}.

      If this flag is set then kms-location and kms-key are required.

      See {kms_help} for more details.
      """.format(
          resource='disk', kms_help=kms_utils.KMS_HELP_URL)
  spec = {
      'description': str,
      'mode': str,
      'image': str,
      'image-family': str,
      'image-project': str,
      'size': arg_parsers.BinarySize(lower_bound='1GB'),
      'type': str,
      'device-name': str,
      'auto-delete': arg_parsers.ArgBoolean(),
      'provisioned-iops': int,
      'provisioned-throughput': int,
      'disk-resource-policy': arg_parsers.ArgList(max_length=1),
      'architecture': str,
  }

  if include_name:
    spec['name'] = str

  if enable_kms:
    spec['kms-key'] = str
    spec['kms-project'] = str
    spec['kms-location'] = str
    spec['kms-keyring'] = str

  if support_boot:
    spec['boot'] = arg_parsers.ArgBoolean()

  if enable_snapshots:
    disk_help += """
      *source-snapshot*::: The source disk snapshot that will be used to
      create the disk. You can provide this as a full URL
      to the snapshot or just the snapshot name. For example, the following
      are valid values:

        * https://compute.googleapis.com/compute/v1/projects/myproject/global/snapshots/snapshot
        * snapshot
      """
    spec['source-snapshot'] = str

  if source_snapshot_csek:
    disk_help += """
      *source-snapshot-csek-required*::: The CSK protected source disk snapshot
      that will be used to create the disk. This can be provided as a full URL
      to the snapshot or just the snapshot name. Must be specified with
      `source-snapshot-csek-key-file`. The following are valid values:

        * https://www.googleapis.com/compute/v1/projects/myproject/global/snapshots/snapshot
        * snapshot

      *source-snapshot-csek-key-file*::: Path to a Customer-Supplied Encryption
      Key (CSEK) key file for the source snapshot. Must be specified with
      `source-snapshot-csek-required`.
      """
    spec['source-snapshot-csek-key-file'] = str

  if enable_source_instant_snapshots:
    disk_help += """
      *source-instant-snapshot*::: The source disk instant snapshot that will be used to
      create the disk. You can provide this as a full URL
      to the instant snapshot. For example, the following is a valid value:

        * https://compute.googleapis.com/compute/v1/projects/myproject/zones/myzone/instantSnapshots/instantSnapshot
      """
    spec['source-instant-snapshot'] = str

  if image_csek:
    disk_help += """
      *image-csek-required*::: Specifies the name of the CSK protected image
      that the disk will be initialized with. A new disk will be created based
      on the given image. To view a list of public images and projects, run
      `$ gcloud compute images list`. It is best practice to use image when
      a specific version of an image is needed. If both image and image-family
      flags are omitted a blank disk will be created. Must be specified with
      `image-csek-key-file`.

      *image-csek-key-file*::: Path to a Customer-Supplied Encryption Key (CSEK)
      key file for the image. Must be specified with `image-csek-required`.
    """
    spec['image-csek-key-file'] = str

  if support_multi_writer:
    spec['multi-writer'] = arg_parsers.ArgBoolean()
    disk_help += """
      *multi-writer*::: If ``yes'', the disk is created in multi-writer mode so
      that it can be attached with read-write access to two VMs. The
      default value is ``no''.
      The multi-writer feature requires specialized filesystems, among other
      restrictions. For more information, see
      https://cloud.google.com/compute/docs/disks/sharing-disks-between-vms.
    """

  if enable_confidential_compute:
    spec['confidential-compute'] = arg_parsers.ArgBoolean()
    disk_help += """
      *confidential-compute*::: If ``yes'', the disk is created in confidential
      mode. The default value is ``no''. Encryption with a Cloud KMS key is required to enable this option.
    """

  if support_replica_zones:
    disk_help += """
      *replica-zones*::: Required for each regional disk associated with the
      instance. Specify the URLs of the zones where the disk should be
      replicated to. You must provide exactly two replica zones, and one zone
      must be the same as the instance zone.
    """
    spec['replica-zones'] = arg_parsers.ArgList(max_length=2)

  if support_storage_pool:
    spec['storage-pool'] = str
    disk_help += """
      *storage-pool*::: The name of the storage pool in which the new disk is
      created. The new disk and the storage pool must be in the same location.
    """

  parser.add_argument(
      '--create-disk',
      type=arg_parsers.ArgDict(spec=spec),
      action='append',
      metavar='PROPERTY=VALUE',
      help=disk_help,
  )


def AddCustomMachineTypeArgs(parser):
  """Adds arguments related to custom machine types for instances."""
  custom_group = parser.add_group(help='Custom machine type extensions.')
  custom_group.add_argument(
      '--custom-cpu',
      type=NonEmptyString('--custom-cpu'),
      required=True,
      help="""\
      A whole number value specifying the number of cores that are needed in
      the custom machine type.

      For some machine types, shared-core values can also be used. For
      example, for E2 machine types, you can specify `micro`, `small`, or
      `medium`.
      """)
  custom_group.add_argument(
      '--custom-memory',
      type=arg_parsers.BinarySize(),
      required=True,
      help="""\
      A whole number value indicating how much memory is desired in the custom
      machine type. A size unit should be provided (eg. 3072MB or 9GB) - if no
      units are specified, GB is assumed.
      """)
  custom_group.add_argument(
      '--custom-extensions',
      action='store_true',
      help='Use the extended custom machine type.')
  custom_group.add_argument(
      '--custom-vm-type',
      help="""
      Specifies a custom machine type. The default is `n1`. For more information about custom machine types, see:
      https://cloud.google.com/compute/docs/general-purpose-machines#custom_machine_types
      """)


def _GetAddress(compute_client, address_ref):
  """Returns the address resource corresponding to the given reference.

  Args:
    compute_client: GCE API client,
    address_ref: resource reference to reserved IP address

  Returns:
    GCE reserved IP address resource
  """
  errors = []
  messages = compute_client.messages
  compute = compute_client.apitools_client
  res = compute_client.MakeRequests(
      requests=[(compute.addresses, 'Get',
                 messages.ComputeAddressesGetRequest(
                     address=address_ref.Name(),
                     project=address_ref.project,
                     region=address_ref.region))],
      errors_to_collect=errors)
  return res[0]


def ExpandAddressFlag(resources, compute_client, address, region):
  """Resolves the --address flag value.

  If the value of --address is a name, the regional address is queried.

  Args:
    resources: resources object,
    compute_client: GCE API client,
    address: The command-line flags. The flag accessed is --address,
    region: The region.

  Returns:
    If an --address is given, the resolved IP address; otherwise None.
  """
  if not address:
    return None

  # Try interpreting the address as IPv4 or IPv6.
  try:
    # ipaddress only allows unicode input
    ipaddress.ip_address(six.text_type(address))
    return address
  except ValueError:
    # ipaddress could not resolve as an IPv4 or IPv6 address.
    pass

  # Lookup the address.
  address_ref = GetAddressRef(resources, address, region)
  res = _GetAddress(compute_client, address_ref)
  return res.address


def GetAddressRef(resources, address, region):
  """Generates an address reference from the specified address and region."""
  return resources.Parse(
      address,
      collection='compute.addresses',
      params={
          'project': properties.VALUES.core.project.GetOrFail,
          'region': region
      })


def ValidateDiskFlags(
    args,
    enable_kms=False,
    enable_snapshots=False,
    enable_source_snapshot_csek=False,
    enable_image_csek=False,
    enable_source_instant_snapshot=False,
):
  """Validates the values of all disk-related flags."""
  ValidateDiskCommonFlags(args)
  ValidateDiskAccessModeFlags(args)
  ValidateDiskBootFlags(args, enable_kms=enable_kms)
  ValidateCreateDiskFlags(
      args,
      enable_snapshots=enable_snapshots,
      enable_source_snapshot_csek=enable_source_snapshot_csek,
      enable_image_csek=enable_image_csek,
      enable_source_instant_snapshot=enable_source_instant_snapshot,
  )


def ValidateDiskCommonFlags(args):
  """Validates the values of common disk-related flags."""

  for disk in args.disk or []:
    disk_name = disk.get('name')
    if not disk_name:
      raise exceptions.InvalidArgumentException(
          '--disk',
          '[name] is missing in [--disk]. [--disk] value must be of the form '
          '[{0}].'.format(DISK_METAVAR))

    mode_value = disk.get('mode')
    if mode_value and mode_value not in ('rw', 'ro'):
      raise exceptions.InvalidArgumentException(
          '--disk',
          'Value for [mode] in [--disk] must be [rw] or [ro], not [{0}].'
          .format(mode_value))


def ValidateDiskAccessModeFlags(args):
  """Checks disks R/O and R/W access mode."""
  for disk in args.disk or []:
    disk_name = disk.get('name')
    mode_value = disk.get('mode')
    # Ensures that the user is not trying to attach a read-write
    # disk to more than one instance.
    if len(args.instance_names) > 1 and mode_value == 'rw':
      raise exceptions.BadArgumentException(
          '--disk',
          'Cannot attach disk [{0}] in read-write mode to more than one '
          'instance.'.format(disk_name))


def GetNumOfBootDisk(disks):
  """get number of boot disks in list of disks."""
  num_of_boot_disk = 0
  for disk in disks or []:
    if disk.get('boot', False):
      num_of_boot_disk += 1
  return num_of_boot_disk


def ValidateDiskBootFlags(args, enable_kms=False):
  """Validates the values of boot disk-related flags."""
  boot_disk_specified = False
  num_of_boot_disk_in_disks = GetNumOfBootDisk(args.disk)
  # we need to fail because only one boot disk can be attached.
  if num_of_boot_disk_in_disks > 1:
    raise exceptions.BadArgumentException(
        '--disk', 'Each instance can have exactly one boot disk. At least two '
        'boot disks were specified through [--disk].')

  num_of_boot_disk_in_create_disks = GetNumOfBootDisk(args.create_disk)
  if num_of_boot_disk_in_create_disks > 1:
    raise exceptions.BadArgumentException(
        '--create-disk',
        'Each instance can have exactly one boot disk. At least two '
        'boot disks were specified through [--create-disk].')

  if (num_of_boot_disk_in_create_disks + num_of_boot_disk_in_disks) > 1:
    raise exceptions.BadArgumentException(
        '--create-disk',
        'Each instance can have exactly one boot disk. At least two '
        'boot disks were specified through [--disk and --create-disk].')

  if (num_of_boot_disk_in_create_disks + num_of_boot_disk_in_disks) == 1:
    boot_disk_specified = True

  if args.IsSpecified('boot_disk_provisioned_iops'):
    if not args.IsSpecified(
        'boot_disk_type'
    ) or not disks_util.IsProvisioningTypeIops(args.boot_disk_type):
      raise exceptions.InvalidArgumentException(
          '--boot-disk-provisioned-iops',
          '--boot-disk-provisioned-iops cannot be used with the given disk '
          'type.',
      )

  if args.IsSpecified('boot_disk_provisioned_throughput'):
    if not args.IsSpecified(
        'boot_disk_type'
    ) or not disks_util.IsProvisioningTypeThroughput(args.boot_disk_type):
      raise exceptions.InvalidArgumentException(
          '--boot-disk-provisioned-throughput',
          '--boot-disk-provisioned-throughput cannot be used with the given'
          ' disk type.',
      )

  if args.IsSpecified('boot_disk_size'):
    size_gb = utils.BytesToGb(args.boot_disk_size)
    if (
        args.IsSpecified('boot_disk_type')
        and args.boot_disk_type in constants.LEGACY_DISK_TYPE_LIST
        and size_gb < 10
    ):
      raise exceptions.InvalidArgumentException(
          '--boot-disk-size',
          'Value must be greater than or equal to 10 GB; reveived {0} GB'
          .format(size_gb),
      )

  if args.image and boot_disk_specified:
    raise exceptions.BadArgumentException(
        '--disk', 'Each instance can have exactly one boot disk. One boot disk '
        'was specified through [--disk or --create-disk]'
        ' and another through [--image].')

  if boot_disk_specified:
    if args.boot_disk_device_name:
      raise exceptions.BadArgumentException(
          '--boot-disk-device-name',
          'Each instance can have exactly one boot disk. '
          'One boot disk was specified through [--disk or --create-disk]')

    if args.boot_disk_type:
      raise exceptions.BadArgumentException(
          '--boot-disk-type', 'Each instance can have exactly one boot disk. '
          'One boot disk was specified through [--disk or --create-disk]')

    if args.boot_disk_size:
      raise exceptions.BadArgumentException(
          '--boot-disk-size', 'Each instance can have exactly one boot disk. '
          'One boot disk was specified through [--disk or --create-disk]')

    if not args.boot_disk_auto_delete:
      raise exceptions.BadArgumentException(
          '--no-boot-disk-auto-delete',
          'Each instance can have exactly one boot disk. '
          'One boot disk was specified through [--disk or --create-disk]')

    if enable_kms:
      if args.boot_disk_kms_key:
        raise exceptions.BadArgumentException(
            '--boot-disk-kms-key',
            'Each instance can have exactly one boot disk. '
            'One boot disk was specified through [--disk or --create-disk]')

      if args.boot_disk_kms_keyring:
        raise exceptions.BadArgumentException(
            '--boot-disk-kms-keyring',
            'Each instance can have exactly one boot disk. '
            'One boot disk was specified through [--disk or --create-disk]')

      if args.boot_disk_kms_location:
        raise exceptions.BadArgumentException(
            '--boot-disk-kms-location',
            'Each instance can have exactly one boot disk. '
            'One boot disk was specified through [--disk or --create-disk]')

      if args.boot_disk_kms_project:
        raise exceptions.BadArgumentException(
            '--boot-disk-kms-project',
            'Each instance can have exactly one boot disk. '
            'One boot disk was specified through [--disk or --create-disk]')


def ValidateCreateDiskFlags(
    args,
    enable_snapshots=False,
    enable_source_snapshot_csek=False,
    enable_image_csek=False,
    include_name=True,
    enable_source_instant_snapshot=False,
):
  """Validates the values of create-disk related flags."""
  require_csek_key_create = getattr(args, 'require_csek_key_create', None)
  csek_key_file = getattr(args, 'csek_key_file', None)
  resource_names = getattr(args, 'names', [])

  for disk in getattr(args, 'create_disk', []) or []:
    disk_name = disk.get('name')
    if include_name and len(resource_names) > 1 and disk_name:
      raise exceptions.BadArgumentException(
          '--disk',
          'Cannot create a disk with [name]={} for more than one instance.'
          .format(disk_name))
    if disk_name and require_csek_key_create and csek_key_file:
      raise exceptions.BadArgumentException(
          '--disk',
          'Cannot create a disk with customer supplied key when disk name '
          'is not specified.')

    mode_value = disk.get('mode')
    if mode_value and mode_value not in ('rw', 'ro'):
      raise exceptions.InvalidArgumentException(
          '--disk',
          'Value for [mode] in [--disk] must be [rw] or [ro], not [{0}].'
          .format(mode_value))

    image_value = disk.get('image')
    image_family_value = disk.get('image-family')
    source_snapshot = disk.get('source-snapshot')
    image_csek_file = disk.get('image_csek')
    source_snapshot_csek_file = disk.get('source_snapshot_csek_file')
    source_instant_snapshot = disk.get('source-instant-snapshot')

    disk_source = set()
    if image_value:
      disk_source.add(image_value)
    if image_family_value:
      disk_source.add(image_family_value)
    if source_snapshot:
      disk_source.add(source_snapshot)
    if image_csek_file:
      disk_source.add(image_csek_file)
    if source_snapshot_csek_file:
      disk_source.add(source_snapshot_csek_file)
    if source_instant_snapshot:
      disk_source.add(source_instant_snapshot)

    mutex_attributes = ['[image]', '[image-family]']
    if enable_image_csek:
      mutex_attributes.append('[image-csek-required]')
    if enable_snapshots:
      mutex_attributes.append('[source-snapshot]')
    if enable_source_snapshot_csek:
      mutex_attributes.append('[source-snapshot-csek-required]')
    if enable_source_instant_snapshot:
      mutex_attributes.append('[source-instant-snapshot]')
    formatted_attributes = '{}, or {}'.format(', '.join(mutex_attributes[:-1]),
                                              mutex_attributes[-1])
    source_error_message = (
        'Must specify exactly one of {} for a '
        '[--create-disk]. These fields are mutually exclusive.'.format(
            formatted_attributes))
    if len(disk_source) > 1:
      raise compute_exceptions.ArgumentError(source_error_message)


def ValidateImageFlags(args):
  """Validates the image flags."""
  if args.image_project and not (args.image or args.image_family):
    raise compute_exceptions.ArgumentError(
        'Must specify either [--image] or [--image-family] when specifying '
        '[--image-project] flag.')


def _ValidateNetworkInterfaceStackType(stack_type_input):
  """Validates stack type field, throws exception if invalid."""
  stack_type = stack_type_input.upper()
  if stack_type in constants.NETWORK_INTERFACE_STACK_TYPE_CHOICES:
    return stack_type
  else:
    raise exceptions.InvalidArgumentException(
        '--network-interface',
        'Invalid value for stack-type [%s].' % stack_type)


def _ValidateNetworkInterfaceStackTypeIpv6OnlyNotSupported(stack_type_input):
  """Validates stack type field, throws exception if invalid."""
  stack_type = stack_type_input.upper()
  if (stack_type in constants.NETWORK_INTERFACE_STACK_TYPE_CHOICES and
      stack_type != constants.NETWORK_INTERFACE_IPV6_ONLY_STACK_TYPE):
    return stack_type
  else:
    raise exceptions.InvalidArgumentException(
        '--network-interface',
        'Invalid value for stack-type [%s].' % stack_type)


def _ValidateNetworkInterfaceIgmpQuery(igmp_query_input):
  """Validates igmp query field, throws exception if invalid."""
  igmp_query = igmp_query_input.upper()
  if igmp_query in constants.NETWORK_INTERFACE_IGMP_QUERY_CHOICES:
    return igmp_query
  else:
    raise exceptions.InvalidArgumentException(
        '--network-interface',
        f'Invalid value for igmp-query [{igmp_query}].')


def _ValidateNetworkTier(network_tier_input):
  """Validates network tier field, throws exception if invalid."""
  network_tier = network_tier_input.upper()
  if network_tier in constants.NETWORK_TIER_CHOICES_FOR_INSTANCE:
    return network_tier
  else:
    raise exceptions.InvalidArgumentException('--network-interface',
                                              'Invalid value for network-tier')


def _ValidateNetworkInterfaceIpv6NetworkTier(ipv6_network_tier_input):
  """Validates IPv6 network tier field, throws exception if invalid."""
  ipv6_network_tier = ipv6_network_tier_input.upper()
  if (ipv6_network_tier
      in constants.NETWORK_INTERFACE_IPV6_NETWORK_TIER_CHOICES):
    return ipv6_network_tier
  else:
    raise exceptions.InvalidArgumentException(
        '--network-interface',
        'Invalid value for ipv6-network-tier [%s].' % ipv6_network_tier)


def ValidateNetworkInterfaceNicType(nic_type_input):
  """Validates network interface type field, throws exception if invalid."""
  nic_type = nic_type_input.upper()
  if nic_type in constants.NETWORK_INTERFACE_NIC_TYPE_CHOICES:
    return nic_type
  else:
    raise exceptions.InvalidArgumentException(
        '--network-interface', 'Invalid value for nic-type [%s]' % nic_type)


def AddAddressArgs(parser,
                   instances=True,
                   support_subinterface=False,
                   instance_create=False,
                   containers=False,
                   support_network_queue_count=False,
                   support_network_attachments=False,
                   support_vlan_nic=False,
                   support_ipv6_only=False,
                   support_igmp_query=False):
  """Adds address arguments for instances and instance-templates.

  Args:
    parser: gcloud command arguments parser.
    instances: adds address arguments for instances if set to true, for instance
      templates elsewise.
    support_subinterface: indicates subinterface is supported or not.
    instance_create: adds address arguments for instance creation if set to
      true.
    containers: adds address arguments for create-with-containers command if set
      to true, for create command otherwise.
    support_network_queue_count: indicates flexible networking queue count is
      supported or not.
    support_network_attachments: indicates whether network attachments are
      supported.
    support_vlan_nic: indicates whether VLAN network interfaces are supported.
    support_ipv6_only: indicates whether IPV6_ONLY stack type is supported.
    support_igmp_query: indicates whether setting igmp query on network
      interfaces is supported.
  """
  addresses = parser.add_mutually_exclusive_group()
  AddNoAddressArg(addresses)
  if instances:
    address_help = """\
        Assigns the given external address to the instance that is created.
        The address might be an IP address or the name or URI of an address
        resource. This option can only be used when creating a single instance.
        """
  else:
    address_help = """\
        Assigns the given external IP address to the instance that is created.
        This option can only be used when creating a single instance.
        """
  addresses.add_argument('--address', help=address_help)
  multiple_network_interface_cards_spec = {
      'address': str,
      'network': str,
      'no-address': None,
      'subnet': str,
      'private-network-ip': str,
      'aliases': str,
      'network-attachment': str,
      'ipv6-address': str,
      'ipv6-prefix-length': int,
      'external-ipv6-address': str,
      'external-ipv6-prefix-length': int,
      'internal-ipv6-address': str,
      'internal-ipv6-prefix-length': int
  }

  multiple_network_interface_cards_spec['network-tier'] = _ValidateNetworkTier

  multiple_network_interface_cards_spec[
      'nic-type'] = ValidateNetworkInterfaceNicType

  multiple_network_interface_cards_spec[
      'igmp-query'] = _ValidateNetworkInterfaceIgmpQuery

  network_interface_help_texts = []
  # IPv6 related fields are not supported in create-with-container commands yet.
  if not containers:
    multiple_network_interface_cards_spec['ipv6-public-ptr-domain'] = str
    if support_ipv6_only:
      multiple_network_interface_cards_spec[
          'stack-type'] = _ValidateNetworkInterfaceStackType
    else:
      multiple_network_interface_cards_spec[
          'stack-type'] = _ValidateNetworkInterfaceStackTypeIpv6OnlyNotSupported
    multiple_network_interface_cards_spec[
        'ipv6-network-tier'] = _ValidateNetworkInterfaceIpv6NetworkTier
    network_interface_help_texts.append("""\
      Adds a network interface to the instance. Mutually exclusive with any
      of these flags: *--address*, *--network*, *--network-tier*, *--subnet*,
      *--private-network-ip*, *--stack-type*, *--ipv6-network-tier*,
      *--ipv6-public-ptr-domain*, *--internal-ipv6-address*,
      *--internal-ipv6-prefix-length*, *--ipv6-address*, *--ipv6-prefix-length*,
      *--external-ipv6-address*, *--external-ipv6-prefix-length*.
      This flag can be repeated to specify multiple network interfaces.
    """)
  else:
    network_interface_help_texts.append("""\
      Adds a network interface to the instance. Mutually exclusive with any
      of these flags: *--address*, *--network*, *--network-tier*, *--subnet*,
      *--private-network-ip*. This flag can be repeated to specify multiple
      network interfaces.
    """)
  network_interface_help_texts.append("""
      The following keys are allowed:
      *address*::: Assigns the given external address to the instance that is
      created. Specifying an empty string will assign an ephemeral IP.
      Mutually exclusive with no-address. If neither key is present the
      instance will get an ephemeral IP.

      *network*::: Specifies the network that the interface will be part of.
      If subnet is also specified it must be subnetwork of this network. If
      neither is specified, this defaults to the "default" network.

      *no-address*::: If specified the interface will have no external IP.
      Mutually exclusive with address. If neither key is present the
      instance will get an ephemeral IP.

      *network-tier*::: Specifies the network tier of the interface.
      ``NETWORK_TIER'' must be one of: `PREMIUM`, `STANDARD`, `FIXED_STANDARD`.
      The default value is `PREMIUM`.

      *private-network-ip*::: Assigns the given RFC1918 IP address to the
      interface.

      *subnet*::: Specifies the subnet that the interface will be part of.
      If network key is also specified this must be a subnetwork of the
      specified network.

      *nic-type*::: Specifies the  Network Interface Controller (NIC) type for
      the interface. ``NIC_TYPE'' must be one of: `GVNIC`, `VIRTIO_NET`.
      """)

  if support_network_queue_count:
    multiple_network_interface_cards_spec['queue-count'] = int
    network_interface_help_texts.append("""
      *queue-count*::: Specifies the networking queue count for this interface.
      Both Rx and Tx queues will be set to this number. If it's not specified,
      a default queue count will be assigned. See
      https://cloud.google.com/compute/docs/network-bandwidth#rx-tx for
      more details.
      """)

  if not containers:
    if support_ipv6_only:
      stack_types = '`IPV4_ONLY`, `IPV4_IPV6`, `IPV6_ONLY`'
    else:
      stack_types = '`IPV4_ONLY`, `IPV4_IPV6`'
    network_interface_help_texts.append(f"""
      *stack-type*::: Specifies whether IPv6 is enabled on the interface.
      ``STACK_TYPE'' must be one of: {stack_types}.
      The default value is `IPV4_ONLY`.
    """)
    network_interface_help_texts.append("""
      *ipv6-network-tier*::: Specifies the IPv6 network tier that will be used
      to configure the instance network interface IPv6 access config.
      ``IPV6_NETWORK_TIER'' must be `PREMIUM` (currently only one value is
      supported).

      *ipv6-public-ptr-domain*::: Assigns a custom PTR domain for the external
      IPv6 in the IPv6 access configuration of instance. If its value is not
      specified, the default PTR record will be used. This option can only be
      specified for the default network interface, `nic0`.
    """)

  network_interface_help_texts.append("""
      *aliases*::: Specifies the IP alias ranges to allocate for this
      interface.  If there are multiple IP alias ranges, they are separated
      by semicolons.

      For example:

          --aliases="10.128.1.0/24;range1:/32"

      """)
  if instances:
    network_interface_help_texts.append("""
      Each IP alias range consists of a range name and an IP range
      separated by a colon, or just the IP range.
      The range name is the name of the range within the network
      interface's subnet from which to allocate an IP alias range. If
      unspecified, it defaults to the primary IP range of the subnet.
      The IP range can be a CIDR range (e.g. `192.168.100.0/24`), a single
      IP address (e.g. `192.168.100.1`), or a netmask in CIDR format (e.g.
      `/24`). If the IP range is specified by CIDR range or single IP
      address, it must belong to the CIDR range specified by the range
      name on the subnet. If the IP range is specified by netmask, the
      IP allocator will pick an available range with the specified netmask
      and allocate it to this network interface.
      """)
  else:
    network_interface_help_texts.append("""
      Each IP alias range consists of a range name and a CIDR netmask
      (e.g. `/24`) separated by a colon or just the netmask.
      The range name is the name of the range within the network
      interface's subnet from which to allocate an IP alias range. If
      unspecified, it defaults to the primary IP range of the subnet.
      The IP allocator will pick an available range with the specified
      netmask and allocate it to this network interface.
      """)

  if support_network_attachments:
    # TODO(b/265153883): Add a link to the user guide.
    network_interface_help_texts.append("""
      *network-attachment*::: Specifies the network attachment that this
      interface should connect to. Mutually exclusive with *--network* and
      *--subnet* flags.
      """)

  if support_vlan_nic:
    multiple_network_interface_cards_spec['vlan'] = int
    # TODO(b/274638343): Add help text before release.

  if support_igmp_query:
    network_interface_help_texts.append("""
      *igmp-query*::: Determines if the Compute Engine Instance can receive and respond to IGMP query packets on the specified network interface.
      ``IGMP_QUERY'' must be one of: `IGMP_QUERY_V2`, `IGMP_QUERY_DISABLED`.
      It is disabled by default.
    """)

  if instance_create:
    network_interfaces = parser.add_group(mutex=True)
    network_interfaces.add_argument(
        '--network-interface',
        type=arg_parsers.ArgDict(
            spec=multiple_network_interface_cards_spec,
            allow_key_only=True,
        ),
        action='append',  # pylint:disable=protected-access
        metavar='PROPERTY=VALUE',
        help=''.join(network_interface_help_texts))

    if support_subinterface:
      network_interface_file_help_text = """\
        Same as --network-interface except that the value for the entry will
        be read from a local file. This is used in case subinterfaces need to
        be specified. All field names in the json follow lowerCamelCase.

        The following additional key is allowed:
         subinterfaces
            Specifies the list of subinterfaces assigned to this network
            interface of the instance.

                The following keys are allowed:
                subnetwork: Specifies the subnet that the subinterface will be
                part of. The subnet should have l2-enable set and VLAN tagged.

                vlan: Specifies the VLAN of the subinterface. Can have a value
                between 2-4094. This should be the same VLAN as the subnet. VLAN tag
                within a network interface is unique.

                ipAddress: Optional. Specifies the ip address of the
                subinterface. If not specified, an ip address will be allocated from
                subnet ip range.

        An example json looks like:
        [
         {
          "network":"global/networks/network-example",
          "subnetwork":"projects/example-project/regions/us-central1/subnetworks/untagged-subnet",
          "subinterfaces":[
             {
              "subnetwork":"projects/example-project/regions/us-central1/subnetworks/tagged-subnet",
              "vlan":2,
              "ipAddress":"111.11.11.1"
           }
          ]
         }
        ]
          """
      network_interfaces.add_argument(
          '--network-interface-from-file',
          type=arg_parsers.FileContents(),
          metavar='KEY=LOCAL_FILE_PATH',
          help=network_interface_file_help_text)

      network_interface_json_help_text = """\
        Same as --network-interface-from-file except that the value for the
        entry will be a json string. This can also be used in case
        subinterfaces need to be specified. All field names in the json follow
        lowerCamelCase."""

      network_interfaces.add_argument(
          '--network-interface-from-json-string',
          metavar='NETWORK_INTERFACE_JSON_STRING',
          help=network_interface_json_help_text)
  else:
    parser.add_argument(
        '--network-interface',
        type=arg_parsers.ArgDict(
            spec=multiple_network_interface_cards_spec,
            allow_key_only=True,
        ),
        action='append',  # pylint:disable=protected-access
        metavar='PROPERTY=VALUE',
        help=''.join(network_interface_help_texts))


def AddNoAddressArg(parser):
  parser.add_argument(
      '--no-address',
      action='store_true',
      help="""\
           If provided, the instances are not assigned external IP
           addresses. To pull container images, you must configure private
           Google access if using Container Registry or configure Cloud NAT
           for instances to access container images directly. For more
           information, see:
             * https://cloud.google.com/vpc/docs/configure-private-google-access
             * https://cloud.google.com/nat/docs/using-nat
           """)


def AddMachineTypeArgs(parser, required=False, unspecified_help=None):
  if unspecified_help is None:
    unspecified_help = ' If unspecified, the default type is n1-standard-1.'
  parser.add_argument(
      '--machine-type',
      completer=compute_completers.MachineTypesCompleter,
      required=required,
      help="""\
      Specifies the machine type used for the instances. To get a
      list of available machine types, run 'gcloud compute
      machine-types list'.{}""".format(unspecified_help))


def AddMinCpuPlatformArgs(parser, track, required=False):
  parser.add_argument(
      '--min-cpu-platform',
      metavar='PLATFORM',
      required=required,
      help="""\
      When specified, the VM will be scheduled on host with specified CPU
      architecture or a newer one. To list available CPU platforms in given
      zone, run:

          $ gcloud {}compute zones describe ZONE --format="value(availableCpuPlatforms)"

      Default setting is "AUTOMATIC".

      CPU platform selection is available only in selected zones.

      You can find more information on-line:
      [](https://cloud.google.com/compute/docs/instances/specify-min-cpu-platform)
      """.format(track.prefix + ' ' if track.prefix else ''))


def AddMinNodeCpuArg(parser, is_update=False):
  parser.add_argument(
      '--min-node-cpu',
      help="""\
      Minimum number of virtual CPUs this instance will consume when running on
      a sole-tenant node.
      """)
  if is_update:
    parser.add_argument(
        '--clear-min-node-cpu',
        action='store_true',
        help="""\
        Removes the min-node-cpu field from the instance. If specified, the
        instance min-node-cpu will be cleared. The instance will not be
        overcommitted and utilize the full CPU count assigned.
        """)


def AddLocationHintArg(parser):
  parser.add_argument(
      '--location-hint',
      hidden=True,
      help="""\
      Used by internal tools to control sub-zone location of the instance.
      """)


def AddPreemptibleVmArgs(parser, is_update=False):
  """Set preemptible scheduling property for instances.

  For set_scheduling operation, in addition we are providing no-preemptible flag
  in use case when user wants to disable this property.

  Args:
     parser: ArgumentParser, parser to which flags will be added.
     is_update: Bool. If True, flags are intended for set-scheduling operation.
  """
  help_text = """\
      If provided, instances will be preemptible and time-limited. Instances
      might be preempted to free up resources for standard VM instances,
      and will only be able to run for a limited amount of time. Preemptible
      instances can not be restarted and will not migrate.
      """
  if is_update:
    parser.add_argument(
        '--preemptible',
        action=arg_parsers.StoreTrueFalseAction,
        help=help_text)
  else:
    parser.add_argument(
        '--preemptible', action='store_true', default=False, help=help_text)


def AddProvisioningModelVmArgs(parser):
  """Set arguments for specifing provisioning model for instances."""
  parser.add_argument(
      '--provisioning-model',
      choices={
          'SPOT':
              ('Spot VMs are spare capacity; Spot VMs are discounted '
               'to have much lower prices than standard VMs '
               'but have no guaranteed runtime. Spot VMs are the new version '
               'of preemptible VM instances, except Spot VMs do not have '
               'a 24-hour maximum runtime.'),
          'STANDARD': ('Default. Standard provisioning model for VM instances, '
                       'which has user-controlled runtime '
                       'but no Spot discounts.')
      },
      type=arg_utils.ChoiceToEnumName,
      help="""\
      Specifies provisioning model, which determines price, obtainability,
      and runtime for the VM instance.
      """)


def AddMaxRunDurationVmArgs(parser, is_update=False):
  """Set arguments for specifing max-run-duration and termination-time flags."""
  max_run_duration_help_text = """\
      Limits how long this VM instance can run, specified as a duration
      relative to the VM instance's most-recent start time. Format the duration,
      ``MAX_RUN_DURATION'', as the number of days, hours, minutes, and seconds
      followed by d, h, m, and s respectively. For example, specify 30m for a
      duration of 30 minutes or specify 1d2h3m4s for a duration of 1 day,
      2 hours, 3 minutes, and 4 seconds. Alternatively, to specify a timestamp,
      use `--termination-time` instead.

      If neither `--max-run-duration` nor `--termination-time` is specified
      (default), the VM instance runs until prompted by a user action
      or system event.
      If either is specified, the VM instance is scheduled to be automatically
      terminated using the action specified by `--instance-termination-action`.
      For `--max-run-duration`, the VM instance is automatically terminated when the VM's
      current runtime reaches ``MAX_RUN_DURATION''. Note: Anytime the VM instance
      is stopped or suspended,  `--max-run-duration` and (unless the VM uses
      `--provisioning-model=SPOT`) `--instance-termination-action` are
      automatically removed from the VM.
      """

  termination_time_help_text = """
      Limits how long this VM instance can run, specified as a time.
      Format the time, ``TERMINATION_TIME'', as a RFC 3339 timestamp. For more
      information, see https://tools.ietf.org/html/rfc3339.
      Alternatively, to specify a duration, use `--max-run-duration` instead.

    If neither `--termination-time` nor `--max-run-duration`
    is specified (default),
    the VM instance runs until prompted by a user action or system event.
    If either is specified, the VM instance is scheduled to be automatically
    terminated using the action specified by `--instance-termination-action`.
    For `--termination-time`, the VM instance is automatically terminated at the
    specified timestamp. Note: Anytime the VM instance is stopped or suspended,
    `--termination-time` and (unless the VM uses `--provisioning-model=SPOT`)
    `--instance-termination-action` are automatically removed from the VM.
    """
  if is_update:
    max_run_duration_group = parser.add_group('Max Run Duration', mutex=True)
    max_run_duration_group.add_argument(
        '--clear-max-run-duration',
        action='store_true',
        help="""\
        Removes the max-run-duration field from the scheduling options.
        """,
    )
    max_run_duration_group.add_argument(
        '--max-run-duration',
        type=arg_parsers.Duration(),
        help=max_run_duration_help_text,
    )

    termination_time_group = parser.add_group('Termination Time', mutex=True)
    termination_time_group.add_argument(
        '--clear-termination-time',
        action='store_true',
        help="""\
        Removes the termination-time field from the scheduling options.
        """,
    )
    termination_time_group.add_argument(
        '--termination-time',
        type=arg_parsers.Datetime.Parse,
        help=termination_time_help_text,
    )
  else:
    parser.add_argument(
        '--max-run-duration',
        type=arg_parsers.Duration(),
        help=max_run_duration_help_text,
    )
    parser.add_argument(
        '--termination-time',
        type=arg_parsers.Datetime.Parse,
        help=termination_time_help_text,
    )


def AddHostErrorTimeoutSecondsArgs(parser):
  parser.add_argument(
      '--host-error-timeout-seconds',
      type=arg_parsers.Duration(lower_bound='90s', upper_bound='300s'),
      help="""
      The timeout in seconds for host error detection. The value must be
      set with 30 second increments, with a range of 90 to 330 seconds.
      If unset, the default behavior of the host error recovery is used.
    """)


def AddGracefulShutdownArgs(parser, is_create=False):
  """Set arguments for graceful shutdown."""
  if is_create:
    parser.add_argument(
        '--graceful-shutdown',
        action='store_const',
        const=True,
        help="""\
        Enables graceful shutdown for the instance.
        """,
    )
  else:
    parser.add_argument(
        '--graceful-shutdown',
        action=arg_parsers.StoreTrueFalseAction,
        help="""\
        If set to true, enables graceful shutdown for the instance.
        """,
    )
  parser.add_argument(
      '--graceful-shutdown-max-duration',
      type=arg_parsers.Duration(lower_bound='1s', upper_bound='3600s'),
      help="""
      Specifies time needed to gracefully
      shutdown the instance. After that time, the instance goes to STOPPING even
      if graceful shutdown is not completed.e.g. `300s`, `1h`. See $ gcloud
      topic datetimes for information on duration formats.
      """,
  )


def AddLocalSsdRecoveryTimeoutArgs(parser):
  parser.add_argument(
      '--local-ssd-recovery-timeout',
      type=arg_parsers.Duration(
          default_unit='h', lower_bound='0h', upper_bound='168h'),
      help="""
      Specifies the maximum amount of time a Local Ssd Vm should wait while
      recovery of the Local Ssd state is attempted. Its value should be in
      between 0 and 168 hours with hour granularity and the default value being 1
      hour.
    """)


def AddInstanceTerminationActionVmArgs(parser, is_update=False):
  """Set arguments for specifing the termination action for the instance.

  For set_scheduling operation we are implementing this as argument group with
  additional argument clear-* providing the functionality to clear the
  instance-termination-action field.

  Args:
     parser: ArgumentParser, parser to which flags will be added.
     is_update: Bool. If True, flags are intended for set-scheduling operation.
  """

  if is_update:
    termination_action_group = parser.add_group(
        'Instance Termination Action', mutex=True)
    termination_action_group.add_argument(
        '--instance-termination-action',
        choices={
            'STOP': 'Default. Stop the VM without preserving memory. '
                    'The VM can be restarted later.',
            'DELETE': 'Permanently delete the VM.'
        },
        type=arg_utils.ChoiceToEnumName,
        help="""\
      Specifies the termination action that will be taken upon VM preemption
      (`--provisioning-model=SPOT` or `--preemptible`) or automatic instance
      termination (`--max-run-duration` or `--termination-time`).
      """)
    termination_action_group.add_argument(
        '--clear-instance-termination-action',
        action='store_true',
        help="""\
        Disables the termination action for this VM if allowed OR
        sets termination action to the default value.
        Depending on a VM's availability settings, a termination action is
        either required or not allowed. This flag is required when you are
        updating a VM such that it's previously specified termination action is
        no longer allowed.
        If you use this flag when a VM requires a termination action,
        it's termination action is just set to the default value (stop).
        """)
  else:
    parser.add_argument(
        '--instance-termination-action',
        choices={
            'STOP': 'Default. Stop the VM without preserving memory. '
                    'The VM can be restarted later.',
            'DELETE': 'Permanently delete the VM.'
        },
        type=arg_utils.ChoiceToEnumName,
        help="""\
      Specifies the termination action that will be taken upon VM preemption
      (`--provisioning-model=SPOT` or `--preemptible`) or automatic instance
      termination (`--max-run-duration` or `--termination-time`).
      """)


def ValidateInstanceScheduling(args, support_max_run_duration=False):
  """Validates instance scheduling related flags."""

  if args.IsSpecified('instance_termination_action'):
    if support_max_run_duration:
      if not (args.IsSpecified('provisioning_model') or
              args.IsSpecified('max_run_duration') or
              args.IsSpecified('termination_time')):
        raise exceptions.MinimumArgumentException([
            '--provisioning-model', '--max-run-duration', '--termination-time'
        ], 'required with argument `--instance-termination-action`.')
    elif not args.IsSpecified('provisioning_model'):
      raise exceptions.RequiredArgumentException(
          '--provisioning-model',
          'required with argument `--instance-termination-action`.')

  if support_max_run_duration and args.IsSpecified(
      'termination_time') and args.IsSpecified('max_run_duration'):
    raise compute_exceptions.ArgumentError(
        'Must specify exactly one of --max-run-duration or --termination-time '
        'as these fields are mutually exclusive.')


def AddNetworkArgs(parser):
  """Set arguments for choosing the network/subnetwork."""
  parser.add_argument(
      '--network',
      help="""\
      Specifies the network that the VM instances are a part of. If `--subnet`
      is also specified, subnet must be a subnetwork of the network specified by
      this `--network` flag. If neither is specified, the default network is
      used.
      """)

  parser.add_argument(
      '--subnet',
      help="""\
      Specifies the subnet that the VM instances are a part of. If `--network`
      is also specified, subnet must be a subnetwork of the network specified by
      the `--network` flag.
      """)


def AddPrivateNetworkIpArgs(parser):
  """Set arguments for choosing the network IP address."""
  parser.add_argument(
      '--private-network-ip',
      help="""\
      Specifies the RFC1918 IP to assign to the instance. The IP should be in
      the subnet or legacy network IP range.
      """)


def AddServiceAccountAndScopeArgs(parser,
                                  instance_exists,
                                  extra_scopes_help='',
                                  operation='Create',
                                  resource='instance'):
  """Add args for configuring service account and scopes.

  This should replace AddScopeArgs (b/30802231).

  Args:
    parser: ArgumentParser, parser to which flags will be added.
    instance_exists: bool, If instance already exists and we are modifying it.
    extra_scopes_help: str, Extra help text for the scopes flag.
    operation: operation being performed, capitalized. E.g. 'Create' or 'Import'
    resource: resource type on which scopes and service account are being added.
      E.g. 'instance' or 'machine image'.
  """
  service_account_group = parser.add_mutually_exclusive_group()
  no_sa_instance_not_exist = (
      '{operation} {resource} without service account'.format(
          operation=operation, resource=resource))
  service_account_group.add_argument(
      '--no-service-account',
      action='store_true',
      help='Remove service account from the {0}'.format(resource)
      if instance_exists else no_sa_instance_not_exist)

  sa_exists = """You can explicitly specify the Compute Engine default service
  account using the 'default' alias.

  If not provided, the {0} will use the service account it currently has.
  """.format(resource)

  sa_not_exists = """

  If not provided, the {0} will use the project\'s default service account.
  """.format(resource)

  service_account_help = """\
  A service account is an identity attached to the {resource}. Its access tokens
  can be accessed through the instance metadata server and are used to
  authenticate applications on the instance. The account can be set using an
  email address corresponding to the required service account. {extra_help}
  """.format(
      extra_help=sa_exists if instance_exists else sa_not_exists,
      resource=resource)
  service_account_group.add_argument(
      '--service-account', help=service_account_help)

  scopes_group = parser.add_mutually_exclusive_group()
  scopes_group.add_argument(
      '--no-scopes',
      action='store_true',
      help='Remove all scopes from the {resource}'.format(resource=resource)
      if instance_exists else '{operation} {resource} without scopes'.format(
          operation=operation, resource=resource))
  scopes_exists = 'keep the scopes it currently has'
  scopes_not_exists = 'be assigned the default scopes, described below'
  scopes_help = """\
If not provided, the {resource} will {exists}. {extra}

{scopes_help}
""".format(
    exists=scopes_exists if instance_exists else scopes_not_exists,
    extra=extra_scopes_help,
    scopes_help=constants.ScopesHelp(),
    resource=resource)
  scopes_group.add_argument(
      '--scopes', type=arg_parsers.ArgList(), metavar='SCOPE', help=scopes_help)


def AddNetworkInterfaceArgs(parser):
  """Adds network interface flag to the argparse."""

  parser.add_argument(
      '--network-interface',
      default=constants.DEFAULT_NETWORK_INTERFACE,
      action=arg_parsers.StoreOnceAction,
      help="""\
      Specifies the name of the network interface which contains the access
      configuration. If this is not provided, then "nic0" is used
      as the default.
      """)


def AddNetworkTierArgs(parser, instance=True, for_update=False):
  """Adds network tier flag to the argparse."""

  if for_update:
    parser.add_argument(
        '--network-tier',
        type=lambda x: x.upper(),
        help="""\
        Update the network tier of the access configuration. It does not allow
        to change from `PREMIUM` to `STANDARD` and visa versa.
        """,
    )
    return

  if instance:
    network_tier_help = """\
        Specifies the network tier that will be used to configure the instance.
        ``NETWORK_TIER'' must be one of: `PREMIUM`, `STANDARD`, `FIXED_STANDARD`.
        The default value is `PREMIUM`.
        """
  else:
    network_tier_help = """\
        Specifies the network tier of the access configuration. ``NETWORK_TIER''
        must be one of: `PREMIUM`, `STANDARD`, `FIXED_STANDARD`.
        The default value is `PREMIUM`.
        """
  parser.add_argument(
      '--network-tier', type=lambda x: x.upper(), help=network_tier_help)


def AddDisplayDeviceArg(parser, is_update=False):
  """Adds public DNS arguments for instance or access configuration."""
  display_help = 'Enable a display device on VM instances.'
  if not is_update:
    display_help += ' Disabled by default.'
  parser.add_argument(
      '--enable-display-device',
      action=arg_parsers.StoreTrueFalseAction if is_update else 'store_true',
      help=display_help)


def AddPublicDnsArgs(parser, instance=True):
  """Adds public DNS arguments for instance or access configuration."""

  public_dns_args = parser.add_mutually_exclusive_group()
  if instance:
    no_public_dns_help = """\
        If provided, the instance will not be assigned a public DNS name.
        """
  else:
    no_public_dns_help = """\
        If provided, the external IP in the access configuration will not be
        assigned a public DNS name.
        """
  public_dns_args.add_argument(
      '--no-public-dns', action='store_true', help=no_public_dns_help)

  if instance:
    public_dns_help = """\
        Assigns a public DNS name to the instance.
        """
  else:
    public_dns_help = """\
        Assigns a public DNS name to the external IP in the access
        configuration. This option can only be specified for the default
        network-interface, "nic0".
        """
  public_dns_args.add_argument(
      '--public-dns', action='store_true', help=public_dns_help)


def AddPublicPtrArgs(parser, instance=True):
  """Adds public PTR arguments for instance or access configuration."""

  public_ptr_args = parser.add_mutually_exclusive_group()
  if instance:
    no_public_ptr_help = """\
        If provided, no DNS PTR record is created for the external IP of the
        instance. Mutually exclusive with public-ptr-domain.
        """
  else:
    no_public_ptr_help = """\
        If provided, no DNS PTR record is created for the external IP in the
        access configuration. Mutually exclusive with public-ptr-domain.
        """
  public_ptr_args.add_argument(
      '--no-public-ptr', action='store_true', help=no_public_ptr_help)

  if instance:
    public_ptr_help = """\
        Creates a DNS PTR record for the external IP of the instance.
        """
  else:
    public_ptr_help = """\
        Creates a DNS PTR record for the external IP in the access
        configuration. This option can only be specified for the default
        network-interface, "nic0"."""
  public_ptr_args.add_argument(
      '--public-ptr', action='store_true', help=public_ptr_help)

  public_ptr_domain_args = parser.add_mutually_exclusive_group()
  if instance:
    no_public_ptr_domain_help = """\
        If both this flag and --public-ptr are specified, creates a DNS PTR
        record for the external IP of the instance with the PTR domain name
        being the DNS name of the instance.
        """
  else:
    no_public_ptr_domain_help = """\
        If both this flag and --public-ptr are specified, creates a DNS PTR
        record for the external IP in the access configuration with the PTR
        domain name being the DNS name of the instance.
        """
  public_ptr_domain_args.add_argument(
      '--no-public-ptr-domain',
      action='store_true',
      help=no_public_ptr_domain_help)

  if instance:
    public_ptr_domain_help = """\
        Assigns a custom PTR domain for the external IP of the instance.
        Mutually exclusive with no-public-ptr.
        """
  else:
    public_ptr_domain_help = """\
        Assigns a custom PTR domain for the external IP in the access
        configuration. Mutually exclusive with no-public-ptr. This option can
        only be specified for the default network-interface, "nic0".
        """
  public_ptr_domain_args.add_argument(
      '--public-ptr-domain', help=public_ptr_domain_help)


def AddIpv6PublicPtrDomainArg(parser):
  """Adds IPv6 public PTR domain for IPv6 access configuration of instance."""
  parser.add_argument(
      '--ipv6-public-ptr-domain',
      default=None,
      help="""\
      Assigns a custom PTR domain for the external IPv6 in the IPv6 access
      configuration of instance. If its value is not specified, the default
      PTR record will be used. This option can only be specified for the default
      network interface, ``nic0''.""")


def AddIpv6PublicPtrArgs(parser):
  """Adds IPv6 public PTR arguments for ipv6 access configuration."""

  ipv6_public_ptr_args = parser.add_mutually_exclusive_group()
  no_ipv6_public_ptr_help = """\
        If provided, the default DNS PTR record will replace the existing one
        for external IPv6 in the IPv6 access configuration. Mutually exclusive
        with ipv6-public-ptr-domain.
        """
  ipv6_public_ptr_args.add_argument(
      '--no-ipv6-public-ptr', action='store_true', help=no_ipv6_public_ptr_help)

  ipv6_public_ptr_domain_help = """\
        Assigns a custom PTR domain for the external IPv6 in the access
        configuration. Mutually exclusive with no-ipv6-public-ptr. This option
        can only be specified for the default network interface, ``nic0''.
        """
  ipv6_public_ptr_args.add_argument(
      '--ipv6-public-ptr-domain', help=ipv6_public_ptr_domain_help)


def ValidatePublicDnsFlags(args):
  """Validates the values of public DNS related flags."""

  network_interface = getattr(args, 'network_interface', None)
  public_dns = getattr(args, 'public_dns', None)
  if public_dns:
    if (network_interface is not None and
        network_interface != constants.DEFAULT_NETWORK_INTERFACE):
      raise compute_exceptions.ArgumentError(
          'Public DNS can only be enabled for default network interface '
          '\'{0}\' rather than \'{1}\'.'.format(
              constants.DEFAULT_NETWORK_INTERFACE, network_interface))


def ValidatePublicPtrFlags(args):
  """Validates the values of public PTR related flags."""

  network_interface = getattr(args, 'network_interface', None)
  public_ptr = getattr(args, 'public_ptr', None)
  if public_ptr is True:  # pylint:disable=g-bool-id-comparison
    if (network_interface is not None and
        network_interface != constants.DEFAULT_NETWORK_INTERFACE):
      raise compute_exceptions.ArgumentError(
          'Public PTR can only be enabled for default network interface '
          '\'{0}\' rather than \'{1}\'.'.format(
              constants.DEFAULT_NETWORK_INTERFACE, network_interface))

  if args.public_ptr_domain is not None and args.no_public_ptr is True:  # pylint:disable=g-bool-id-comparison
    raise exceptions.ConflictingArgumentsException('--public-ptr-domain',
                                                   '--no-public-ptr')


def ValidateIpv6PublicPtrFlags(args):
  """Validates the values of IPv6 public PTR related flags."""

  network_interface = getattr(args, 'network_interface', None)

  if args.ipv6_public_ptr_domain is not None or args.no_ipv6_public_ptr:
    if (network_interface is not None and
        network_interface != constants.DEFAULT_NETWORK_INTERFACE):
      raise compute_exceptions.ArgumentError(
          'IPv6 Public PTR can only be enabled for default network interface '
          '\'{0}\' rather than \'{1}\'.'.format(
              constants.DEFAULT_NETWORK_INTERFACE, network_interface))

  if args.ipv6_public_ptr_domain is not None and args.no_ipv6_public_ptr:
    raise exceptions.ConflictingArgumentsException('--ipv6-public-ptr-domain',
                                                   '--no-ipv6-public-ptr')


def ValidateServiceAccountAndScopeArgs(args):
  if args.no_service_account and not args.no_scopes:
    raise exceptions.RequiredArgumentException(
        '--no-scopes', 'required with argument '
        '--no-service-account')
  # Reject empty scopes
  for scope in (args.scopes or []):
    if not scope:
      raise exceptions.InvalidArgumentException(
          '--scopes', 'Scope cannot be an empty string.')


def AddTagsArgs(parser):
  parser.add_argument(
      '--tags',
      type=arg_parsers.ArgList(min_length=1),
      metavar='TAG',
      help="""\
      Specifies a list of tags to apply to the instance. These tags allow
      network firewall rules and routes to be applied to specified VM instances.
      See gcloud_compute_firewall-rules_create(1) for more details.

      To read more about configuring network tags, read this guide:
      https://cloud.google.com/vpc/docs/add-remove-network-tags

      To list instances with their respective status and tags, run:

        $ gcloud compute instances list --format='table(name,status,tags.list())'

      To list instances tagged with a specific tag, `tag1`, run:

        $ gcloud compute instances list --filter='tags:tag1'
      """)


def AddSecureTagsArgs(parser):
  """Adds secure tag related args."""
  parser.add_argument(
      '--secure-tags',
      type=arg_parsers.ArgList(min_length=1),
      metavar='SECURE_TAG',
      help="""\
      Specifies a list of secure tags to apply to the instance. These tags allow
      network firewall rules and routes to be applied to specified VM instances.
      See gcloud_compute_network_firewall-policies_rules_create(1) for more
      details.
      """)


def AddResourceManagerTagsArgs(parser):
  """Adds resource manager tag related args."""
  parser.add_argument(
      '--resource-manager-tags',
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE',
      action=arg_parsers.UpdateAction,
      help="""\
      Specifies a list of resource manager tags to apply to the instance.
      """)


def AddNoRestartOnFailureArgs(parser):
  parser.add_argument(
      '--restart-on-failure',
      action='store_true',
      default=True,
      help="""\
      The instances will be restarted if they are terminated by Compute Engine.
      This does not affect terminations performed by the user.
      """)


def AddMaintenancePolicyArgs(parser, deprecate=False):
  """Adds maintenance behavior related args."""
  help_text = """\
  Specifies the behavior of the VMs when their host machines undergo
  maintenance. The default is MIGRATE.
  For more information, see
  https://cloud.google.com/compute/docs/instances/host-maintenance-options.
  """
  flag_type = lambda x: x.upper()
  action = None
  if deprecate:
    # Use nested group to group the deprecated arg with the new one.
    parser = parser.add_mutually_exclusive_group('Maintenance Behavior.')
    parser.add_argument(
        '--on-host-maintenance',
        dest='maintenance_policy',
        choices=MIGRATION_OPTIONS,
        type=flag_type,
        help=help_text)
    action = actions.DeprecationAction(
        '--maintenance-policy',
        warn='The {flag_name} flag is now deprecated. Please use '
        '`--on-host-maintenance` instead')
  parser.add_argument(
      '--maintenance-policy',
      action=action,
      choices=MIGRATION_OPTIONS,
      type=flag_type,
      help=help_text)


def AddAcceleratorArgs(parser):
  """Adds Accelerator-related args."""
  # Attaches accelerators (e.g. GPUs) to the instances. e.g. --accelerator
  # type=nvidia-tesla-k80,count=4
  parser.add_argument(
      '--accelerator',
      type=arg_parsers.ArgDict(spec={
          'type': str,
          'count': int,
      }),
      help="""\
      Attaches accelerators (e.g. GPUs) to the instances.

      *type*::: The specific type (e.g. nvidia-tesla-k80 for nVidia Tesla K80)
      of accelerator to attach to the instances. Use 'gcloud compute
      accelerator-types list' to learn about all available accelerator types.

      *count*::: Number of accelerators to attach to each
      instance. The default value is 1.
      """)


def ValidateAcceleratorArgs(args):
  """Valiadates flags specifying accelerators (e.g.

  GPUs).

  Args:
    args: parsed comandline arguments.

  Raises:
    InvalidArgumentException: when type is not specified in the accelerator
    config dictionary.
  """
  accelerator_args = getattr(args, 'accelerator', None)
  if accelerator_args:
    accelerator_type_name = accelerator_args.get('type', '')
    if not accelerator_type_name:
      raise exceptions.InvalidArgumentException(
          '--accelerator', 'accelerator type must be specified. '
          'e.g. --accelerator type=nvidia-tesla-k80,count=2')


def AddKonletArgs(parser):
  """Adds Konlet-related args."""
  parser.add_argument(
      '--container-image',
      help="""\
      Full container image name, which should be pulled onto VM instance,
      eg. `docker.io/tomcat`.
      """)

  parser.add_argument(
      '--container-command',
      help="""\
      Specifies what executable to run when the container starts (overrides
      default entrypoint), eg. `nc`.

      Default: None (default container entrypoint is used)
      """)

  parser.add_argument(
      '--container-arg',
      action='append',
      help="""\
      Argument to append to container entrypoint or to override container CMD.
      Each argument must have a separate flag. Arguments are appended in the
      order of flags. Example:

      Assuming the default entry point of the container (or an entry point
      overridden with --container-command flag) is a Bourne shell-compatible
      executable, in order to execute 'ls -l' command in the container,
      the user could use:

      `--container-arg="-c" --container-arg="ls -l"`

      Caveat: due to the nature of the argument parsing, it's impossible to
      provide the flag value that starts with a dash (`-`) without the `=` sign
      (that is, `--container-arg "-c"` will not work correctly).

      Default: None. (no arguments appended)
      """)

  parser.add_argument(
      '--container-privileged',
      action='store_true',
      help="""\
      Specify whether to run container in privileged mode.

      Default: `--no-container-privileged`.
      """)

  _AddContainerMountHostPathFlag(parser)
  _AddContainerMountTmpfsFlag(parser)

  parser.add_argument(
      '--container-env',
      type=arg_parsers.ArgDict(),
      action='append',
      metavar='KEY=VALUE, ...',
      help="""\
      Declare environment variables KEY with value VALUE passed to container.
      Only the last value of KEY is taken when KEY is repeated more than once.

      Values, declared with --container-env flag override those with the same
      KEY from file, provided in --container-env-file.
      """)

  parser.add_argument(
      '--container-env-file',
      help="""\
      Declare environment variables in a file. Values, declared with
      --container-env flag override those with the same KEY from file.

      File with environment variables in format used by docker (almost).
      This means:
      - Lines are in format KEY=VALUE.
      - Values must contain equality signs.
      - Variables without values are not supported (this is different from
        docker format).
      - If `#` is first non-whitespace character in a line the line is ignored
        as a comment.
      - Lines with nothing but whitespace are ignored.
      """)

  parser.add_argument(
      '--container-stdin',
      action='store_true',
      help="""\
      Keep container STDIN open even if not attached.

      Default: `--no-container-stdin`.
      """)

  parser.add_argument(
      '--container-tty',
      action='store_true',
      help="""\
      Allocate a pseudo-TTY for the container.

      Default: `--no-container-tty`.
      """)

  parser.add_argument(
      '--container-restart-policy',
      choices=['never', 'on-failure', 'always'],
      default='always',
      metavar='POLICY',
      type=lambda val: val.lower(),
      help="""\
      Specify whether to restart a container on exit.
      """)


def ValidateKonletArgs(args):
  """Validates Konlet-related args."""
  if not args.IsSpecified('container_image'):
    raise exceptions.RequiredArgumentException(
        '--container-image', 'You must provide container image')
  if args.IsSpecified('machine_type') and args.machine_type.startswith('t2a'):
    raise exceptions.InvalidArgumentException(
        '--machine_type',
        'T2A machine types are not compatible with Konlet or containers.')


def ValidateLocalSsdFlags(args):
  """Validate local ssd flags."""
  for local_ssd in args.local_ssd or []:
    interface = local_ssd.get('interface')
    if interface and interface not in LOCAL_SSD_INTERFACES:
      raise exceptions.InvalidArgumentException(
          '--local-ssd:interface', 'Unexpected local SSD interface: [{given}]. '
          'Legal values are [{ok}].'.format(
              given=interface, ok=', '.join(LOCAL_SSD_INTERFACES)))
    size = local_ssd.get('size')
    # TODO(b/206253303): 3000GB partitions will only be available for private
    # preview for now. Any help_text or error messages will reflect what is
    # currently publicly available, 375GB partitions only, despite 3000GB
    # still accepted as a value for select customers. Updates to any public
    # documentation will occur once Large Local SSD is more widely available.
    if size is not None:
      if size != (constants.SSD_SMALL_PARTITION_GB * constants.BYTES_IN_ONE_GB
                 ) and size != (constants.SSD_LARGE_PARTITION_GB *
                                constants.BYTES_IN_ONE_GB):
        raise exceptions.InvalidArgumentException(
            '--local-ssd:size', 'Unexpected local SSD size: [{given}] bytes. '
            'Legal values are {small}GB and {large}GB only.'.format(
                given=size,
                small=constants.SSD_SMALL_PARTITION_GB,
                large=constants.SSD_LARGE_PARTITION_GB))


def ValidateNicFlags(args):
  """Validates flags specifying network interface cards.

  Throws exceptions or print warning if incompatible nic args are specified.

  Args:
    args: parsed command line arguments.

  Raises:
    InvalidArgumentException: when it finds --network-interface that has both
                              address, and no-address keys.
    ConflictingArgumentsException: when it finds --network-interface and at
                                   least one of --address, --network,
                                   --private_network_ip, or --subnet.
  """
  network_interface = getattr(args, 'network_interface', None)
  network_interface_from_file = getattr(args, 'network_interface_from_file',
                                        None)
  network_interface_from_json = getattr(args,
                                        'network_interface_from_json_string',
                                        None)
  if (network_interface is None and network_interface_from_file is None and
      network_interface_from_json is None):
    return
  elif network_interface is not None:
    for ni in network_interface:
      if 'address' in ni and 'no-address' in ni:
        raise exceptions.InvalidArgumentException(
            '--network-interface',
            'specifies both address and no-address for one interface')

  conflicting_args = [
      'address',
      'network',
      'private_network_ip',
      'subnet',
  ]
  conflicting_args_present = [
      arg for arg in conflicting_args if getattr(args, arg, None)
  ]
  conflicting_args = [
      '--{0}'.format(arg.replace('_', '-')) for arg in conflicting_args_present
  ]

  # These args are also incompatible with --network-interface, but they were
  # already released without validation, so print warning for them instead of
  # throwing exception
  warning_args = [
      'network_tier',
      'stack_type',
      'ipv6_network_tier',
      'ipv6_public_ptr_domain',
      'internal_ipv6_address',
      'internal_ipv6_prefix_length',
      'ipv6_address',
      'ipv6_prefix_length',
      'external_ipv6_address',
      'external_ipv6_prefix_length',
  ]
  warning_args_present = [
      arg for arg in warning_args if getattr(args, arg, None)
  ]
  warning_args = [
      '--{0}'.format(arg.replace('_', '-')) for arg in warning_args_present
  ]

  if not conflicting_args_present and not warning_args_present:
    return

  if conflicting_args_present:
    if network_interface is not None:
      raise exceptions.ConflictingArgumentsException(
          '--network-interface',
          'all of the following: ' + ', '.join(conflicting_args),
      )
    elif network_interface_from_file is not None:
      raise exceptions.ConflictingArgumentsException(
          '--network-interface-from-file',
          'all of the following: ' + ', '.join(conflicting_args),
      )
    else:
      raise exceptions.ConflictingArgumentsException(
          '--network-interface-from-json-string',
          'all of the following: ' + ', '.join(conflicting_args),
      )

  if warning_args_present:
    if network_interface is not None:
      nic_arg_name = '--network-interface'
    elif network_interface_from_file is not None:
      nic_arg_name = '--network-interface-from-file'
    else:
      nic_arg_name = '--network-interface-from-json-string'

    log.status.write(
        f'When {nic_arg_name} is specified, the following arguments are'
        ' ignored: '
        + ', '.join(warning_args)
        + '.\n'
    )


def AddDiskScopeFlag(parser):
  """Adds --disk-scope flag."""
  parser.add_argument(
      '--disk-scope',
      choices={
          'zonal': 'The disk specified in --disk is interpreted as a '
                   'zonal disk in the same zone as the instance. '
                   'Ignored if a full URI is provided to the `--disk` flag.',
          'regional': 'The disk specified in --disk is interpreted as a '
                      'regional disk in the same region as the instance. '
                      'Ignored if a full URI is provided to the `--disk` flag.'
      },
      help='The scope of the disk.',
      default='zonal')


def WarnForSourceInstanceTemplateLimitations(args):
  """Warn if --source-instance-template is mixed with unsupported flags.

  Args:
    args: Argument namespace
  """
  allowed_flags = [
      '--project', '--zone', '--region', '--source-instance-template',
      'INSTANCE_NAMES:1', '--machine-type', '--custom-cpu', '--custom-memory',
      '--labels'
  ]

  if args.IsSpecified('source_instance_template'):
    specified_args = args.GetSpecifiedArgNames()
    # TODO(b/62933344) - Improve flag collision detection
    for flag in allowed_flags:
      if flag in specified_args:
        specified_args.remove(flag)
    if specified_args:
      log.status.write('When a source instance template is used, additional '
                       'parameters other than --machine-type and --labels will '
                       'be ignored but provided by the source instance '
                       'template\n')


def ValidateNetworkTierArgs(args):
  if (args.network_tier and
      args.network_tier not in constants.NETWORK_TIER_CHOICES_FOR_INSTANCE):
    raise exceptions.InvalidArgumentException(
        '--network-tier',
        'Invalid network tier [{tier}]'.format(tier=args.network_tier))


def AddDeletionProtectionFlag(parser, use_default_value=True):
  """Adds --deletion-protection Boolean flag.

  Args:
    parser: ArgumentParser, parser to which flags will be added.
    use_default_value: Bool, if True, deletion protection flag will be given the
      default value False, else None. Update uses None as an indicator that no
      update needs to be done for deletion protection.
  """
  help_text = ('Enables deletion protection for the instance.')
  action = ('store_true'
            if use_default_value else arg_parsers.StoreTrueFalseAction)
  parser.add_argument('--deletion-protection', help=help_text, action=action)


def AddShieldedInstanceConfigArgs(parser,
                                  use_default_value=True,
                                  for_update=False,
                                  for_container=False):
  """Adds flags for Shielded VM configuration.

  Args:
    parser: ArgumentParser, parser to which flags will be added.
    use_default_value: Bool, if True, flag will be given the default value
      False, else None. Update uses None as an indicator that no update needs to
      be done for deletion protection.
    for_update: Bool, if True, flags are intended for an update operation.
    for_container: Bool, if True, flags intended for an instances with container
      operation.
  """
  if use_default_value:
    default_action = 'store_true'
    action_kwargs = {'default': None}
  else:
    default_action = arg_parsers.StoreTrueFalseAction
    action_kwargs = {}

  # --shielded-secure-boot
  secure_boot_help = """\
      The instance boots with secure boot enabled. On Shielded VM instances,
      Secure Boot is not enabled by default. For information about how to modify
      Shielded VM options, see
      https://cloud.google.com/compute/docs/instances/modifying-shielded-vm.
      """
  if for_update:
    secure_boot_help += """\
      Changes to this setting with the update command only take effect
      after stopping and starting the instance.
      """

  parser.add_argument(
      '--shielded-secure-boot',
      help=secure_boot_help,
      dest='shielded_vm_secure_boot',
      action=default_action,
      **action_kwargs)

  # --shielded-vtpm
  vtpm_help = """\
      The instance boots with the TPM (Trusted Platform Module) enabled.
      A TPM is a hardware module that can be used for different security
      operations such as remote attestation, encryption, and sealing of keys.
      On Shielded VM instances, vTPM is enabled by default. For information
      about how to modify Shielded VM options, see
      https://cloud.google.com/compute/docs/instances/modifying-shielded-vm.
      """
  if for_update:
    vtpm_help += """\
      Changes to this setting with the update command only take effect
      after stopping and starting the instance.
      """

  parser.add_argument(
      '--shielded-vtpm',
      dest='shielded_vm_vtpm',
      help=vtpm_help,
      action=default_action,
      **action_kwargs)

  # --shielded-integrity-monitoring
  integrity_monitoring_help_format = """\
      Enables monitoring and attestation of the boot integrity of the
      instance. The attestation is performed against the integrity policy
      baseline. This baseline is initially derived from the implicitly
      trusted boot image when the instance is created. This baseline can be
      updated by using
      `gcloud compute instances {} --shielded-learn-integrity-policy`. On
      Shielded VM instances, integrity monitoring is enabled by default. For
      information about how to modify Shielded VM options, see
      https://cloud.google.com/compute/docs/instances/modifying-shielded-vm.
      For information about monitoring integrity on Shielded VM instances, see
      https://cloud.google.com/compute/docs/instances/integrity-monitoring."
      """
  if for_container:
    update_command = 'update-container'
  else:
    update_command = 'update'
  integrity_monitoring_help = integrity_monitoring_help_format.format(
      update_command)
  if for_update:
    integrity_monitoring_help += """\
      Changes to this setting with the update command only take effect
      after stopping and starting the instance.
      """

  parser.add_argument(
      '--shielded-integrity-monitoring',
      help=integrity_monitoring_help,
      dest='shielded_vm_integrity_monitoring',
      action=default_action,
      **action_kwargs)


def AddShieldedInstanceIntegrityPolicyArgs(parser):
  """Adds flags for shielded instance integrity policy settings."""
  help_text = """\
  Causes the instance to re-learn the integrity policy baseline using
  the current instance configuration. Use this flag after any planned
  boot-specific changes in the instance configuration, like kernel
  updates or kernel driver installation.
  """
  default_action = 'store_true'
  parser.add_argument(
      '--shielded-learn-integrity-policy',
      dest='shielded_vm_learn_integrity_policy',
      action=default_action,
      default=None,
      help=help_text)


def AddConfidentialComputeArgs(
    parser,
    support_confidential_compute_type=False,
    support_confidential_compute_type_tdx=False) -> None:
  """Adds flags for confidential compute for instance."""
  if support_confidential_compute_type:
    choices = {
        'SEV': 'Secure Encrypted Virtualization',
        'SEV_SNP': 'Secure Encrypted Virtualization - Secure Nested Paging'
    }
    help_text = """\
        The instance boots with Confidential Computing enabled. Confidential
        Computing can be based on Secure Encrypted Virtualization (SEV) or Secure
        Encrypted Virtualization - Secure Nested Paging (SEV-SNP), both of which
        are AMD virtualization features for running confidential instances.
        """

    # It is set in:
    # - third_party/py/googlecloudsdk/surface/compute/instances/..
    #    - create_with_container.py
    #    - create.py
    # along with tests that depend on it
    if support_confidential_compute_type_tdx:
      choices['TDX'] = 'Trust Domain eXtension'
      help_text = ''.join((help_text, ("""\
        Trust Domain eXtension based on Intel virtualization features for
        running confidential instances is also supported.
        """)))

    parser = parser.add_mutually_exclusive_group()
    parser.add_argument(
        '--confidential-compute-type',
        dest='confidential_compute_type',
        choices=choices,
        help=help_text)

    bool_flag_action = actions.DeprecationAction(
        '--confidential-compute',
        warn=(
            'The --confidential-compute flag will soon be deprecated. Please'
            ' use `--confidential-compute-type=SEV` instead'
        ),
        action='store_true',
    )
  else:
    bool_flag_action = 'store_true'

  parser.add_argument(
      '--confidential-compute',
      dest='confidential_compute',
      action=bool_flag_action,
      default=None,
      help="""\
      The instance boots with Confidential Computing enabled. Confidential
      Computing is based on Secure Encrypted Virtualization (SEV), an AMD
      virtualization feature for running confidential instances.
      """)


def AddHostnameArg(parser):
  """Adds flag for overriding hostname for instance."""
  parser.add_argument(
      '--hostname',
      help="""\
      Specify the hostname of the instance to be created. The specified
      hostname must be RFC1035 compliant. If hostname is not specified, the
      default hostname is [INSTANCE_NAME].c.[PROJECT_ID].internal when using
      the global DNS, and [INSTANCE_NAME].[ZONE].c.[PROJECT_ID].internal
      when using zonal DNS.
      """)


def AddReservationAffinityGroup(
    parser,
    group_text,
    affinity_text,
    support_specific_then_x_affinity,
):
  """Adds the argument group to handle reservation affinity configurations."""
  group = parser.add_group(help=group_text)
  choices = {
      'any': 'Consume any available, matching reservation.',
      'none': 'Do not consume from any reserved capacity.',
      'specific': 'Must consume from a specific reservation.',
  }
  if support_specific_then_x_affinity:
    choices.update({
        'specific-then-any-reservation': (
            'Prefer to consume from a specific reservation, but still'
            ' consume any available matching reservation if the specified'
            ' reservation is not available or exhausted.'
        ),
        'specific-then-no-reservation': (
            'Prefer to consume from a specific reservation, but still'
            ' consume from the on-demand pool if the specified reservation'
            ' is not available or exhausted.'
        ),
    })
  group.add_argument(
      '--reservation-affinity',
      choices=choices,
      default='any',
      help=affinity_text,
  )
  if support_specific_then_x_affinity:
    reservation_help_text = """
The name of the reservation, required when `--reservation-affinity` is one of: `specific`, `specific-then-any-reservation` or `specific-then-no-reservation`.
"""
  else:
    reservation_help_text = """
The name of the reservation, required when `--reservation-affinity=specific`.
"""
  group.add_argument(
      '--reservation',
      help=reservation_help_text,
  )


def ValidateReservationAffinityGroup(args):
  """Validates flags specifying reservation affinity."""
  affinity = getattr(args, 'reservation_affinity', None)
  if affinity in [
      'specific',
      'specific-then-any-reservation',
      'specific-then-no-reservation',
  ]:
    if not args.IsSpecified('reservation'):
      raise exceptions.InvalidArgumentException(
          '--reservation',
          'The name the specific reservation must be specified.',
      )


def _GetContainerMountDescriptionAndNameDescription(for_update=False):
  """Get description text for --container-mount-disk flag."""
  if for_update:
    description = ("""\
Mounts a disk to the container by using mount-path or updates how the volume is
mounted if the same mount path has already been declared. The disk must already
be attached to the instance with a device-name that matches the disk name.
Multiple flags are allowed.
""")
    name_description = ("""\
Name of the disk. Can be omitted if exactly one additional disk is attached to
the instance. The name of the single additional disk will be used by default.
""")
    return description, name_description
  else:
    description = ("""\
Mounts a disk to the specified mount path in the container. Multiple '
flags are allowed. Must be used with `--disk` or `--create-disk`.
""")
    name_description = ("""\
Name of the disk. If exactly one additional disk is attached
to the instance using `--disk` or `--create-disk`, specifying disk
name here is optional. The name of the single additional disk will be
used by default.
""")
    return description, name_description


def ParseMountVolumeMode(argument_name, mode):
  """Parser for mode option in ArgDict specs."""
  if not mode or mode == 'rw':
    return containers_utils.MountVolumeMode.READ_WRITE
  elif mode == 'ro':
    return containers_utils.MountVolumeMode.READ_ONLY
  else:
    raise exceptions.InvalidArgumentException(argument_name,
                                              'Mode can only be [ro] or [rw].')


def AddContainerMountDiskFlag(parser, for_update=False):
  """Add --container-mount-disk flag."""
  description, name_description = (
      _GetContainerMountDescriptionAndNameDescription(for_update=for_update))
  help_text = ("""\
{}

*name*::: {}

*mount-path*::: Path on container to mount to. Mount paths with spaces
      and commas (and other special characters) are not supported by this
      command.

*partition*::: Optional. The partition of the disk to mount. Multiple
partitions of a disk can be mounted.{}

*mode*::: Volume mount mode: `rw` (read/write) or `ro` (read-only).
Defaults to `rw`. Fails if the disk mode is `ro` and volume mount mode
is `rw`.
""".format(description, name_description,
           '' if for_update else ' Can\'t be used with --create-disk.'))

  spec = {
      'name': str,
      'mount-path': str,
      'partition': int,
      'mode': functools.partial(ParseMountVolumeMode, '--container-mount-disk')
  }
  parser.add_argument(
      '--container-mount-disk',
      type=arg_parsers.ArgDict(spec=spec, required_keys=['mount-path']),
      help=help_text,
      action='append')


def _GetMatchingDiskFromMessages(holder, mount_disk_name, disk, client=None):
  """Helper to match a mount disk's name to a disk message."""
  if client is None:
    client = apis.GetClientClass('compute', 'alpha')
  if mount_disk_name is None and len(disk) == 1:
    return {
        'name':
            holder.resources.Parse(disk[0].source).Name(),
        'device_name':
            disk[0].deviceName,
        'ro':
            (disk[0].mode ==
             client.MESSAGES_MODULE.AttachedDisk.ModeValueValuesEnum.READ_WRITE)
    }, False
  for disk_spec in disk:
    disk_name = holder.resources.Parse(disk_spec.source).Name()
    if disk_name == mount_disk_name:
      return {
          'name':
              disk_name,
          'device_name':
              disk_spec.deviceName,
          'ro': (disk_spec.mode == client.MESSAGES_MODULE.AttachedDisk
                 .ModeValueValuesEnum.READ_WRITE)
      }, False
  return None, None


def _GetMatchingDiskFromFlags(mount_disk_name, disk, create_disk):
  """Helper to match a mount disk's name to a disk spec from a flag."""

  def _GetMatchingDiskFromSpec(spec):
    return {
        'name': spec.get('name'),
        'device_name': spec.get('device-name'),
        'ro': spec.get('mode') == 'ro'
    }

  if mount_disk_name is None and len(disk + create_disk) == 1:
    disk_spec = (disk + create_disk)[0]
    return _GetMatchingDiskFromSpec(disk_spec), bool(create_disk)
  for disk_spec in disk:
    if disk_spec.get('name') == mount_disk_name:
      return _GetMatchingDiskFromSpec(disk_spec), False
  for disk_spec in create_disk:
    if disk_spec.get('name') == mount_disk_name:
      return _GetMatchingDiskFromSpec(disk_spec), True
  return None, None


def _CheckMode(name, mode_value, mount_disk, matching_disk, create):
  """Make sure the correct mode is specified for container mount disk."""
  partition = mount_disk.get('partition')
  if (mode_value == containers_utils.MountVolumeMode.READ_WRITE and
      matching_disk.get('ro')):
    raise exceptions.InvalidArgumentException(
        '--container-mount-disk',
        'Value for [mode] in [--container-mount-disk] cannot be [rw] if the '
        'disk is attached in [ro] mode: disk name [{}], partition [{}]'.format(
            name, partition))
  if matching_disk.get('ro') and create:
    raise exceptions.InvalidArgumentException(
        '--container-mount-disk',
        'Cannot mount disk named [{}] to container: disk is created in [ro] '
        'mode and thus cannot be formatted.'.format(name))


def GetValidatedContainerMountDisk(holder,
                                   container_mount_disk,
                                   disk,
                                   create_disk,
                                   for_update=False,
                                   client=None):
  """Validate --container-mount-disk value."""
  disk = disk or []
  create_disk = create_disk or []
  if not container_mount_disk:
    return
  if not (disk or create_disk or for_update):
    raise exceptions.InvalidArgumentException(
        '--container-mount-disk',
        'Must be used with `--disk` or `--create-disk`')

  message = '' if for_update else ' using `--disk` or `--create-disk`.'
  validated_disks = []
  for mount_disk in container_mount_disk:
    if for_update:
      matching_disk, create = _GetMatchingDiskFromMessages(
          holder, mount_disk.get('name'), disk, client=client)
    else:
      matching_disk, create = _GetMatchingDiskFromFlags(
          mount_disk.get('name'), disk, create_disk)
    if not mount_disk.get('name'):
      if len(disk + create_disk) != 1:
        raise exceptions.InvalidArgumentException(
            '--container-mount-disk',
            'Must specify the name of the disk to be mounted unless exactly '
            'one disk is attached to the instance{}.'.format(message))
      name = matching_disk.get('name')
      if not name:
        raise exceptions.InvalidArgumentException(
            '--container-mount-disk',
            'When attaching or creating a disk that is also being mounted to '
            'a container, must specify the disk name.')
    else:
      name = mount_disk.get('name')
      if not matching_disk:
        raise exceptions.InvalidArgumentException(
            '--container-mount-disk',
            'Attempting to mount a disk that is not attached to the instance: '
            'must attach a disk named [{}]{}'.format(name, message))
    if (matching_disk and matching_disk.get('device_name') and
        matching_disk.get('device_name') != matching_disk.get('name')):
      raise exceptions.InvalidArgumentException(
          '--container-mount-disk',
          'Container mount disk cannot be used with a device whose device-name '
          'is different from its name. The disk with name [{}] has the '
          'device-name [{}].'.format(
              matching_disk.get('name'), matching_disk.get('device_name')))

    mode_value = mount_disk.get('mode')
    if matching_disk:
      _CheckMode(name, mode_value, mount_disk, matching_disk, create)
    if matching_disk and create and mount_disk.get('partition'):
      raise exceptions.InvalidArgumentException(
          '--container-mount-disk',
          'Container mount disk cannot specify a partition when the disk '
          'is created with --create-disk: disk name [{}], partition [{}]'
          .format(name, mount_disk.get('partition')))
    mount_disk = copy.deepcopy(mount_disk)
    mount_disk['name'] = mount_disk.get('name') or name
    validated_disks.append(mount_disk)
  return validated_disks


def NonEmptyString(parameter_name):

  def Factory(string):
    if not string:
      raise exceptions.InvalidArgumentException(parameter_name,
                                                'Empty string is not allowed.')
    return string

  return Factory


def _AddContainerEnvGroup(parser):
  """Add flags to update the container environment."""

  env_group = parser.add_argument_group()

  env_group.add_argument(
      '--container-env',
      type=arg_parsers.ArgDict(),
      action='append',
      metavar='KEY=VALUE, ...',
      help="""\
      Update environment variables `KEY` with value `VALUE` passed to
      container.
      - Sets `KEY` to the specified value.
      - Adds `KEY` = `VALUE`, if `KEY` is not yet declared.
      - Only the last value of `KEY` is taken when `KEY` is repeated more
      than once.

      Values, declared with `--container-env` flag override those with the
      same `KEY` from file, provided in `--container-env-file`.
      """)

  env_group.add_argument(
      '--container-env-file',
      help="""\
      Update environment variables from a file.
      Same update rules as for `--container-env` apply.
      Values, declared with `--container-env` flag override those with the
      same `KEY` from file.

      File with environment variables declarations in format used by docker
      (almost). This means:
      - Lines are in format KEY=VALUE
      - Values must contain equality signs.
      - Variables without values are not supported (this is different from
      docker format).
      - If # is first non-whitespace character in a line the line is ignored
      as a comment.
      """)

  env_group.add_argument(
      '--remove-container-env',
      type=arg_parsers.ArgList(),
      action='append',
      metavar='KEY',
      help="""\
      Removes environment variables `KEY` from container declaration Does
      nothing, if a variable is not present.
      """)


def _AddContainerArgGroup(parser):
  """Add flags to update the container arg."""

  arg_group = parser.add_mutually_exclusive_group()

  arg_group.add_argument(
      '--container-arg',
      action='append',
      help="""\
      Completely replaces the list of arguments with the new list.
      Each argument must have a separate --container-arg flag.
      Arguments are appended the new list in the order of flags.

      Cannot be used in the same command with `--clear-container-arg`.
      """)

  arg_group.add_argument(
      '--clear-container-args',
      action='store_true',
      default=None,
      help="""\
      Removes the list of arguments from container declaration.

      Cannot be used in the same command with `--container-arg`.
      """)


def _AddContainerCommandGroup(parser):
  """Add flags to update the command in the container declaration."""
  command_group = parser.add_mutually_exclusive_group()

  command_group.add_argument(
      '--container-command',
      type=NonEmptyString('--container-command'),
      help="""\
      Sets command in the declaration to the specified value.
      Empty string is not allowed.

      Cannot be used in the same command with `--clear-container-command`.
      """)

  command_group.add_argument(
      '--clear-container-command',
      action='store_true',
      default=None,
      help="""\
      Removes command from container declaration.

      Cannot be used in the same command with `--container-command`.
      """)


def _AddContainerMountHostPathFlag(parser, for_update=False):
  """Helper to add --container-mount-host-path flag."""
  if for_update:
    additional = """\

      - Adds a volume, if `mount-path` is not yet declared.
      - Replaces a volume, if `mount-path` is declared.
      All parameters (`host-path`, `mount-path`, `mode`) are completely
      replaced."""
  else:
    additional = ''
  parser.add_argument(
      '--container-mount-host-path',
      metavar='host-path=HOSTPATH,mount-path=MOUNTPATH[,mode=MODE]',
      type=arg_parsers.ArgDict(
          spec={
              'host-path':
                  str,
              'mount-path':
                  str,
              'mode':
                  functools.partial(ParseMountVolumeMode,
                                    '--container-mount-host-path')
          }),
      action='append',
      help="""\
      Mounts a volume by using host-path.{}

      *host-path*::: Path on host to mount from.

      *mount-path*::: Path on container to mount to. Mount paths with spaces
      and commas (and other special characters) are not supported by this
      command.

      *mode*::: Volume mount mode: rw (read/write) or ro (read-only).

      Default: rw.
      """.format(additional))


def _AddContainerMountTmpfsFlag(parser):
  """Helper to add --container-mount-tmpfs flag."""
  parser.add_argument(
      '--container-mount-tmpfs',
      metavar='mount-path=MOUNTPATH',
      type=arg_parsers.ArgDict(spec={'mount-path': str}),
      action='append',
      help="""\
      Mounts empty tmpfs into container at MOUNTPATH.

      *mount-path*::: Path on container to mount to. Mount paths with spaces
      and commas (and other special characters) are not supported by this
      command.
      """)


def _AddContainerMountGroup(parser, container_mount_disk_enabled=False):
  """Add flags to update what is mounted to the container."""

  mount_group = parser.add_argument_group()

  _AddContainerMountHostPathFlag(mount_group, for_update=True)
  _AddContainerMountTmpfsFlag(mount_group)

  if container_mount_disk_enabled:
    AddContainerMountDiskFlag(parser, for_update=True)

  mount_types = ['`host-path`', '`tmpfs`']
  if container_mount_disk_enabled:
    mount_types.append('`disk`')
  mount_group.add_argument(
      '--remove-container-mounts',
      type=arg_parsers.ArgList(),
      metavar='MOUNTPATH[,MOUNTPATH,...]',
      help="""\
      Removes volume mounts ({}) with
      `mountPath: MOUNTPATH` from container declaration.

      Does nothing, if a volume mount is not declared.
      """.format(', '.join(mount_types)))


def _AddContainerArgs(parser):
  """Add basic args for update-container."""

  parser.add_argument(
      '--container-image',
      type=NonEmptyString('--container-image'),
      help="""\
      Sets container image in the declaration to the specified value.

      Empty string is not allowed.
      """)

  parser.add_argument(
      '--container-privileged',
      action='store_true',
      default=None,
      help="""\
      Sets permission to run container to the specified value.
      """)

  parser.add_argument(
      '--container-stdin',
      action='store_true',
      default=None,
      help="""\
      Sets configuration whether to keep container `STDIN` always open to the
      specified value.
      """)

  parser.add_argument(
      '--container-tty',
      action='store_true',
      default=None,
      help="""\
      Sets configuration whether to allocate a pseudo-TTY for the container
      to the specified value.
      """)

  parser.add_argument(
      '--container-restart-policy',
      choices=['never', 'on-failure', 'always'],
      metavar='POLICY',
      type=lambda val: val.lower(),
      help="""\
      Sets container restart policy to the specified value.
      """)


def AddUpdateContainerArgs(parser, container_mount_disk_enabled=False):
  """Add all args to update the container environment."""
  INSTANCE_ARG.AddArgument(parser, operation_type='update')
  _AddContainerCommandGroup(parser)
  _AddContainerEnvGroup(parser)
  _AddContainerArgGroup(parser)
  _AddContainerMountGroup(
      parser, container_mount_disk_enabled=container_mount_disk_enabled)
  _AddContainerArgs(parser)
  AddShieldedInstanceConfigArgs(
      parser, use_default_value=False, for_update=True, for_container=True)
  AddShieldedInstanceIntegrityPolicyArgs(parser)


def AddPostKeyRevocationActionTypeArgs(parser):
  """Helper to add --post-key-revocation-action-type flag."""
  help_text = ('Specifies the behavior of the instance when the KMS key of one '
               'of its attached disks is revoked. The default is noop.')
  choices_text = {
      'noop':
          'No operation is performed.',
      'shutdown': ('The instance is shut down when the KMS key of one of '
                   'its attached disks is revoked.')
  }
  parser.add_argument(
      '--post-key-revocation-action-type',
      choices=choices_text,
      metavar='POLICY',
      required=False,
      help=help_text)


def AddNestedVirtualizationArgs(parser):
  parser.add_argument(
      '--enable-nested-virtualization',
      action=arg_parsers.StoreTrueFalseAction,
      help="""\
      If set to true, enables nested virtualization for the instance.
      """)


def AddThreadsPerCoreArgs(parser):
  parser.add_argument(
      '--threads-per-core',
      type=int,
      help="""
      The number of visible threads per physical core. To disable simultaneous
      multithreading (SMT) set this to 1. Valid values are: 1 or 2.

      For more information about configuring SMT, see:
      https://cloud.google.com/compute/docs/instances/configuring-simultaneous-multithreading.
    """)


def AddEnableUefiNetworkingArgs(parser):
  parser.add_argument(
      '--enable-uefi-networking',
      action=arg_parsers.StoreTrueFalseAction,
      help="""\
      If set to true, enables UEFI networking for the instance creation.
      """)


def AddPerformanceMonitoringUnitArgs(parser):
  parser.add_argument(
      '--performance-monitoring-unit',
      choices={
          'architectural': 'Enable architecturally defined non-LLC events.',
          'standard': 'Enable most documented core/L2 events.',
          'enhanced': 'Enable most documented core/L2 and LLC events.',
      },
      type=str,
      help=(
          'The set of performance measurement counters to enable for the'
          ' instance.'
      ),
  )


def AddNumaNodeCountArgs(parser):
  parser.add_argument(
      '--numa-node-count',
      type=int,
      help="""\
      The number of virtual NUMA nodes for the instance.
      Valid values are: 0, 1, 2, 4 or 8. Setting NUMA node count to 0 means
      using the default setting.
      """)


def AddVisibleCoreCountArgs(parser):
  parser.add_argument(
      '--visible-core-count',
      type=int,
      help="""
      The number of physical cores to expose to the instance's guest operating
      system. The number of virtual CPUs visible to the instance's guest
      operating system is this number of cores multiplied by the instance's
      count of visible threads per physical core.
    """)


def AddStackTypeArgs(parser, support_ipv6_only=False):
  """Adds stack type arguments for instance."""
  choices = {
      'IPV4_ONLY': 'The network interface will be assigned IPv4 addresses',
      'IPV4_IPV6': (
          'The network interface can have both IPv4 and IPv6 addresses'
      ),
  }
  if support_ipv6_only:
    choices['IPV6_ONLY'] = (
        'The network interface will be assigned IPv6 addresses'
    )
  parser.add_argument(
      '--stack-type',
      choices=choices,
      type=arg_utils.ChoiceToEnumName,
      help=(
          'Specifies whether IPv6 is enabled on the default network '
          'interface. If not specified, IPV4_ONLY will be used.'
      ),
  )


def AddIpv6NetworkTierArgs(parser):
  """Adds IPv6 network tier for network interface IPv6 access config."""
  parser.add_argument(
      '--ipv6-network-tier',
      choices={
          'PREMIUM': ('High quality, Google-grade network tier.'),
      },
      type=arg_utils.ChoiceToEnumName,
      help=('Specifies the IPv6 network tier that will be used to configure '
            'the instance network interface IPv6 access config.'))


def AddIPv6AddressArgs(parser):
  parser.add_argument(
      '--external-ipv6-address',
      type=NonEmptyString('--external-ipv6-address'),
      help="""
      Assigns the given external IPv6 address to the instance that is created.
      The address must be the first IP address in the range. This option can be
      used only when creating a single instance.
    """)


def AddIPv6AddressAlphaArgs(parser):
  parser.add_argument(
      '--ipv6-address',
      type=NonEmptyString('--ipv6-address'),
      help="""
      Assigns the given external IPv6 address to the instance that is created.
      The address must be the first IP address in the range. This option can be
      used only when creating a single instance.
    """)


def AddIPv6PrefixLengthArgs(parser):
  parser.add_argument(
      '--external-ipv6-prefix-length',
      type=int,
      help="""
      The prefix length of the external IPv6 address range. This field should be
      used together with `--external-ipv6-address`. Only the /96 IP address range
      is supported, and the default value is 96.
    """)


def AddIPv6PrefixLengthAlphaArgs(parser):
  parser.add_argument(
      '--ipv6-prefix-length',
      type=int,
      help="""
      The prefix length of the external IPv6 address range. This field should be
      used together with `--ipv6-address`. Only the /96 IP address range is
      supported, and the default value is 96.
    """)


def AddInternalIPv6AddressArgs(parser):
  parser.add_argument(
      '--internal-ipv6-address',
      type=NonEmptyString('--internal-ipv6-address'),
      help="""
      Assigns the given internal IPv6 address or range to the instance that is
      created. The address must be the first IP address in the range or from a
      /96 IP address range. This option can be used only when creating a single
      instance.
    """,
  )


def AddInternalIPv6PrefixLengthArgs(parser):
  parser.add_argument(
      '--internal-ipv6-prefix-length',
      type=int,
      help="""
      Optional field that indicates the prefix length of the internal IPv6
      address range. It should be used together with --internal-ipv6-address.
      Only /96 IP address range is supported and the default value is 96. If
      not set, either the prefix length from --internal-ipv6-address will be
      used or the default value of 96 will be assigned.
    """,
  )


def AddNetworkPerformanceConfigsArgs(parser):
  """Adds config flags for advanced networking bandwidth tiers."""

  network_perf_config_help = """\
      Configures network performance settings for the instance.
      If this flag is not specified, the instance will be created
      with its default network performance configuration.

      *total-egress-bandwidth-tier*::: Total egress bandwidth is the available
      outbound bandwidth from a VM, regardless of whether the traffic
      is going to internal IP or external IP destinations.
      The following tier values are allowed: [{tier_values}]

      """.format(tier_values=','.join([
          six.text_type(tier_val)
          for tier_val in constants.ADV_NETWORK_TIER_CHOICES
      ]))

  spec = {'total-egress-bandwidth-tier': str}

  parser.add_argument(
      '--network-performance-configs',
      type=arg_parsers.ArgDict(spec=spec),
      action='append',
      metavar='PROPERTY=VALUE',
      help=network_perf_config_help)


def ValidateNetworkPerformanceConfigsArgs(args):
  """Validates advanced networking bandwidth tier values."""

  for config in getattr(args, 'network_performance_configs', []) or []:
    total_tier = config.get('total-egress-bandwidth-tier', '').upper()
    if (total_tier and total_tier not in constants.ADV_NETWORK_TIER_CHOICES):
      raise exceptions.InvalidArgumentException(
          '--network-performance-configs',
          """Invalid total-egress-bandwidth-tier tier value, "{tier}".
             Tier value must be one of the following {tier_values}""".format(
                 tier=total_tier,
                 tier_values=','.join([
                     six.text_type(tier_val)
                     for tier_val in constants.ADV_NETWORK_TIER_CHOICES
                 ])))


def AddNodeProjectArgs(parser):
  """Adds node project argument."""
  parser.add_argument(
      '--node-project',
      help="""\
      The name of the project with shared sole tenant node groups to create
      an instance in.""")


def AddKeyRevocationActionTypeArgs(parser):
  """Helper to add --key-revocation-action-type flag."""
  help_text = ('Specifies the behavior of the instance when the KMS key of one '
               'of its attached disks is revoked. The default is none.')
  choices_text = {
      'none': 'No operation is performed.',
      'stop': 'The instance is stopped when the KMS key of one of its attached '
              'disks is revoked.'
  }
  parser.add_argument(
      '--key-revocation-action-type',
      choices=choices_text,
      metavar='POLICY',
      required=False,
      help=help_text)


def AddMaintenanceIntervalArgs(parser):
  """Adds maintenance interval arguments for instance."""
  help_text = 'Specifies the frequency of planned maintenance events.'
  choices_text = {'PERIODIC': 'PERIODIC means the VM is a Stable Fleet VM.'}
  parser.add_argument(
      '--maintenance-interval',
      choices=choices_text,
      type=arg_utils.ChoiceToEnumName,
      help=help_text,
  )


def AddAvailabilityDomainAgrs(parser):
  parser.add_argument(
      '--availability-domain',
      type=arg_parsers.BoundedInt(lower_bound=1, upper_bound=8),
      help="""
          Specifies the availability domain that this VM instance should be
          scheduled on. The number of availability domains that a VM can be
          scheduled on is specified when you create the spread placement
          policy.

          Specify a value from 1 to the number of domains that are available in
          your placement policy.
          """,
  )
