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
"""Command for updating a BGP peer on a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import routers_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.command_lib.compute.routers import router_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateBgpPeer(base.UpdateCommand):
  """Update a BGP peer on a Compute Engine router."""

  ROUTER_ARG = None

  @classmethod
  def _Args(cls, parser, enable_ipv6_bgp=False, enable_route_policies=False):
    cls.ROUTER_ARG = flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddBgpPeerArgs(
        parser,
        for_add_bgp_peer=False,
        is_update=True,
        enable_ipv6_bgp=enable_ipv6_bgp,
        enable_route_policies=enable_route_policies,
    )
    flags.AddUpdateCustomAdvertisementArgs(parser, 'peer')
    flags.AddUpdateCustomLearnedRoutesArgs(parser)

  @classmethod
  def Args(cls, parser):
    cls._Args(parser)

  def _Run(
      self,
      args,
      support_bfd_mode=False,
      enable_ipv6_bgp=False,
      enable_route_policies=False,
  ):
    """Runs the command.

    Args:
      args: contains arguments passed to the command.
      support_bfd_mode: The flag to indicate whether bfd mode is supported.
      enable_ipv6_bgp: The flag to indicate whether IPv6-based BGP is supported.
      enable_route_policies: The flag to indicate whether exportPolicies and
        importPolicies are supported.

    Returns:
      The result of patching the router updating the bgp peer with the
      information provided in the arguments.
    """
    # Manually ensure replace/incremental flags are mutually exclusive.
    router_utils.CheckIncompatibleFlagsOrRaise(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    service = holder.client.apitools_client.routers

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)

    request_type = messages.ComputeRoutersGetRequest
    replacement = service.Get(request_type(**router_ref.AsDict()))

    # Retrieve specified peer and update base fields.
    peer = router_utils.FindBgpPeerOrRaise(replacement, args.peer_name)

    md5_authentication_key_name = None
    cleared_fields = []
    if (
        args.clear_md5_authentication_key
        and peer.md5AuthenticationKeyName is not None
    ):
      replacement.md5AuthenticationKeys = [
          md5_authentication_key
          for md5_authentication_key in replacement.md5AuthenticationKeys
          if md5_authentication_key.name != peer.md5AuthenticationKeyName
      ]
      if not replacement.md5AuthenticationKeys:
        cleared_fields.append('md5AuthenticationKeys')
    elif args.md5_authentication_key is not None:
      if peer.md5AuthenticationKeyName is not None:
        md5_authentication_key_name = peer.md5AuthenticationKeyName
        for md5_authentication_key in replacement.md5AuthenticationKeys:
          if md5_authentication_key.name == md5_authentication_key_name:
            md5_authentication_key.key = args.md5_authentication_key
            break
      else:
        md5_authentication_key_name = (
            router_utils.GenerateMd5AuthenticationKeyName(replacement, args)
        )

        md5_authentication_key = messages.RouterMd5AuthenticationKey(
            name=md5_authentication_key_name, key=args.md5_authentication_key
        )
        replacement.md5AuthenticationKeys.append(md5_authentication_key)

    _UpdateBgpPeerMessage(
        peer,
        messages,
        args,
        md5_authentication_key_name=md5_authentication_key_name,
        support_bfd_mode=support_bfd_mode,
        enable_ipv6_bgp=enable_ipv6_bgp,
        enable_route_policies=enable_route_policies,
    )

    if router_utils.HasReplaceAdvertisementFlags(args):
      mode, groups, ranges = router_utils.ParseAdvertisements(
          messages=messages, resource_class=messages.RouterBgpPeer, args=args
      )

      router_utils.PromptIfSwitchToDefaultMode(
          messages=messages,
          resource_class=messages.RouterBgpPeer,
          existing_mode=peer.advertiseMode,
          new_mode=mode,
      )

      attrs = {
          'advertiseMode': mode,
          'advertisedGroups': groups,
          'advertisedIpRanges': ranges,
      }

      for attr, value in attrs.items():
        if value is not None:
          setattr(peer, attr, value)

    if router_utils.HasIncrementalAdvertisementFlags(args):
      # This operation should only be run on custom mode peers.
      router_utils.ValidateCustomMode(
          messages=messages,
          resource_class=messages.RouterBgpPeer,
          resource=peer,
      )

      # These arguments are guaranteed to be mutually exclusive in args.
      if args.add_advertisement_groups:
        groups_to_add = routers_utils.ParseGroups(
            resource_class=messages.RouterBgpPeer,
            groups=args.add_advertisement_groups,
        )
        peer.advertisedGroups.extend(groups_to_add)

      if args.remove_advertisement_groups:
        groups_to_remove = routers_utils.ParseGroups(
            resource_class=messages.RouterBgpPeer,
            groups=args.remove_advertisement_groups,
        )
        router_utils.RemoveGroupsFromAdvertisements(
            messages=messages,
            resource_class=messages.RouterBgpPeer,
            resource=peer,
            groups=groups_to_remove,
        )

      if args.add_advertisement_ranges:
        ip_ranges_to_add = routers_utils.ParseIpRanges(
            messages=messages, ip_ranges=args.add_advertisement_ranges
        )
        peer.advertisedIpRanges.extend(ip_ranges_to_add)

      if args.remove_advertisement_ranges:
        router_utils.RemoveIpRangesFromAdvertisements(
            messages=messages,
            resource_class=messages.RouterBgpPeer,
            resource=peer,
            ip_ranges=args.remove_advertisement_ranges,
        )

    if args.set_custom_learned_route_ranges is not None:
      peer.customLearnedIpRanges = routers_utils.ParseCustomLearnedIpRanges(
          messages=messages, ip_ranges=args.set_custom_learned_route_ranges
      )

    # These arguments are guaranteed to be mutually exclusive in args.
    if args.add_custom_learned_route_ranges:
      ip_ranges_to_add = routers_utils.ParseCustomLearnedIpRanges(
          messages=messages, ip_ranges=args.add_custom_learned_route_ranges
      )
      peer.customLearnedIpRanges.extend(ip_ranges_to_add)

    if args.remove_custom_learned_route_ranges:
      router_utils.RemoveIpRangesFromCustomLearnedRoutes(
          messages=messages,
          peer=peer,
          ip_ranges=args.remove_custom_learned_route_ranges,
      )

    request_type = messages.ComputeRoutersPatchRequest
    with holder.client.apitools_client.IncludeFields(cleared_fields):
      result = service.Patch(
          request_type(
              project=router_ref.project,
              region=router_ref.region,
              router=router_ref.Name(),
              routerResource=replacement,
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
      log.UpdatedResource(
          operation_ref,
          kind='peer [{0}] in router [{1}]'.format(
              peer.name, router_ref.Name()
          ),
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
        'Updating peer [{0}] in router [{1}]'.format(
            peer.name, router_ref.Name()
        ),
    )

  def Run(self, args):
    """See base.UpdateCommand."""
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBgpPeerBeta(UpdateBgpPeer):
  """Update a BGP peer on a Compute Engine router."""

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls._Args(parser, enable_ipv6_bgp=True)

  def Run(self, args):
    """Runs the command.

    Args:
      args: contains arguments passed to the command.

    Returns:
      The result of patching the router updating the bgp peer with the
      information provided in the arguments.
    """
    return self._Run(args, support_bfd_mode=False, enable_ipv6_bgp=True)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateBgpPeerAlpha(UpdateBgpPeerBeta):
  """Update a BGP peer on a Compute Engine router."""

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls._Args(parser, enable_ipv6_bgp=True, enable_route_policies=True)

  def Run(self, args):
    """Runs the command.

    Args:
      args: contains arguments passed to the command.

    Returns:
      The result of patching the router updating the bgp peer with the
      information provided in the arguments.
    """
    return self._Run(
        args,
        support_bfd_mode=True,
        enable_ipv6_bgp=True,
        enable_route_policies=True,
    )


def _UpdateBgpPeerMessage(
    peer,
    messages,
    args,
    md5_authentication_key_name,
    support_bfd_mode=False,
    enable_ipv6_bgp=False,
    enable_route_policies=False,
):
  """Updates base attributes of a BGP peer based on flag arguments."""

  attrs = {
      'interfaceName': args.interface,
      'ipAddress': args.ip_address,
      'peerIpAddress': args.peer_ip_address,
      'peerAsn': args.peer_asn,
      'advertisedRoutePriority': args.advertised_route_priority,
  }

  if args.enabled is not None:
    if args.enabled:
      attrs['enable'] = messages.RouterBgpPeer.EnableValueValuesEnum.TRUE
    else:
      attrs['enable'] = messages.RouterBgpPeer.EnableValueValuesEnum.FALSE
  if args.enable_ipv6 is not None:
    attrs['enableIpv6'] = args.enable_ipv6
  if args.ipv6_nexthop_address is not None:
    attrs['ipv6NexthopAddress'] = args.ipv6_nexthop_address
  if args.peer_ipv6_nexthop_address is not None:
    attrs['peerIpv6NexthopAddress'] = args.peer_ipv6_nexthop_address
  if enable_ipv6_bgp and args.enable_ipv4 is not None:
    attrs['enableIpv4'] = args.enable_ipv4
  if enable_ipv6_bgp and args.ipv4_nexthop_address is not None:
    attrs['ipv4NexthopAddress'] = args.ipv4_nexthop_address
  if enable_ipv6_bgp and args.peer_ipv4_nexthop_address is not None:
    attrs['peerIpv4NexthopAddress'] = args.peer_ipv4_nexthop_address
  if args.custom_learned_route_priority is not None:
    attrs['customLearnedRoutePriority'] = args.custom_learned_route_priority
  if args.md5_authentication_key is not None:
    attrs['md5AuthenticationKeyName'] = md5_authentication_key_name
  if enable_route_policies:
    attrs['exportPolicies'] = args.export_policies
    attrs['importPolicies'] = args.import_policies
  for attr, value in attrs.items():
    if value is not None:
      setattr(peer, attr, value)
  if args.clear_md5_authentication_key:
    peer.md5AuthenticationKeyName = None
  if support_bfd_mode:
    bfd = _UpdateBgpPeerBfdMessageMode(messages, peer, args)
  else:
    bfd = _UpdateBgpPeerBfdMessage(messages, peer, args)
  if bfd is not None:
    setattr(peer, 'bfd', bfd)


def _UpdateBgpPeerBfdMessage(messages, peer, args):
  """Updates BGP peer BFD messages based on flag arguments."""
  if not (
      args.IsSpecified('bfd_min_receive_interval')
      or args.IsSpecified('bfd_min_transmit_interval')
      or args.IsSpecified('bfd_session_initialization_mode')
      or args.IsSpecified('bfd_multiplier')
  ):
    return None
  if peer.bfd is not None:
    bfd = peer.bfd
  else:
    bfd = messages.RouterBgpPeerBfd()
  attrs = {}
  if args.bfd_session_initialization_mode is not None:
    attrs['sessionInitializationMode'] = (
        messages.RouterBgpPeerBfd.SessionInitializationModeValueValuesEnum(
            args.bfd_session_initialization_mode
        )
    )
  attrs['minReceiveInterval'] = args.bfd_min_receive_interval
  attrs['minTransmitInterval'] = args.bfd_min_transmit_interval
  attrs['multiplier'] = args.bfd_multiplier
  for attr, value in attrs.items():
    if value is not None:
      setattr(bfd, attr, value)
  return bfd


def _UpdateBgpPeerBfdMessageMode(messages, peer, args):
  """Updates BGP peer BFD messages based on flag arguments."""
  if not (
      args.IsSpecified('bfd_min_receive_interval')
      or args.IsSpecified('bfd_min_transmit_interval')
      or args.IsSpecified('bfd_session_initialization_mode')
      or args.IsSpecified('bfd_multiplier')
  ):
    return None
  if peer.bfd is not None:
    bfd = peer.bfd
  else:
    bfd = messages.RouterBgpPeerBfd()
  attrs = {}
  if args.bfd_session_initialization_mode is not None:
    attrs['mode'] = messages.RouterBgpPeerBfd.ModeValueValuesEnum(
        args.bfd_session_initialization_mode
    )
    attrs['sessionInitializationMode'] = (
        messages.RouterBgpPeerBfd.SessionInitializationModeValueValuesEnum(
            args.bfd_session_initialization_mode
        )
    )
  attrs['minReceiveInterval'] = args.bfd_min_receive_interval
  attrs['minTransmitInterval'] = args.bfd_min_transmit_interval
  attrs['multiplier'] = args.bfd_multiplier
  for attr, value in attrs.items():
    if value is not None:
      setattr(bfd, attr, value)
  return bfd


UpdateBgpPeer.detailed_help = {
    'DESCRIPTION': """
        *{command}* is used to update a BGP peer on a Compute Engine
        router.
        """,
}
