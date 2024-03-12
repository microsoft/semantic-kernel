# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command for moving addresses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.addresses import flags


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Move(base.SilentCommand):
  """Move an address to another project.

  ## EXAMPLES

  The following command moves address `external-ip1` in region `us-central1` to
  project `test-playground` with new address name `test-ip1`:

     $ {command} external-ip1 --new-name=test-ip1
     --target-project=test-playground --region=us-central1
  """

  ADDRESS_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ADDRESS_ARG = flags.AddressArgument(plural=False)
    cls.ADDRESS_ARG.AddArgument(parser)
    flags.AddMoveArguments(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    address_ref = self.ADDRESS_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))
    new_name = args.new_name if args.new_name is not None else address_ref.Name(
    )

    messages = holder.client.messages
    if address_ref.Collection() == 'compute.globalAddresses':
      address_url = 'projects/{}/global/addresses/{}'.format(
          args.target_project, new_name)
      request_msg = messages.ComputeGlobalAddressesMoveRequest(
          address=address_ref.Name(),
          project=address_ref.project,
          globalAddressesMoveRequest=messages.GlobalAddressesMoveRequest(
              description=args.description,
              destinationAddress=address_url,
          ),
      )
      request = (holder.client.apitools_client.globalAddresses, 'Move',
                 request_msg)
    else:
      address_url = 'projects/{}/regions/{}/addresses/{}'.format(
          args.target_project, address_ref.region, new_name)
      request_msg = messages.ComputeAddressesMoveRequest(
          region=address_ref.region,
          address=address_ref.Name(),
          project=address_ref.project,
          regionAddressesMoveRequest=messages.RegionAddressesMoveRequest(
              description=args.description,
              destinationAddress=address_url,
          ),
      )
      request = (holder.client.apitools_client.addresses, 'Move', request_msg)
    return holder.client.MakeRequests([request],
                                      project_override=args.target_project)
