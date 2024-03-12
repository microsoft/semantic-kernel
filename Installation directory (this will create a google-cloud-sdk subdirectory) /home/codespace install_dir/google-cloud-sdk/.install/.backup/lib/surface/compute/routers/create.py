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
"""Command for creating Compute Engine routers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.networks import flags as network_flags
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.command_lib.compute.routers import router_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
import six


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Compute Engine router.

  *{command}* is used to create a router to provide dynamic routing to VPN
  tunnels and interconnects.
  """

  ROUTER_ARG = None

  @classmethod
  def _Args(cls, parser, enable_ipv6_bgp=False):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.NETWORK_ARG = network_flags.NetworkArgumentForOtherResource(
        'The network for this router'
    )
    cls.NETWORK_ARG.AddArgument(parser)
    cls.ROUTER_ARG = flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser, operation_type='create')
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddCreateRouterArgs(parser)
    flags.AddKeepaliveIntervalArg(parser)
    if enable_ipv6_bgp:
      flags.AddBgpIdentifierRangeArg(parser)
    flags.AddEncryptedInterconnectRouter(parser)
    flags.AddReplaceCustomAdvertisementArgs(parser, 'router')
    parser.display_info.AddCacheUpdater(flags.RoutersCompleter)

  @classmethod
  def Args(cls, parser):
    """See base.CreateCommand."""
    cls._Args(parser)

  def _Run(self, args, enable_ipv6_bgp=False):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    service = holder.client.apitools_client.routers

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)
    network_ref = self.NETWORK_ARG.ResolveAsResource(args, holder.resources)

    router_resource = messages.Router(
        name=router_ref.Name(),
        description=args.description,
        network=network_ref.SelfLink(),
    )

    # Add bgp field with the assigned asn and/or keepalive_interval
    if args.asn is not None or args.keepalive_interval is not None:
      router_resource.bgp = messages.RouterBgp(
          asn=args.asn, keepaliveInterval=args.keepalive_interval
      )

    if args.IsSpecified('encrypted_interconnect_router'):
      router_resource.encryptedInterconnectRouter = (
          args.encrypted_interconnect_router
      )
    if router_utils.HasReplaceAdvertisementFlags(args):
      mode, groups, ranges = router_utils.ParseAdvertisements(
          messages=messages, resource_class=messages.RouterBgp, args=args
      )

      attrs = {
          'advertiseMode': mode,
          'advertisedGroups': groups,
          'advertisedIpRanges': ranges,
      }
      # Create an empty bgp field if not generated yet.
      if args.asn is None:
        router_resource.bgp = messages.RouterBgp()
      for attr, value in six.iteritems(attrs):
        if value is not None:
          setattr(router_resource.bgp, attr, value)

    if enable_ipv6_bgp and args.bgp_identifier_range is not None:
      if not hasattr(router_resource.bgp, 'identifierRange'):
        router_resource.bgp = messages.RouterBgp()
      router_resource.bgp.identifierRange = args.bgp_identifier_range

    result = service.Insert(
        messages.ComputeRoutersInsertRequest(
            router=router_resource,
            region=router_ref.region,
            project=router_ref.project,
        )
    )

    operation_ref = resources.REGISTRY.Parse(
        result.name,
        collection='compute.regionOperations',
        params={
            'project': router_ref.project,
            'region': router_ref.region,
        },
    )

    if args.async_:
      # Override the networks list format with the default operations format
      if not args.IsSpecified('format'):
        args.format = 'none'
      log.CreatedResource(
          operation_ref,
          kind='router [{0}]'.format(router_ref.Name()),
          is_async=True,
          details=(
              'Run the [gcloud compute operations describe] command '
              'to check the status of this operation.'
          ),
      )
      return result

    target_router_ref = holder.resources.Parse(
        router_ref.Name(),
        collection='compute.routers',
        params={
            'project': router_ref.project,
            'region': router_ref.region,
        },
    )

    operation_poller = poller.Poller(service, target_router_ref)
    return waiter.WaitFor(
        operation_poller,
        operation_ref,
        'Creating router [{0}]'.format(router_ref.Name()),
    )

  def Run(self, args):
    """See base.UpdateCommand."""
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Compute Engine router.

  *{command}* is used to create a router to provide dynamic routing to VPN
  tunnels and interconnects.
  """

  @classmethod
  def Args(cls, parser):
    """See base.CreateCommand."""
    cls._Args(parser, enable_ipv6_bgp=True)

  def Run(self, args):
    """See base.UpdateCommand."""
    return self._Run(args, enable_ipv6_bgp=True)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a Compute Engine router.

  *{command}* is used to create a router to provide dynamic routing to VPN
  tunnels and interconnects.
  """
