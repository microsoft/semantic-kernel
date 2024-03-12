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
"""Update public delegated prefix command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import public_delegated_prefixes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.public_delegated_prefixes import flags


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Update(base.UpdateCommand):
  r"""Updates a Compute Engine public delegated prefix.

  ## EXAMPLES

  To announce a regional v2 public delegated prefix:

    $ {command} my-pdp --announce-prefix --region=us-central1

  To withdraw a regional v2 public delegated prefix:

    $ {command} my-pdp --withdraw-prefix --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.MakeRegionalPublicDelegatedPrefixesArg().AddArgument(parser)
    announce_withdraw_parser = parser.add_mutually_exclusive_group(
        required=True
    )
    flags.AddUpdatePrefixArgs(announce_withdraw_parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    pdp_client = public_delegated_prefixes.PublicDelegatedPrefixesClient(
        holder.client, holder.client.messages, holder.resources
    )

    pdp_ref = flags.MakeRegionalPublicDelegatedPrefixesArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
    )

    if args.announce_prefix:
      return pdp_client.Announce(pdp_ref)
    if args.withdraw_prefix:
      return pdp_client.Withdraw(pdp_ref)
