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
"""Command for removing a BGP peer from a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.core import exceptions


class PeerNotFoundError(exceptions.Error):
  """Raised when a peer is not found."""

  def __init__(self, name_list):
    error_msg = ('peer ' + ', '.join(
        ['%s'] * len(name_list))) % tuple(name_list) + ' not found'
    super(PeerNotFoundError, self).__init__(error_msg)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class RemoveBgpPeer(base.UpdateCommand):
  """Remove a BGP peer from a Compute Engine router.

  *{command}* removes a BGP peer from a Compute Engine router.
  """

  ROUTER_ARG = None

  @classmethod
  def _Args(cls, parser):
    cls.ROUTER_ARG = flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser, operation_type='update')

    bgp_peer_parser = parser.add_mutually_exclusive_group(required=True)
    # TODO(b/170227243): deprecate --peer-name after --peer-names hit GA
    bgp_peer_parser.add_argument(
        '--peer-name', help='The name of the peer being removed.')
    bgp_peer_parser.add_argument(
        '--peer-names',
        type=arg_parsers.ArgList(),
        metavar='PEER_NAME',
        help='The list of names for peers being removed.')

  @classmethod
  def Args(cls, parser):
    cls._Args(parser)

  def GetGetRequest(self, client, router_ref):
    return (client.apitools_client.routers, 'Get',
            client.messages.ComputeRoutersGetRequest(
                router=router_ref.Name(),
                region=router_ref.region,
                project=router_ref.project))

  def GetSetRequest(self, client, router_ref, replacement):
    return (client.apitools_client.routers, 'Patch',
            client.messages.ComputeRoutersPatchRequest(
                router=router_ref.Name(),
                routerResource=replacement,
                region=router_ref.region,
                project=router_ref.project))

  def Modify(self, args, existing, cleared_fields):
    """Mutate the router and record any cleared_fields for Patch request."""
    replacement = encoding.CopyProtoMessage(existing)

    input_remove_list = args.peer_names if args.peer_names else []

    input_remove_list = input_remove_list + ([args.peer_name]
                                             if args.peer_name else [])

    actual_remove_list = []
    replacement = encoding.CopyProtoMessage(existing)
    existing_router = encoding.CopyProtoMessage(existing)
    # remove peer if exists

    md5_authentication_keys_to_remove = set()
    for p in existing_router.bgpPeers:
      if p.name in input_remove_list:
        peer = p
        if peer.md5AuthenticationKeyName is not None:
          md5_authentication_keys_to_remove.add(peer.md5AuthenticationKeyName)
        replacement.bgpPeers.remove(peer)
        if not replacement.bgpPeers:
          cleared_fields.append('bgpPeers')
        actual_remove_list.append(peer.name)

    if replacement.md5AuthenticationKeys:
      replacement.md5AuthenticationKeys = [
          md5_key for md5_key in replacement.md5AuthenticationKeys
          if md5_key.name not in md5_authentication_keys_to_remove
      ]
      if not replacement.md5AuthenticationKeys:
        cleared_fields.append('md5AuthenticationKeys')

    not_found_peers = list(set(input_remove_list) - set(actual_remove_list))
    if not_found_peers:
      raise PeerNotFoundError(not_found_peers)

    return replacement

  def _Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)
    get_request = self.GetGetRequest(client, router_ref)

    objects = client.MakeRequests([get_request])

    # Cleared list fields need to be explicitly identified for Patch API.
    cleared_fields = []
    new_object = self.Modify(args, objects[0], cleared_fields)

    with client.apitools_client.IncludeFields(cleared_fields):
      # There is only one response because one request is made above
      result = client.MakeRequests(
          [self.GetSetRequest(client, router_ref, new_object)])
    return result

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RemoveBgpPeerBeta(RemoveBgpPeer):
  """Remove a BGP peer from a Compute Engine router."""

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls._Args(parser)

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveBgpPeerAlpha(RemoveBgpPeerBeta):
  """Remove a BGP peer from a Compute Engine router."""

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls._Args(parser)

  def Run(self, args):
    return self._Run(args)


RemoveBgpPeer.detailed_help = {
    'DESCRIPTION':
        """
        *{command}* removes a BGP peer from a Compute Engine router.
        """,
}
