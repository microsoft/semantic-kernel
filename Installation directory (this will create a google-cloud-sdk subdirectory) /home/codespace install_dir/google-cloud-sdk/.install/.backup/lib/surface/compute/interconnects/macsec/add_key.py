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
"""Command for updating the MACsec configuration of interconnect."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.interconnects import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """\
        *{command}* is used to add a pre-shared key to MACsec configuration of
        interconnect.

        For an example, refer to the *EXAMPLES* section below.
        """,
    # pylint: disable=line-too-long
    'EXAMPLES':
        """\
        To add a pre-shared key to MACsec configuration, run:

          $ {command} example-interconnect --key-name=default-key --start-time=2021-02-01T12:12:12Z
        """,
    # pylint: enable=line-too-long
}


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class AddKey(base.UpdateCommand):
  """Add pre-shared key to a Compute Engine interconnect MACsec configuration.

  *{command}* is used to add pre-shared key to MACsec configuration of
  interconnect.
  """

  INTERCONNECT_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.INTERCONNECT_ARG = flags.InterconnectArgument()
    cls.INTERCONNECT_ARG.AddArgument(parser, operation_type='update')

    flags.AddMacsecPreSharedKeyNameForAddOrUpdateKey(parser)
    flags.AddMacsecPreSharedKeyStartTimeForAddOrUpdateKey(parser)

  def Collection(self):
    return 'compute.interconnects'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.INTERCONNECT_ARG.ResolveAsResource(args, holder.resources)
    interconnect = client.Interconnect(ref, compute_client=holder.client)

    macsec = interconnect.Describe().macsec
    if macsec is None:
      macsec = holder.client.messages.InterconnectMacsec()

    if all(key.name != args.key_name for key in macsec.preSharedKeys):
      macsec.preSharedKeys.append(
          holder.client.messages.InterconnectMacsecPreSharedKey(
              name=args.key_name, startTime=args.start_time))

    return interconnect.Patch(
        description=None,
        interconnect_type=None,
        requested_link_count=None,
        link_type=None,
        admin_enabled=None,
        noc_contact_email=None,
        location=None,
        labels=None,
        label_fingerprint=None,
        macsec_enabled=None,
        macsec=macsec)


AddKey.detailed_help = DETAILED_HELP
