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
"""Distributed Cloud Edge Network router API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ipaddress

from apitools.base.py import encoding
from googlecloudsdk.api_lib.edge_cloud.networking import utils
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.core import exceptions as core_exceptions

import six


class RoutersClient(object):
  """Client for private connections service in the API."""
  # REST API Field Names for the updateMask
  FIELD_PATH_INTERFACE = 'interface'
  FIELD_PATH_BGP_PEER = 'bgp_peer'
  FIELD_PATH_ROUTE_ADVERTISEMENTS = 'route_advertisements'

  def __init__(self, release_track, client=None, messages=None):
    self._client = client or utils.GetClientInstance(release_track)
    self._messages = messages or utils.GetMessagesModule(release_track)
    self._service = self._client.projects_locations_zones_routers
    self._resource_parser = utils.GetResourceParser(release_track)

  def WaitForOperation(self, operation):
    """Waits for the given google.longrunning.Operation to complete."""
    return utils.WaitForOperation(self._client, operation, self._service)

  def ModifyToAddInterface(self, router_ref, args, existing):
    """Mutate the router to add an interface."""
    replacement = encoding.CopyProtoMessage(existing)
    new_interface = self._messages.Interface(name=args.interface_name)

    if args.interconnect_attachment is not None:
      attachment_ref = self._resource_parser.Create(
          'edgenetwork.projects.locations.zones.interconnectAttachments',
          interconnectAttachmentsId=args.interconnect_attachment,
          projectsId=router_ref.projectsId,
          locationsId=router_ref.locationsId,
          zonesId=router_ref.zonesId)

      if args.ip_mask_length is None or args.ip_address is None:
        raise parser_errors.ArgumentException(
            '--ip-address and --ip-mask-length must be set'
        )

      try:
        ip_address = ipaddress.ip_address(args.ip_address)
      except ValueError as err:
        raise parser_errors.ArgumentException(str(err))

      if args.ip_mask_length > ip_address.max_prefixlen:
        raise parser_errors.ArgumentException(
            '--ip-mask-length should be less than %s' % ip_address.max_prefixlen
        )

      cidr = '{0}/{1}'.format(args.ip_address, args.ip_mask_length)
      if ip_address.version == 4:  # Is an ipv4 cidr
        new_interface.ipv4Cidr = cidr
      else:
        new_interface.ipv6Cidr = cidr

      new_interface.linkedInterconnectAttachment = attachment_ref.RelativeName()

    if args.subnetwork is not None:
      subnet_ref = self._resource_parser.Create(
          'edgenetwork.projects.locations.zones.subnets',
          subnetsId=args.subnetwork,
          projectsId=router_ref.projectsId,
          locationsId=router_ref.locationsId,
          zonesId=router_ref.zonesId)
      new_interface.subnetwork = subnet_ref.RelativeName()

    if args.loopback_ip_addresses is not None:
      new_interface.loopbackIpAddresses = args.loopback_ip_addresses

    replacement.interface.append(new_interface)
    return replacement

  def ModifyToRemoveInterface(self, args, existing):
    """Mutate the router to delete a list of interfaces."""
    # Get the list of interfaces that are to be removed from args.
    input_remove_list = args.interface_names if args.interface_names else []
    input_remove_list = input_remove_list + ([args.interface_name]
                                             if args.interface_name else [])
    # Remove interface if exists
    actual_remove_list = []
    replacement = encoding.CopyProtoMessage(existing)
    existing_router = encoding.CopyProtoMessage(existing)

    for iface in existing_router.interface:
      if iface.name in input_remove_list:
        replacement.interface.remove(iface)
        actual_remove_list.append(iface.name)

    # If there still are interfaces that we didn't find, the input is invalid.
    not_found_interface = sorted(
        set(input_remove_list) - set(actual_remove_list))
    if not_found_interface:
      error_msg = 'interface [{}] not found'.format(
          ', '.join(not_found_interface))
      raise core_exceptions.Error(error_msg)

    return replacement

  def ModifyToAddBgpPeer(self, args, existing):
    """Mutate the router to add a BGP peer."""

    replacement = encoding.CopyProtoMessage(existing)
    bgp_peer_args = {
        'name': args.peer_name,
        'interface': args.interface,
        'peerAsn': args.peer_asn,
    }

    if args.peer_ipv4_range is not None:
      bgp_peer_args['peerIpv4Cidr'] = args.peer_ipv4_range

    # Only present in ALPHA release
    if 'peer_ipv6_range' in args and args.peer_ipv6_range is not None:
      bgp_peer_args['peerIpv6Cidr'] = args.peer_ipv6_range

    new_bgp_peer = self._messages.BgpPeer(**bgp_peer_args)
    replacement.bgpPeer.append(new_bgp_peer)
    return replacement

  def ModifyToRemoveBgpPeer(self, args, existing):
    """Mutate the router to delete BGP peers."""
    input_remove_list = args.peer_names if args.peer_names else []
    input_remove_list = input_remove_list + ([args.peer_name]
                                             if args.peer_name else [])
    actual_remove_list = []
    replacement = encoding.CopyProtoMessage(existing)
    existing_router = encoding.CopyProtoMessage(existing)

    for peer in existing_router.bgpPeer:
      if peer.name in input_remove_list:
        replacement.bgpPeer.remove(peer)
        actual_remove_list.append(peer.name)

    # If there still are bgp peers that we didn't find, the input is invalid.
    not_found_peer = sorted(set(input_remove_list) - set(actual_remove_list))
    if not_found_peer:
      error_msg = 'peer [{}] not found'.format(', '.join(not_found_peer))
      raise core_exceptions.Error(error_msg)

    return replacement

  def AddInterface(self, router_ref, args):
    """Create an interface on a router."""
    # Get current interfaces of router
    get_router_req = self._messages.EdgenetworkProjectsLocationsZonesRoutersGetRequest(
        name=router_ref.RelativeName())
    router_object = self._service.Get(get_router_req)

    # Update interfaces to add the new interface
    new_router_object = self.ModifyToAddInterface(router_ref, args,
                                                  router_object)

    update_router_req = self._messages.EdgenetworkProjectsLocationsZonesRoutersPatchRequest(
        name=router_ref.RelativeName(),
        router=new_router_object,
        updateMask=self.FIELD_PATH_INTERFACE)
    return self._service.Patch(update_router_req)

  def RemoveInterface(self, router_ref, args):
    """Remove a list of interfaces on a router."""
    # Get current interfaces of router
    get_router_req = self._messages.EdgenetworkProjectsLocationsZonesRoutersGetRequest(
        name=router_ref.RelativeName())
    router_object = self._service.Get(get_router_req)
    # Update interfaces to add the new interface
    new_router_object = self.ModifyToRemoveInterface(args, router_object)

    update_router_req = self._messages.EdgenetworkProjectsLocationsZonesRoutersPatchRequest(
        name=router_ref.RelativeName(),
        router=new_router_object,
        updateMask=self.FIELD_PATH_INTERFACE)

    return self._service.Patch(update_router_req)

  def ModifyToApplyAdvertisementChanges(self, args, existing):
    """Create a router based on `existing` with the routes change."""

    def cidrset(cidr_strs):
      return set(ipaddress.ip_network(cidrstr) for cidrstr in cidr_strs)

    def sorted_strings(cidrs):
      return [six.text_type(cidr) for cidr in sorted(cidrs)]

    advertisements = cidrset(existing.routeAdvertisements)
    replacement = encoding.CopyProtoMessage(existing)

    if args.add_advertisement_ranges:
      to_add = set(args.add_advertisement_ranges)
      already_present = sorted_strings(advertisements & to_add)
      if already_present:
        raise core_exceptions.Error(
            'attempting to add routes that are already present: {}'.format(
                ', '.join(already_present)))
      advertisements |= to_add
    elif args.remove_advertisement_ranges:
      to_rm = cidrset(args.remove_advertisement_ranges)
      already_missing = sorted_strings(to_rm - advertisements)
      if already_missing:
        raise core_exceptions.Error(
            'attempting to remove routes that are not present: {}'.format(
                ', '.join(already_missing)))
      advertisements -= to_rm
    elif args.set_advertisement_ranges:
      advertisements = cidrset(args.set_advertisement_ranges)
    else:
      raise parser_errors.ArgumentException(
          'Missing --add-advertisement-ranges, '
          '--remove-advertisement-ranges, or --set-advertisement-ranges')

    replacement.routeAdvertisements = list(map(str, sorted(advertisements)))
    return replacement

  def ChangeAdvertisements(self, router_ref, args):
    """Create a patch request that updates the Route advertisements of a router.
    """
    get_router_req = self._messages.EdgenetworkProjectsLocationsZonesRoutersGetRequest(
        name=router_ref.RelativeName())
    router_object = self._service.Get(get_router_req)

    new_router_object = self.ModifyToApplyAdvertisementChanges(
        args, router_object)

    update_router_request = (
        self._messages.EdgenetworkProjectsLocationsZonesRoutersPatchRequest(
            name=router_ref.RelativeName(),
            router=new_router_object,
            updateMask=self.FIELD_PATH_ROUTE_ADVERTISEMENTS))

    return self._service.Patch(update_router_request)

  def AddBgpPeer(self, router_ref, args):
    """Mutate the router so to add a BGP peer."""
    # Get current router
    get_router_req = self._messages.EdgenetworkProjectsLocationsZonesRoutersGetRequest(
        name=router_ref.RelativeName())
    router_object = self._service.Get(get_router_req)

    # Update router object to add the new bgp peer
    new_router_object = self.ModifyToAddBgpPeer(args, router_object)

    update_router_req = self._messages.EdgenetworkProjectsLocationsZonesRoutersPatchRequest(
        name=router_ref.RelativeName(),
        router=new_router_object,
        updateMask=self.FIELD_PATH_BGP_PEER)
    return self._service.Patch(update_router_req)

  def RemoveBgpPeer(self, router_ref, args):
    """Mutate the router so to remove a BGP peer."""
    # Get current router
    get_router_req = self._messages.EdgenetworkProjectsLocationsZonesRoutersGetRequest(
        name=router_ref.RelativeName())
    router_object = self._service.Get(get_router_req)

    # Update router object to remove specified bgp peers
    new_router_object = self.ModifyToRemoveBgpPeer(args, router_object)

    update_router_req = self._messages.EdgenetworkProjectsLocationsZonesRoutersPatchRequest(
        name=router_ref.RelativeName(),
        router=new_router_object,
        updateMask=self.FIELD_PATH_BGP_PEER)
    return self._service.Patch(update_router_req)

  def GetStatus(self, router_ref):
    """Get the status of a specified router."""
    get_router_status_req = self._messages.EdgenetworkProjectsLocationsZonesRoutersDiagnoseRequest(
        name=router_ref.RelativeName())
    return self._service.Diagnose(get_router_status_req)
