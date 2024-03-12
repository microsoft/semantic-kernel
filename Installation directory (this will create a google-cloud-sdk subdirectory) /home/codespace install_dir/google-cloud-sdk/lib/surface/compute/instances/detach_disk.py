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
"""Command for detaching a disk from an instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import scope as compute_scopes
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class DetachDisk(base.UpdateCommand):
  """Detach disks from Compute Engine virtual machine instances.

  *{command}* is used to detach disks from virtual machines.

  Detaching a disk without first unmounting it may result in
  incomplete I/O operations and data corruption.
  To unmount a persistent disk on a Linux-based image,
  ssh into the instance and run:

      $ sudo umount /dev/disk/by-id/google-DEVICE_NAME
  """

  detailed_help = {
      'EXAMPLES': """
          To detach a disk named 'my-disk' to an instance named 'my-instance',
          run:

            $ {command} my-instance --disk=my-disk

          To detach a device named 'my-device' from an instance named
          'my-instance', run:

            $ {command} my-instance --device-name=my-device
          """,
  }

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)
    disk_group = parser.add_mutually_exclusive_group(required=True)

    disk_group.add_argument(
        '--disk',
        help="""\
        Specifies a disk to detach by its resource name. If you specify a
        disk to remove by persistent disk name, then you must not specify its
        device name using the ``--device-name'' flag.
        """)

    disk_group.add_argument(
        '--device-name',
        help="""\
        Specifies a disk to detach by its device name, which is the name
        that the guest operating system sees. The device name is set
        at the time that the disk is attached to the instance, and needs not be
        the same as the persistent disk name. If the disk's device name is
        specified, then its persistent disk name must not be specified
        using the ``--disk'' flag.
        """)
    flags.AddDiskScopeFlag(parser)

  def CreateReference(self, client, resources, args):
    return flags.INSTANCE_ARG.ResolveAsResource(
        args, resources, scope_lister=flags.GetInstanceZoneScopeLister(client))

  def GetGetRequest(self, client, instance_ref):
    return (client.apitools_client.instances,
            'Get',
            client.messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))

  def GetSetRequest(self, client, instance_ref, replacement, existing):
    removed_disk = list(
        set(disk.deviceName for disk in existing.disks) -
        set(disk.deviceName for disk in replacement.disks))[0]

    return (client.apitools_client.instances,
            'DetachDisk',
            client.messages.ComputeInstancesDetachDiskRequest(
                deviceName=removed_disk,
                **instance_ref.AsDict()))

  def Modify(self, resources, args, instance_ref, existing):
    replacement = encoding.CopyProtoMessage(existing)

    if args.disk:
      disk_ref = self.ParseDiskRef(resources, args, instance_ref)

      replacement.disks = [
          disk for disk in existing.disks
          if not disk.source or resources.ParseURL(disk.source).RelativeName()
          != disk_ref.RelativeName()
      ]

      if len(existing.disks) == len(replacement.disks):
        raise compute_exceptions.ArgumentError(
            'Disk [{0}] is not attached to instance [{1}] in zone [{2}].'
            .format(disk_ref.Name(), instance_ref.instance, instance_ref.zone))

    else:
      replacement.disks = [disk for disk in existing.disks
                           if disk.deviceName != args.device_name]

      if len(existing.disks) == len(replacement.disks):
        raise compute_exceptions.ArgumentError(
            'No disk with device name [{0}] is attached to instance [{1}] in '
            'zone [{2}].'
            .format(args.device_name, instance_ref.instance, instance_ref.zone))

    return replacement

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = self.CreateReference(client, holder.resources, args)
    get_request = self.GetGetRequest(client, instance_ref)

    objects = client.MakeRequests([get_request])

    new_object = self.Modify(holder.resources, args, instance_ref, objects[0])

    # If existing object is equal to the proposed object or if
    # Modify() returns None, then there is no work to be done, so we
    # print the resource and return.
    if objects[0] == new_object:
      log.status.Print(
          'No change requested; skipping update for [{0}].'.format(
              objects[0].name))
      return objects

    return client.MakeRequests(
        [self.GetSetRequest(client, instance_ref, new_object, objects[0])])

  def ParseDiskRef(self, resources, args, instance_ref):
    if args.disk_scope == 'regional':
      scope = compute_scopes.ScopeEnum.REGION
    else:
      scope = compute_scopes.ScopeEnum.ZONE
    return instance_utils.ParseDiskResource(resources, args.disk,
                                            instance_ref.project,
                                            instance_ref.zone,
                                            scope)
