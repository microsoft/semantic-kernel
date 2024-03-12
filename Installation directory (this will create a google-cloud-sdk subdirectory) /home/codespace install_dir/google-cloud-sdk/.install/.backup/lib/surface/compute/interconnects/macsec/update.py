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
        *{command}* is used to update MACsec configuration of interconnect. An
        interconnect represents a single specific connection between Google and
        the customer.

        For an example, refer to the *EXAMPLES* section below.
        """,
    # pylint: disable=line-too-long
    'EXAMPLES':
        """\
        To enable MACsec on an interconnect, run:

          $ {command} example-interconnect --enabled
        """,
    # pylint: enable=line-too-long
}


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Update(base.UpdateCommand):
  """Update a Compute Engine interconnect MACsec configuration.

  *{command}* is used to update MACsec configuration of interconnect. An
  interconnect represents a single specific connection between Google and the
  customer.
  """

  INTERCONNECT_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.INTERCONNECT_ARG = flags.InterconnectArgument()
    cls.INTERCONNECT_ARG.AddArgument(parser, operation_type='update')

    flags.AddMacsecEnabledForUpdate(parser)
    flags.AddFailOpenForUpdate(parser)

  def Collection(self):
    return 'compute.interconnects'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.INTERCONNECT_ARG.ResolveAsResource(args, holder.resources)
    interconnect = client.Interconnect(ref, compute_client=holder.client)

    macsec = None
    if args.fail_open is not None:
      macsec = interconnect.Describe().macsec
      macsec.failOpen = args.fail_open

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
        macsec_enabled=args.enabled,
        macsec=macsec)


Update.detailed_help = DETAILED_HELP
