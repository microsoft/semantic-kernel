# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Command for moving disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class Move(base.SilentCommand):
  """Move a disk between zones."""

  @staticmethod
  def Args(parser):
    Move.disk_arg = disks_flags.MakeDiskArgZonal(plural=False)
    Move.disk_arg.AddArgument(parser)

    parser.add_argument(
        '--destination-zone',
        help='The zone to move the disk to.',
        completer=completers.ZonesCompleter,
        required=True)

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Returns a request for moving a disk."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    target_disk = Move.disk_arg.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetDefaultScopeLister(holder.client))
    destination_zone = holder.resources.Parse(
        args.destination_zone,
        params={
            'project': properties.VALUES.core.project.GetOrFail,
        },
        collection='compute.zones')

    client = holder.client.apitools_client
    messages = holder.client.messages

    request = messages.ComputeProjectsMoveDiskRequest(
        diskMoveRequest=messages.DiskMoveRequest(
            destinationZone=destination_zone.SelfLink(),
            targetDisk=target_disk.SelfLink(),
        ),
        project=target_disk.project,
    )

    result = client.projects.MoveDisk(request)
    operation_ref = resources.REGISTRY.Parse(
        result.name,
        params={
            'project': properties.VALUES.core.project.GetOrFail,
        },
        collection='compute.globalOperations')

    if args.async_:
      log.UpdatedResource(
          operation_ref,
          kind='disk {0}'.format(target_disk.Name()),
          is_async=True,
          details='Run the [gcloud compute operations describe] command '
                  'to check the status of this operation.'
      )
      return result

    destination_disk_ref = holder.resources.Parse(
        target_disk.Name(),
        params={
            'project': destination_zone.project,
            'zone': destination_zone.Name()
        },
        collection='compute.disks')

    operation_poller = poller.Poller(client.disks, destination_disk_ref)

    return waiter.WaitFor(
        operation_poller, operation_ref,
        'Moving disk {0}'.format(target_disk.Name()))


Move.detailed_help = {
    'brief': 'Move a disk between zones',
    'DESCRIPTION': (
        '*{command}* facilitates moving a Compute Engine disk volume '
        'from one zone to another. You cannot move a disk if it is attached to '
        'a running or stopped instance; use the gcloud compute instances move '
        'command instead.\n\n'
        'The `gcloud compute disks move` command does not support regional '
        'persistent disks. See '
        'https://cloud.google.com/compute/docs/disks/regional-persistent-disk '
        'for more details.\n'),
    'EXAMPLES': (
        'To move the disk called example-disk-1 from us-central1-b to '
        'us-central1-f, run:\n\n'
        '  $ {command} example-disk-1 --zone=us-central1-b '
        '--destination-zone=us-central1-f\n')
}
