# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for creating disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import textwrap

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import disks_util
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import kms_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute import zone_utils
from googlecloudsdk.api_lib.compute.regions import utils as region_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.disks import create
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.command_lib.compute.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.compute.resource_policies import flags as resource_flags
from googlecloudsdk.command_lib.compute.resource_policies import util as resource_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
import six

DETAILED_HELP = {
    'brief':
        'Create Compute Engine persistent disks',
    'DESCRIPTION':
        """\
        *{command}* creates one or more Compute Engine
        persistent disks. When creating virtual machine instances,
        disks can be attached to the instances through the
        `gcloud compute instances create` command. Disks can also be
        attached to instances that are already running using
        `gcloud compute instances attach-disk`.

        Disks are zonal resources, so they reside in a particular zone
        for their entire lifetime. The contents of a disk can be moved
        to a different zone by snapshotting the disk (using
        `gcloud compute disks snapshot`) and creating a new disk using
        `--source-snapshot` in the desired zone. The contents of a
        disk can also be moved across project or zone by creating an
        image (using `gcloud compute images create`) and creating a
        new disk using `--image` in the desired project and/or
        zone.

        For a comprehensive guide, including details on minimum and maximum
        disk size, refer to:
        https://cloud.google.com/compute/docs/disks
        """,
    'EXAMPLES':
        """\
        When creating disks, be sure to include the `--zone` option. To create
        disks 'my-disk-1' and 'my-disk-2' in zone us-east1-a:

          $ {command} my-disk-1 my-disk-2 --zone=us-east1-a
        """,
}


def _SourceArgs(parser):
  """Add mutually exclusive source args."""
  source_parent_group = parser.add_group()
  source_group = source_parent_group.add_mutually_exclusive_group()

  def AddImageHelp():
    """Returns detailed help for `--image` argument."""
    template = """\
        An image to apply to the disks being created. When using
        this option, the size of the disks must be at least as large as
        the image size. Use ``--size'' to adjust the size of the disks.

        This flag is mutually exclusive with ``--source-snapshot'' and
        ``--image-family''.
        """
    return template

  source_group.add_argument('--image', help=AddImageHelp)

  image_utils.AddImageProjectFlag(source_parent_group)

  source_group.add_argument(
      '--image-family',
      help="""\
        The image family for the operating system that the boot disk will be
        initialized with. Compute Engine offers multiple Linux
        distributions, some of which are available as both regular and
        Shielded VM images.  When a family is specified instead of an image,
        the latest non-deprecated image associated with that family is
        used. It is best practice to use --image-family when the latest
        version of an image is needed.
        """)
  image_utils.AddImageFamilyScopeFlag(source_parent_group)

  disks_flags.SOURCE_SNAPSHOT_ARG.AddArgument(source_group)
  disks_flags.SOURCE_INSTANT_SNAPSHOT_ARG.AddArgument(source_group)
  disks_flags.SOURCE_DISK_ARG.AddArgument(parser, mutex_group=source_group)
  disks_flags.ASYNC_PRIMARY_DISK_ARG.AddArgument(
      parser, mutex_group=source_group
  )
  disks_flags.AddPrimaryDiskProject(parser)
  disks_flags.AddLocationHintArg(parser)


def _CommonArgs(
    messages,
    parser,
    include_physical_block_size_support=False,
    vss_erase_enabled=False,
    support_pd_interface=False,
    support_user_licenses=False,
    support_storage_pool=False,
    support_access_mode=False,
):
  """Add arguments used for parsing in all command tracks."""
  Create.disks_arg.AddArgument(parser, operation_type='create')
  parser.add_argument(
      '--description',
      help='An optional, textual description for the disks being created.')

  parser.add_argument(
      '--size',
      type=arg_parsers.BinarySize(
          lower_bound='1GB',
          suggested_binary_size_scales=['GB', 'GiB', 'TB', 'TiB', 'PiB', 'PB']),
      help="""\
        Size of the disks. The value must be a whole
        number followed by a size unit of ``GB'' for gigabyte, or ``TB''
        for terabyte. If no size unit is specified, GB is
        assumed. For example, ``10GB'' will produce 10 gigabyte
        disks. Disk size must be a multiple of 1 GB. If disk size is
        not specified, the default size of {}GB for pd-standard disks, {}GB for
        pd-balanced disks, {}GB for pd-ssd disks, and {}GB for pd-extreme will
        be used. For details about disk size limits, refer to:
        https://cloud.google.com/compute/docs/disks
        """.format(
            constants.DEFAULT_DISK_SIZE_GB_MAP[constants.DISK_TYPE_PD_STANDARD],
            constants.DEFAULT_DISK_SIZE_GB_MAP[constants.DISK_TYPE_PD_BALANCED],
            constants.DEFAULT_DISK_SIZE_GB_MAP[constants.DISK_TYPE_PD_SSD],
            constants.DEFAULT_DISK_SIZE_GB_MAP[constants.DISK_TYPE_PD_EXTREME]))

  parser.add_argument(
      '--type',
      completer=completers.DiskTypesCompleter,
      help="""\
      Specifies the type of disk to create. To get a
      list of available disk types, run `gcloud compute disk-types list`.
      The default disk type is pd-standard.
      """)

  if support_pd_interface:
    parser.add_argument(
        '--interface',
        help="""\
        Specifies the disk interface to use for attaching this disk. Valid values
        are `SCSI` and `NVME`. The default is `SCSI`.
        """)

  parser.display_info.AddFormat(
      'table(name, zone.basename(), sizeGb, type.basename(), status)')

  parser.add_argument(
      '--licenses',
      type=arg_parsers.ArgList(),
      metavar='LICENSE',
      help=('A list of URIs to license resources. The provided licenses will '
            'be added onto the created disks to indicate the licensing and '
            'billing policies.'))

  _SourceArgs(parser)

  disks_flags.AddProvisionedIopsFlag(parser, arg_parsers)
  disks_flags.AddArchitectureFlag(parser, messages)

  disks_flags.AddProvisionedThroughputFlag(parser, arg_parsers)

  if support_storage_pool:
    disks_flags.STORAGE_POOL_ARG.AddArgument(parser)

  if support_access_mode:
    disks_flags.AddAccessModeFlag(parser, messages)

  if support_user_licenses:
    parser.add_argument(
        '--user-licenses',
        type=arg_parsers.ArgList(),
        metavar='LICENSE',
        help=('List of URIs to license resources. User-provided licenses '
              'can be edited after disk is created.'))

  csek_utils.AddCsekKeyArgs(parser)
  labels_util.AddCreateLabelsFlags(parser)

  if include_physical_block_size_support:
    parser.add_argument(
        '--physical-block-size',
        choices=['4096', '16384'],
        default='4096',
        help="""\
Physical block size of the persistent disk in bytes.
Valid values are 4096(default) and 16384.
""")
  if vss_erase_enabled:
    flags.AddEraseVssSignature(parser, resource='a source snapshot')

  resource_flags.AddResourcePoliciesArgs(parser, 'added to', 'disk')


def _AddReplicaZonesArg(parser):
  parser.add_argument(
      '--replica-zones',
      type=arg_parsers.ArgList(min_length=2, max_length=2),
      metavar='ZONE',
      help=('A comma-separated list of exactly 2 zones that a regional disk '
            'will be replicated to. Required when creating regional disk. '
            'The zones must be in the same region as specified in the '
            '`--region` flag. See available zones with '
            '`gcloud compute zones list`.'))


def _ParseGuestOsFeaturesToMessages(args, client_messages):
  """Parse GuestOS features."""
  guest_os_feature_messages = []
  if args.guest_os_features:
    for feature in args.guest_os_features:
      gf_type = client_messages.GuestOsFeature.TypeValueValuesEnum(feature)
      guest_os_feature = client_messages.GuestOsFeature()
      guest_os_feature.type = gf_type
      guest_os_feature_messages.append(guest_os_feature)

  return guest_os_feature_messages


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  """Create Compute Engine persistent disks."""

  @classmethod
  def Args(cls, parser):
    messages = cls._GetApiHolder(no_http=True).client.messages
    Create.disks_arg = disks_flags.MakeDiskArg(plural=True)
    _CommonArgs(messages, parser)
    image_utils.AddGuestOsFeaturesArg(parser, messages)
    _AddReplicaZonesArg(parser)
    kms_resource_args.AddKmsKeyResourceArg(
        parser, 'disk', region_fallthrough=True)
    disks_flags.AddEnableConfidentialComputeFlag(parser)

  def ParseLicenses(self, args):
    """Parse license.

    Subclasses may override it to customize parsing.

    Args:
      args: The argument namespace

    Returns:
      List of licenses.
    """
    if args.licenses:
      return args.licenses
    return []

  def ValidateAndParseDiskRefs(self, args, compute_holder):
    return _ValidateAndParseDiskRefsRegionalReplica(args, compute_holder)

  def GetFromImage(self, args):
    return args.image or args.image_family

  def GetFromSourceInstantSnapshot(self, args):
    return args.source_instant_snapshot

  def GetDiskSizeGb(self, args, from_image):
    size_gb = utils.BytesToGb(args.size)

    if size_gb:
      # Legacy disk type cannot be smaller than 10 GB and it is enforced in
      # gcloud.
      if args.type in constants.LEGACY_DISK_TYPE_LIST and size_gb < 10:
        raise exceptions.InvalidArgumentException(
            '--size',
            'Value must be greater than or equal to 10 GB; reveived {0} GB'
            .format(size_gb),
        )
      # if disk size is given, use it.
      pass
    elif (
        args.source_snapshot
        or from_image
        or args.source_disk
        or self.GetFromSourceInstantSnapshot(args)
    ):
      # if source is a snapshot/image/disk/instant-snapshot, it is ok not to
      # set size_gb since disk size can be obtained from the source.
      pass
    elif args.type in constants.DEFAULT_DISK_SIZE_GB_MAP:
      # Get default disk size from disk_type.
      size_gb = constants.DEFAULT_DISK_SIZE_GB_MAP[args.type]
    elif args.type:
      # If disk type is specified, then leaves it to backend to decide the size.
      pass
    else:
      # If disk type is unspecified or unknown, we use the default size of
      # pd-standard.
      size_gb = constants.DEFAULT_DISK_SIZE_GB_MAP[
          constants.DISK_TYPE_PD_STANDARD]
    utils.WarnIfDiskSizeIsTooSmall(size_gb, args.type)
    return size_gb

  def GetProjectToSourceImageDict(self, args, disk_refs, compute_holder,
                                  from_image):
    project_to_source_image = {}

    image_expander = image_utils.ImageExpander(compute_holder.client,
                                               compute_holder.resources)

    for disk_ref in disk_refs:
      if from_image:
        if disk_ref.project not in project_to_source_image:
          source_image_uri, _ = image_expander.ExpandImageFlag(
              user_project=disk_ref.project,
              image=args.image,
              image_family=args.image_family,
              image_project=args.image_project,
              return_image_resource=False,
              image_family_scope=args.image_family_scope,
              support_image_family_scope=True)
          project_to_source_image[disk_ref.project] = argparse.Namespace()
          project_to_source_image[disk_ref.project].uri = source_image_uri
      else:
        project_to_source_image[disk_ref.project] = argparse.Namespace()
        project_to_source_image[disk_ref.project].uri = None
    return project_to_source_image

  def WarnAboutScopeDeprecationsAndMaintenance(self, disk_refs, client):
    # Check if the zone is deprecated or has maintenance coming.
    zone_resource_fetcher = zone_utils.ZoneResourceFetcher(client)
    zone_resource_fetcher.WarnForZonalCreation(
        (ref for ref in disk_refs if ref.Collection() == 'compute.disks'))
    # Check if the region is deprecated or has maintenance coming.
    region_resource_fetcher = region_utils.RegionResourceFetcher(client)
    region_resource_fetcher.WarnForRegionalCreation(
        (ref for ref in disk_refs if ref.Collection() == 'compute.regionDisks'))

  def GetSnapshotUri(self, args, compute_holder):
    snapshot_ref = disks_flags.SOURCE_SNAPSHOT_ARG.ResolveAsResource(
        args, compute_holder.resources)
    if snapshot_ref:
      return snapshot_ref.SelfLink()
    return None

  def GetSourceInstantSnapshotUri(self, args, compute_holder):
    if args.source_instant_snapshot:
      instant_snapshot_ref = (
          disks_flags.SOURCE_INSTANT_SNAPSHOT_ARG.ResolveAsResource(
              args, compute_holder.resources
          )
      )
      if instant_snapshot_ref:
        return instant_snapshot_ref.SelfLink()
    return None

  def GetSourceDiskUri(self, args, disk_ref, compute_holder):
    source_disk_ref = None
    if args.source_disk:
      if args.source_disk_zone:
        source_disk_ref = disks_flags.SOURCE_DISK_ARG.ResolveAsResource(
            args, compute_holder.resources)
      else:
        if disk_ref.Collection() == 'compute.disks':
          source_disk_ref = disks_flags.SOURCE_DISK_ARG.ResolveAsResource(
              args,
              compute_holder.resources,
              default_scope=compute_scope.ScopeEnum.ZONE)
        elif disk_ref.Collection() == 'compute.regionDisks':
          source_disk_ref = disks_flags.SOURCE_DISK_ARG.ResolveAsResource(
              args,
              compute_holder.resources,
              default_scope=compute_scope.ScopeEnum.REGION)
      if source_disk_ref:
        return source_disk_ref.SelfLink()
    return None

  def GetAsyncPrimaryDiskUri(self, args, compute_holder):
    primary_disk_ref = None
    if args.primary_disk:
      primary_disk_project = getattr(args, 'primary_disk_project', None)
      primary_disk_ref = disks_flags.ASYNC_PRIMARY_DISK_ARG.ResolveAsResource(
          args, compute_holder.resources, source_project=primary_disk_project
      )
      if primary_disk_ref:
        return primary_disk_ref.SelfLink()
    return None

  def GetStoragePoolUri(self, args, compute_holder):
    if args.storage_pool:
      storage_pool_ref = disks_flags.STORAGE_POOL_ARG.ResolveAsResource(
          args,
          compute_holder.resources,
          default_scope=compute_scope.ScopeEnum.ZONE,
      )
      if storage_pool_ref:
        return storage_pool_ref.SelfLink()
    return None

  def GetLabels(self, args, client):
    labels = None
    args_labels = getattr(args, 'labels', None)
    if args_labels:
      labels = client.messages.Disk.LabelsValue(additionalProperties=[
          client.messages.Disk.LabelsValue.AdditionalProperty(
              key=key, value=value)
          for key, value in sorted(six.iteritems(args.labels))
      ])
    return labels

  def GetDiskTypeUri(self, args, disk_ref, compute_holder):
    if args.type:
      if disk_ref.Collection() == 'compute.disks':
        type_ref = compute_holder.resources.Parse(
            args.type,
            collection='compute.diskTypes',
            params={
                'project': disk_ref.project,
                'zone': disk_ref.zone
            })
      elif disk_ref.Collection() == 'compute.regionDisks':
        type_ref = compute_holder.resources.Parse(
            args.type,
            collection='compute.regionDiskTypes',
            params={
                'project': disk_ref.project,
                'region': disk_ref.region
            })
      return type_ref.SelfLink()
    return None

  def GetReplicaZones(self, args, compute_holder, disk_ref):
    result = []
    for zone in args.replica_zones:
      zone_ref = compute_holder.resources.Parse(
          zone,
          collection='compute.zones',
          params={'project': disk_ref.project})
      result.append(zone_ref.SelfLink())
    return result

  @classmethod
  def _GetApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def Run(self, args):
    return self._Run(args, supports_kms_keys=True)

  def _Run(
      self,
      args,
      supports_kms_keys=False,
      supports_physical_block=False,
      support_multiwriter_disk=False,
      support_vss_erase=False,
      support_pd_interface=False,
      support_user_licenses=False,
      support_enable_confidential_compute=True,
      support_storage_pool=False,
      support_access_mode=False,
  ):
    compute_holder = self._GetApiHolder()
    client = compute_holder.client

    self.show_unformated_message = not (args.IsSpecified('image') or
                                        args.IsSpecified('image_family') or
                                        args.IsSpecified('source_snapshot') or
                                        args.IsSpecified('source_disk'))
    self.show_unformated_message = self.show_unformated_message and not (
        args.IsSpecified('source_instant_snapshot'))

    disk_refs = self.ValidateAndParseDiskRefs(args, compute_holder)
    from_image = self.GetFromImage(args)
    size_gb = self.GetDiskSizeGb(args, from_image)
    self.WarnAboutScopeDeprecationsAndMaintenance(disk_refs, client)
    project_to_source_image = self.GetProjectToSourceImageDict(
        args, disk_refs, compute_holder, from_image)
    snapshot_uri = self.GetSnapshotUri(args, compute_holder)

    labels = self.GetLabels(args, client)

    csek_keys = csek_utils.CsekKeyStore.FromArgs(args, True)

    for project in project_to_source_image:
      source_image_uri = project_to_source_image[project].uri
      project_to_source_image[project].keys = (
          csek_utils.MaybeLookupKeyMessagesByUri(
              csek_keys, compute_holder.resources,
              [source_image_uri, snapshot_uri], client.apitools_client))

    guest_os_feature_messages = _ParseGuestOsFeaturesToMessages(
        args, client.messages)

    requests = []
    for disk_ref in disk_refs:
      type_uri = self.GetDiskTypeUri(args, disk_ref, compute_holder)

      kwargs = {}
      if csek_keys:
        disk_key_or_none = csek_keys.LookupKey(disk_ref,
                                               args.require_csek_key_create)
        disk_key_message_or_none = csek_utils.MaybeToMessage(
            disk_key_or_none, client.apitools_client)
        kwargs['diskEncryptionKey'] = disk_key_message_or_none
        kwargs['sourceImageEncryptionKey'] = (
            project_to_source_image[disk_ref.project].keys[0])
        kwargs['sourceSnapshotEncryptionKey'] = (
            project_to_source_image[disk_ref.project].keys[1])
      if labels:
        kwargs['labels'] = labels

      if supports_kms_keys:
        kwargs['diskEncryptionKey'] = kms_utils.MaybeGetKmsKey(
            args, client.messages, kwargs.get('diskEncryptionKey', None))

      # Those features are only exposed in alpha/beta, it would be nice to have
      # code supporting them only in alpha and beta versions of the command.
      # TODO(b/65161039): Stop checking release path in the middle of GA code.
      if support_pd_interface and args.interface:
        kwargs['interface'] = arg_utils.ChoiceToEnum(
            args.interface, client.messages.Disk.InterfaceValueValuesEnum)
      # end of alpha/beta features.

      if args.primary_disk:
        primary_disk = client.messages.DiskAsyncReplication()
        primary_disk.disk = self.GetAsyncPrimaryDiskUri(args, compute_holder)
        kwargs['asyncPrimaryDisk'] = primary_disk

      if supports_physical_block and args.IsSpecified('physical_block_size'):
        physical_block_size_bytes = int(args.physical_block_size)
      else:
        physical_block_size_bytes = None

      resource_policies = getattr(args, 'resource_policies', None)
      if resource_policies:
        if disk_ref.Collection() == 'compute.regionDisks':
          disk_region = disk_ref.region
        else:
          disk_region = utils.ZoneNameToRegionName(disk_ref.zone)
        parsed_resource_policies = []
        for policy in resource_policies:
          resource_policy_ref = resource_util.ParseResourcePolicy(
              compute_holder.resources,
              policy,
              project=disk_ref.project,
              region=disk_region)
          parsed_resource_policies.append(resource_policy_ref.SelfLink())
        kwargs['resourcePolicies'] = parsed_resource_policies

      disk = client.messages.Disk(
          name=disk_ref.Name(),
          description=args.description,
          sizeGb=size_gb,
          sourceSnapshot=snapshot_uri,
          sourceImage=project_to_source_image[disk_ref.project].uri,
          type=type_uri,
          physicalBlockSizeBytes=physical_block_size_bytes,
          **kwargs)
      disk.sourceDisk = self.GetSourceDiskUri(args, disk_ref, compute_holder)
      disk.sourceInstantSnapshot = self.GetSourceInstantSnapshotUri(
          args, compute_holder)

      if (support_multiwriter_disk and
          disk_ref.Collection() in ['compute.disks', 'compute.regionDisks'] and
          args.IsSpecified('multi_writer')):
        disk.multiWriter = args.multi_writer

      if support_enable_confidential_compute and args.IsSpecified(
          'confidential_compute'
      ):
        disk.enableConfidentialCompute = args.confidential_compute

      if guest_os_feature_messages:
        disk.guestOsFeatures = guest_os_feature_messages

      if support_vss_erase and args.IsSpecified('erase_windows_vss_signature'):
        disk.eraseWindowsVssSignature = args.erase_windows_vss_signature

      disk.licenses = self.ParseLicenses(args)

      if args.IsSpecified('provisioned_iops'):
        if type_uri and disks_util.IsProvisioningTypeIops(type_uri):
          disk.provisionedIops = args.provisioned_iops
        else:
          raise exceptions.InvalidArgumentException(
              '--provisioned-iops',
              '--provisioned-iops cannot be used with the given disk type.')

      if args.IsSpecified(
          'provisioned_throughput'):
        if type_uri and disks_util.IsProvisioningTypeThroughput(type_uri):
          disk.provisionedThroughput = args.provisioned_throughput
        else:
          raise exceptions.InvalidArgumentException(
              '--provisioned-throughput',
              '--provisioned-throughput cannot be used with the given disk '
              'type.')

      if args.IsSpecified('architecture'):
        disk.architecture = disk.ArchitectureValueValuesEnum(args.architecture)

      if support_access_mode and args.IsSpecified('access_mode'):
        disk.accessMode = disk.AccessModeValueValuesEnum(args.access_mode)

      if support_user_licenses and args.IsSpecified('user_licenses'):
        disk.userLicenses = args.user_licenses

      if args.IsSpecified('location_hint'):
        disk.locationHint = args.location_hint

      if support_storage_pool and args.IsSpecified('storage_pool'):
        disk.storagePool = self.GetStoragePoolUri(args, compute_holder)

      if disk_ref.Collection() == 'compute.disks':
        request = client.messages.ComputeDisksInsertRequest(
            disk=disk, project=disk_ref.project, zone=disk_ref.zone)

        request = (client.apitools_client.disks, 'Insert', request)
      elif disk_ref.Collection() == 'compute.regionDisks':
        if args.IsSpecified('replica_zones'):
          disk.replicaZones = self.GetReplicaZones(
              args, compute_holder, disk_ref
          )
        request = client.messages.ComputeRegionDisksInsertRequest(
            disk=disk, project=disk_ref.project, region=disk_ref.region)

        request = (client.apitools_client.regionDisks, 'Insert', request)

      requests.append(request)

    return client.MakeRequests(requests)

  def Epilog(self, resources_were_displayed=True):
    message = """\

        New disks are unformatted. You must format and mount a disk before it
        can be used. You can find instructions on how to do this at:

        https://cloud.google.com/compute/docs/disks/add-persistent-disk#formatting
        """
    if self.show_unformated_message:
      log.status.Print(textwrap.dedent(message))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create Compute Engine persistent disks."""

  @classmethod
  def Args(cls, parser):
    messages = cls._GetApiHolder(no_http=True).client.messages
    Create.disks_arg = disks_flags.MakeDiskArg(plural=True)
    _CommonArgs(
        messages,
        parser,
        include_physical_block_size_support=True,
        vss_erase_enabled=True,
        support_pd_interface=True,
    )
    image_utils.AddGuestOsFeaturesArg(parser, messages)
    _AddReplicaZonesArg(parser)
    kms_resource_args.AddKmsKeyResourceArg(
        parser, 'disk', region_fallthrough=True)
    disks_flags.AddMultiWriterFlag(parser)
    disks_flags.AddEnableConfidentialComputeFlag(parser)

  def Run(self, args):
    return self._Run(
        args,
        supports_kms_keys=True,
        supports_physical_block=True,
        support_vss_erase=True,
        support_multiwriter_disk=True,
        support_pd_interface=True,
        support_enable_confidential_compute=True)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create Compute Engine persistent disks."""

  @classmethod
  def Args(cls, parser):
    messages = cls._GetApiHolder(no_http=True).client.messages
    Create.disks_arg = disks_flags.MakeDiskArg(plural=True)
    _CommonArgs(
        messages,
        parser,
        include_physical_block_size_support=True,
        vss_erase_enabled=True,
        support_pd_interface=True,
        support_user_licenses=True,
        support_storage_pool=True,
        support_access_mode=True,
    )
    image_utils.AddGuestOsFeaturesArg(parser, messages)
    _AddReplicaZonesArg(parser)
    kms_resource_args.AddKmsKeyResourceArg(
        parser, 'disk', region_fallthrough=True)
    disks_flags.AddMultiWriterFlag(parser)
    disks_flags.AddEnableConfidentialComputeFlag(parser)

  def Run(self, args):
    return self._Run(
        args,
        supports_kms_keys=True,
        supports_physical_block=True,
        support_multiwriter_disk=True,
        support_vss_erase=True,
        support_pd_interface=True,
        support_user_licenses=True,
        support_enable_confidential_compute=True,
        support_storage_pool=True,
        support_access_mode=True,
    )


def _ValidateAndParseDiskRefsRegionalReplica(
    args, compute_holder
):
  """Validate flags and parse disks references.

  Subclasses may override it to customize parsing.

  Args:
    args: The argument namespace
    compute_holder: base_classes.ComputeApiHolder instance

  Returns:
    List of compute.regionDisks resources.
  """
  if (
      not args.IsSpecified('replica_zones')
      and args.IsSpecified('region')
      and not (args.IsSpecified('source_instant_snapshot'))
  ):
    raise exceptions.RequiredArgumentException(
        '--replica-zones',
        '--replica-zones is required for regional disk creation')
  if args.replica_zones is not None:
    return create.ParseRegionDisksResources(compute_holder.resources,
                                            args.DISK_NAME, args.replica_zones,
                                            args.project, args.region)

  disk_refs = Create.disks_arg.ResolveAsResource(
      args,
      compute_holder.resources,
      scope_lister=flags.GetDefaultScopeLister(compute_holder.client))

  # --replica-zones is required for regional disks unless a source instant
  # snapshot is specified - also when region is selected in prompt.
  for disk_ref in disk_refs:
    if (
        disk_ref.Collection() == 'compute.regionDisks'
        and not args.IsSpecified('source_instant_snapshot')
    ):
      raise exceptions.RequiredArgumentException(
          '--replica-zones',
          '--replica-zones is required for regional disk creation [{}]'.format(
              disk_ref.SelfLink()))

  return disk_refs


Create.detailed_help = DETAILED_HELP
