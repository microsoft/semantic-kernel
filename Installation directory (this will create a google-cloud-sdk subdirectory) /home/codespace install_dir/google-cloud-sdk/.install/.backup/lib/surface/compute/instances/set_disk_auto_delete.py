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

"""Command for setting whether to auto-delete a disk."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import scope as compute_scopes
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources as cloud_resources
from googlecloudsdk.core.console import console_io


class SetDiskAutoDelete(base.UpdateCommand):
  """Set auto-delete behavior for disks.

    *${command}* is used to configure the auto-delete behavior for disks
  attached to Compute Engine virtual machines. When
  auto-delete is on, the persistent disk is deleted when the
  instance it is attached to is deleted.
  """

  detailed_help = {
      'EXAMPLES': """
          To enable auto-delete for a disk named 'my-disk' on an instance
          named 'my-instance', run:

            $ {command} my-instance --auto-delete --disk=my-disk

          To enable auto-delete for a device named 'my-device' on an instance
          named 'my-instance', run:

            $ {command} my-instance --auto-delete --device-name=my-device
          """,
  }

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)

    parser.add_argument(
        '--auto-delete',
        action='store_true',
        default=True,
        help='Enables auto-delete for the given disk.')

    disk_group = parser.add_mutually_exclusive_group(required=True)

    disk_group.add_argument(
        '--disk',
        help="""\
        Specifies a disk to set auto-delete for by its resource name. If
        you specify a disk to set auto-delete for by persistent disk name,
        then you must not specify its device name using the
        ``--device-name'' flag.
        """)

    disk_group.add_argument(
        '--device-name',
        help="""\
        Specifies a disk to set auto-delete for by its device name,
        which is the name that the guest operating system sees. The
        device name is set at the time that the disk is attached to the
        instance, and need not be the same as the persistent disk name.
        If the disk's device name is specified, then its persistent disk
        name must not be specified using the ``--disk'' flag.
        """)

  def CreateReference(self, client, resources, args):
    return flags.INSTANCE_ARG.ResolveAsResource(
        args, resources, scope_lister=flags.GetInstanceZoneScopeLister(client))

  def GetGetRequest(self, client, instance_ref):
    return (client.apitools_client.instances,
            'Get',
            client.messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))

  def GetSetRequest(self, client, instance_ref, attached_disk):
    return (client.apitools_client.instances,
            'SetDiskAutoDelete',
            client.messages.ComputeInstancesSetDiskAutoDeleteRequest(
                deviceName=attached_disk.deviceName,
                instance=instance_ref.instance,
                project=instance_ref.project,
                zone=instance_ref.zone,
                autoDelete=attached_disk.autoDelete))

  def _GetPossibleDisks(self, resources, name, instance_ref):
    """Gets the possible disks that match the provided disk name.

    First, we attempt to parse the provided disk name as a regional and as a
    zonal disk. Next, we iterate over the attached disks to find the ones that
    match the parsed regional and zonal disks.

    If the disk can match either a zonal or regional disk, we prompt the user to
    choose one.

    Args:
      resources: resources.Registry, The resource registry
      name: str, name of the disk.
      instance_ref: Reference of the instance instance.

    Returns:
      List of possible disks references that possibly match the provided disk
          name.
    """
    possible_disks = []
    try:
      regional_disk = instance_utils.ParseDiskResource(
          resources, name, instance_ref.project, instance_ref.zone,
          compute_scopes.ScopeEnum.REGION)
      possible_disks.append(regional_disk)
    except cloud_resources.WrongResourceCollectionException:
      pass
    try:
      zonal_disk = instance_utils.ParseDiskResource(
          resources, name, instance_ref.project, instance_ref.zone,
          compute_scopes.ScopeEnum.ZONE)
      possible_disks.append(zonal_disk)
    except cloud_resources.WrongResourceCollectionException:
      pass

    return possible_disks

  def GetAttachedDiskByName(self, resources, name, instance_ref, instance):
    """Gets an attached disk with the specified disk name.

    First, we attempt to parse the provided disk name to find the possible disks
    that it may describe. Next, we iterate over the attached disks to find the
    ones that match the possible disks.

    If the disk can match multiple disks, we prompt the user to choose one.

    Args:
      resources: resources.Registry, The resource registry
      name: str, name of the attached disk.
      instance_ref: Reference of the instance instance.
      instance: Instance object.

    Returns:
      An attached disk object.

    Raises:
      exceptions.ArgumentError: If a disk with name cannot be found attached to
          the instance or if the user does not choose a specific disk when
          prompted.
    """
    possible_disks = self._GetPossibleDisks(resources, name, instance_ref)

    matched_attached_disks = []
    for attached_disk in instance.disks:
      parsed_disk = instance_utils.ParseDiskResourceFromAttachedDisk(
          resources, attached_disk)
      for d in possible_disks:
        if d and d.RelativeName() == parsed_disk.RelativeName():
          matched_attached_disks.append(attached_disk)

    if not matched_attached_disks:
      raise compute_exceptions.ArgumentError(
          'Disk [{}] is not attached to instance [{}] in zone [{}].'
          .format(name, instance_ref.instance, instance_ref.zone))
    elif len(matched_attached_disks) == 1:
      return matched_attached_disks[0]

    choice_names = []
    for attached_disk in matched_attached_disks:
      disk_ref = instance_utils.ParseDiskResourceFromAttachedDisk(
          resources, attached_disk)
      choice_names.append(disk_ref.RelativeName())
    idx = console_io.PromptChoice(
        options=choice_names,
        message='[{}] matched multiple disks. Choose one:'.format(name))
    if idx is None:
      raise compute_exceptions.ArgumentError(
          'Found multiple disks matching [{}] attached to instance [{}] '
          'in zone [{}].'
          .format(name, instance_ref.instance, instance_ref.zone))
    return matched_attached_disks[idx]

  def GetAttachedDiskByDeviceName(self, resources, device_name, instance_ref,
                                  instance):
    """Gets an attached disk with the specified device name.

    Args:
      resources: resources.Registry, The resource registry
      device_name: str, device name of the attached disk.
      instance_ref: Reference of the instance instance.
      instance: Instance object.

    Returns:
      An attached disk object.

    Raises:
      compute_exceptions.ArgumentError: If a disk with device name cannot be
          found attached to the instance.
    """
    for disk in instance.disks:
      if disk.deviceName == device_name:
        return disk

    raise compute_exceptions.ArgumentError(
        'No disk with device name [{}] is attached to instance [{}] '
        'in zone [{}].'
        .format(device_name, instance_ref.instance, instance_ref.zone))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = self.CreateReference(client, holder.resources, args)
    get_request = self.GetGetRequest(client, instance_ref)

    objects = client.MakeRequests([get_request])
    if args.disk:
      disk = self.GetAttachedDiskByName(holder.resources, args.disk,
                                        instance_ref, objects[0])
    else:
      disk = self.GetAttachedDiskByDeviceName(holder.resources,
                                              args.device_name, instance_ref,
                                              objects[0])

    if disk.autoDelete == args.auto_delete:
      log.status.Print(
          'No change requested; skipping update for [{}].'.format(
              objects[0].name))
      return objects

    disk.autoDelete = args.auto_delete
    return client.MakeRequests(
        [self.GetSetRequest(client, instance_ref, disk)])
