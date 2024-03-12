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
"""Command for labels update to disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import disks_util as api_util
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.command_lib.util.args import labels_util


def _CommonArgs(
    messages,
    cls,
    parser,
    support_user_licenses=False,
    support_access_mode=False,
):
  """Add arguments used for parsing in all command tracks."""
  cls.DISK_ARG = disks_flags.MakeDiskArg(plural=False)
  cls.DISK_ARG.AddArgument(parser, operation_type='update')
  labels_util.AddUpdateLabelsFlags(parser)

  if support_user_licenses:
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        '--update-user-licenses',
        type=arg_parsers.ArgList(),
        metavar='LICENSE',
        action=arg_parsers.UpdateAction,
        help=(
            'List of user licenses to be updated on a disk. These user licenses'
            ' will replace all existing user licenses. If this flag is not '
            'provided, all existing user licenses will remain unchanged.'))
    scope.add_argument(
        '--clear-user-licenses',
        action='store_true',
        help='Remove all existing user licenses on a disk.')

  scope = parser.add_mutually_exclusive_group()

  architecture_enum_type = messages.Disk.ArchitectureValueValuesEnum
  excluded_enums = [architecture_enum_type.ARCHITECTURE_UNSPECIFIED.name]
  architecture_choices = sorted(
      [e for e in architecture_enum_type.names() if e not in excluded_enums])
  scope.add_argument(
      '--update-architecture',
      choices=architecture_choices,
      help=(
          'Updates the architecture or processor type that this disk can support. For available processor types on Compute Engine, see https://cloud.google.com/compute/docs/cpu-platforms.'
      ))
  scope.add_argument(
      '--clear-architecture',
      action='store_true',
      help='Removes the architecture or processor type annotation from the disk.'
  )

  if support_access_mode:
    disks_flags.AddAccessModeFlag(parser, messages)

  parser.add_argument(
      '--provisioned-iops',
      type=arg_parsers.BoundedInt(),
      help=(
          'Provisioned IOPS of disk to update. '
          'Only for use with disks of type '
          'hyperdisk-extreme.'
      ),
  )

  parser.add_argument('--provisioned-throughput',
                      type=arg_parsers.BoundedInt(),
                      help=(
                          'Provisioned throughput of disk to update. '
                          'The throughput unit is  MB per sec. '))

  parser.add_argument(
      '--size',
      type=arg_parsers.BinarySize(
          suggested_binary_size_scales=['GB', 'GiB', 'TB', 'TiB', 'PiB', 'PB']),
      help="""\
        Size of the disks. The value must be a whole
        number followed by a size unit of ``GB'' for gigabyte, or ``TB''
        for terabyte. If no size unit is specified, GB is
        assumed. For details about disk size limits, refer to:
        https://cloud.google.com/compute/docs/disks
        """)


def _LabelsFlagsIncluded(args):
  return args.IsSpecified('update_labels') or args.IsSpecified(
      'clear_labels') or args.IsSpecified('remove_labels')


def _UserLicensesFlagsIncluded(args):
  return args.IsSpecified('update_user_licenses') or args.IsSpecified(
      'clear_user_licenses')


def _ArchitectureFlagsIncluded(args):
  return args.IsSpecified('update_architecture') or args.IsSpecified(
      'clear_architecture')


def _AccessModeFlagsIncluded(args, support_access_mode=False):
  return support_access_mode and args.IsSpecified('access_mode')


def _ProvisionedIopsIncluded(args):
  return args.IsSpecified('provisioned_iops')


def _ProvisionedThroughputIncluded(args):
  return args.IsSpecified('provisioned_throughput')


def _SizeIncluded(args):
  return args.IsSpecified('size')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update a Compute Engine persistent disk."""

  DISK_ARG = None

  @classmethod
  def Args(cls, parser):
    messages = cls._GetApiHolder(no_http=True).client.messages
    _CommonArgs(
        messages, cls, parser, False)

  @classmethod
  def _GetApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def Run(self, args):
    return self._Run(
        args,
        support_user_licenses=False)

  def _Run(self, args, support_user_licenses=False, support_access_mode=False):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    disk_ref = self.DISK_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetDefaultScopeLister(holder.client))
    disk_info = api_util.GetDiskInfo(disk_ref, client, messages)
    service = disk_info.GetService()

    if (
        _ProvisionedIopsIncluded(args)
        or _ProvisionedThroughputIncluded(args)
        or _ArchitectureFlagsIncluded(args)
        or _SizeIncluded(args)
        or (support_user_licenses and _UserLicensesFlagsIncluded(args))
        or _AccessModeFlagsIncluded(
            args, support_access_mode=support_access_mode
        )
    ):
      disk_res = messages.Disk(name=disk_ref.Name())
      disk_update_request = None
      if disk_ref.Collection() == 'compute.disks':
        disk_update_request = messages.ComputeDisksUpdateRequest(
            project=disk_ref.project,
            disk=disk_ref.Name(),
            diskResource=disk_res,
            zone=disk_ref.zone,
            paths=[])
      else:
        disk_update_request = messages.ComputeRegionDisksUpdateRequest(
            project=disk_ref.project,
            disk=disk_ref.Name(),
            diskResource=disk_res,
            region=disk_ref.region,
            paths=[])

      if support_user_licenses and _UserLicensesFlagsIncluded(args):
        if args.update_user_licenses:
          disk_res.userLicenses = args.update_user_licenses
        disk_update_request.paths.append('userLicenses')

      if _ArchitectureFlagsIncluded(args):
        if args.update_architecture:
          disk_res.architecture = disk_res.ArchitectureValueValuesEnum(
              args.update_architecture)
        disk_update_request.paths.append('architecture')

      if _AccessModeFlagsIncluded(
          args, support_access_mode=support_access_mode
      ):
        disk_res.accessMode = disk_res.AccessModeValueValuesEnum(
            args.access_mode
        )
        disk_update_request.paths.append('accessMode')

      if _ProvisionedIopsIncluded(args):
        if args.provisioned_iops:
          disk_res.provisionedIops = args.provisioned_iops
          disk_update_request.paths.append('provisionedIops')

      if _ProvisionedThroughputIncluded(
          args):
        if args.provisioned_throughput:
          disk_res.provisionedThroughput = args.provisioned_throughput
          disk_update_request.paths.append('provisionedThroughput')

      if _SizeIncluded(args) and args.size:
        disk_res.sizeGb = utils.BytesToGb(args.size)
        disk_update_request.paths.append('sizeGb')

      update_operation = service.Update(disk_update_request)
      update_operation_ref = holder.resources.Parse(
          update_operation.selfLink,
          collection=disk_info.GetOperationCollection())
      update_operation_poller = poller.Poller(service)
      result = waiter.WaitFor(
          update_operation_poller, update_operation_ref,
          'Updating fields of disk [{0}]'.format(disk_ref.Name()))
      if not _LabelsFlagsIncluded(args):
        return result

    labels_diff = labels_util.GetAndValidateOpsFromArgs(args)

    disk = disk_info.GetDiskResource()

    set_label_req = disk_info.GetSetLabelsRequestMessage()
    labels_update = labels_diff.Apply(set_label_req.LabelsValue, disk.labels)
    request = disk_info.GetSetDiskLabelsRequestMessage(
        disk, labels_update.GetOrNone())

    if not labels_update.needs_update:
      return disk

    operation = service.SetLabels(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection=disk_info.GetOperationCollection())

    operation_poller = poller.Poller(service)
    return waiter.WaitFor(
        operation_poller, operation_ref,
        'Updating labels of disk [{0}]'.format(
            disk_ref.Name()))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  r"""Update a Compute Engine persistent disk."""

  DISK_ARG = None

  @classmethod
  def Args(cls, parser):
    messages = cls._GetApiHolder(no_http=True).client.messages
    _CommonArgs(
        messages, cls, parser, support_user_licenses=True)

  @classmethod
  def _GetApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def Run(self, args):
    return self._Run(
        args,
        support_user_licenses=True)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  r"""Update a Compute Engine persistent disk."""

  DISK_ARG = None

  @classmethod
  def Args(cls, parser):
    messages = cls._GetApiHolder(no_http=True).client.messages
    _CommonArgs(
        messages,
        cls,
        parser,
        support_user_licenses=True,
        support_access_mode=True,
    )

  @classmethod
  def _GetApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def Run(self, args):
    return self._Run(args, support_user_licenses=True, support_access_mode=True)


Update.detailed_help = {
    'DESCRIPTION':
        '*{command}* updates a Compute Engine persistent disk.',
    'EXAMPLES':
        """\
        To update labels 'k0' and 'k1' and remove label 'k3' of a disk, run:

            $ {command} example-disk --zone=us-central1-a --update-labels=k0=value1,k1=value2 --remove-labels=k3

            ``k0'' and ``k1'' are added as new labels if not already present.

        Labels can be used to identify the disk. To list disks with the 'k1:value2' label, run:

            $ {parent_command} list --filter='labels.k1:value2'

        To list only the labels when describing a resource, use --format to filter the result:

            $ {parent_command} describe example-disk --format="default(labels)"
        """,
}
