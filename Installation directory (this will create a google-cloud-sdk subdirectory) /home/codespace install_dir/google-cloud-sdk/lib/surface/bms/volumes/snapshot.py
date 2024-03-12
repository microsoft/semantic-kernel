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
"""'Bare Metal Solution boot volumes "snapshot" command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a snapshot of a Bare Metal Solution boot volume.
        """,
    'EXAMPLES':
        """
          To create a snapshot of a boot volume named ``my-boot-volume'' in
          region ``us-central1'' with the name ``my-snapshot'' and description
          ``my-description'', run:

          $ {command} my-boot-volume --region=us-central1 --snapshot-name=my-snapshot
          --description=my-description
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a snapshot of a Bare Metal Solution boot volume."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddVolumeArgToParser(parser, positional=True)
    parser.add_argument('--snapshot-name',
                        help='Name to assign to the created snapshot.',
                        required=True)
    parser.add_argument('--description',
                        help='Textual description of the created snapshot.',
                        required=True)

  def Run(self, args):
    volume = args.CONCEPTS.volume.Parse()
    client = BmsClient()
    snapshot_ref = resources.REGISTRY.Parse(
        args.snapshot_name,
        params={
            'projectsId': properties.VALUES.core.project.GetOrFail,
            'locationsId': args.region,
            'volumesId': args.volume,
        },
        collection='baremetalsolution.projects.locations.volumes.snapshots',
        api_version='v2')

    res = client.CreateVolumeSnapshot(resource=volume,
                                      name=snapshot_ref.RelativeName(),
                                      description=args.description)
    log.CreatedResource(res.name, 'snapshot')
    return res


Create.detailed_help = DETAILED_HELP
