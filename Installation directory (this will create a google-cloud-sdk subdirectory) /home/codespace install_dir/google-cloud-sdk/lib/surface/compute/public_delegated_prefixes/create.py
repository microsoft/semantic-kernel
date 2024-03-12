# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Create public delegated prefix command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import public_delegated_prefixes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.public_delegated_prefixes import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Creates a Compute Engine public delegated prefix.

  ## EXAMPLES

  To create a public delegated prefix:

    $ {command} my-public-delegated-prefix --public-advertised-prefix=my-pap \
      --range=120.120.10.128/27 --global
  """
  support_ipv6_pdp = False

  @classmethod
  def Args(cls, parser):
    flags.MakePublicDelegatedPrefixesArg().AddArgument(parser)
    flags.AddCreatePdpArgsToParser(parser, cls.support_ipv6_pdp)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    pdp_client = public_delegated_prefixes.PublicDelegatedPrefixesClient(
        holder.client, holder.client.messages, holder.resources
    )
    pdp_ref = flags.MakePublicDelegatedPrefixesArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
    )

    if self.support_ipv6_pdp:
      if args.mode:
        input_mode = (
            holder.client.messages.PublicDelegatedPrefix.ModeValueValuesEnum(
                args.mode
            )
        )
      else:
        input_mode = None

      result = pdp_client.Create(
          pdp_ref,
          parent_pap_prefix=args.public_advertised_prefix
          if args.public_advertised_prefix
          else None,
          parent_pdp_prefix=args.public_delegated_prefix
          if args.public_delegated_prefix
          else None,
          ip_cidr_range=args.range,
          description=args.description,
          enable_live_migration=args.enable_live_migration,
          mode=input_mode,
          allocatable_prefix_length=int(args.allocatable_prefix_length)
          if args.allocatable_prefix_length
          else None,
      )
    else:
      result = pdp_client.Create(
          pdp_ref,
          parent_pap_prefix=args.public_advertised_prefix
          if args.public_advertised_prefix
          else None,
          parent_pdp_prefix=args.public_delegated_prefix
          if args.public_delegated_prefix
          else None,
          ip_cidr_range=args.range,
          description=args.description,
          enable_live_migration=args.enable_live_migration,
          mode=None,
          allocatable_prefix_length=None,
      )
    log.CreatedResource(pdp_ref.Name(), 'public delegated prefix')
    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  r"""Creates a Compute Engine public delegated prefix.

  ## EXAMPLES

  To create a public delegated prefix:

    $ {command} my-public-delegated-prefix --public-advertised-prefix=my-pap \
      --range=120.120.10.128/27 --global
  """
  support_ipv6_pdp = True
