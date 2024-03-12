# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""'Bare Metal Solution boot volumes "restore" command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


DETAILED_HELP = {
    'DESCRIPTION':
        """
          Restore a Bare Metal Solution boot volume from an existing snapshot.
        """,
    'EXAMPLES':
        """
          To restore a boot volume named ``my-boot-volume'' in region
          ``us-central1'' from snapshot named ``my-snapshot'', run:

          $ {command} my-boot-volume --region=us-central1 --snapshot=my-snapshot
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Restore(base.UpdateCommand):
  """Restore a Bare Metal Solution boot volume from an existing snapshot."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddVolumeArgToParser(parser, positional=True)
    parser.add_argument('--snapshot',
                        required=True,
                        help='Name of the snapshot to restore.')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    volume = args.CONCEPTS.volume.Parse()
    client = BmsClient()
    snapshot_ref = resources.REGISTRY.Parse(
        args.snapshot,
        params={
            'projectsId': properties.VALUES.core.project.GetOrFail,
            'locationsId': args.region,
            'volumesId': args.volume,
        },
        collection='baremetalsolution.projects.locations.volumes.snapshots',
        api_version='v2')
    op_ref = client.RestoreVolumeSnapshot(
        snapshot_name=snapshot_ref.RelativeName())

    if op_ref.done:
      log.RestoredResource(volume.Name(), kind='volume')
      return op_ref

    if args.async_:
      log.status.Print('Restore request issued for [{}]\nCheck operation '
                       '[{}] for status.'.format(volume.Name(), op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='baremetalsolution.projects.locations.operations',
        api_version='v2')
    poller = waiter.CloudOperationPollerNoResources(
        client.operation_service)
    res = waiter.WaitFor(poller, op_resource,
                         'Waiting for operation [{}] to complete'.format(
                             op_ref.name))
    log.RestoredResource(volume.Name(), kind='volume')
    return res


Restore.detailed_help = DETAILED_HELP
