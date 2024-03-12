# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple routers subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import routers_utils
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.console import console_io

import six

_MODE_SWITCH_MESSAGE = (
    'WARNING: switching from custom advertisement mode to default will clear '
    'out any existing advertised groups/ranges from this {resource}.')

_INCOMPATIBLE_INCREMENTAL_FLAGS_ERROR_MESSAGE = (
    '--add/remove-advertisement flags are not compatible with '
    '--set-advertisement flags.')

_CUSTOM_WITH_DEFAULT_ERROR_MESSAGE = (
    'Cannot specify custom advertisements for a {resource} with default mode.')

_GROUP_NOT_FOUND_ERROR_MESSAGE = (
    'Advertised group {group} not found on this {resource}.')

_ADVERTISED_IP_RANGE_NOT_FOUND_ERROR_MESSAGE = (
    'Advertised IP range {ip_range} not found on this {resource}.'
)

_CUSTOM_LEARNED_ROUTE_IP_RANGE_NOT_FOUND_ERROR_MESSAGE = (
    'Custom Learned Route IP address range {ip_range} not found on this'
    ' {resource}.'
)

_REQUIRE_IP_ADDRESS_AND_MASK_LENGTH_ERROR_MESSAGE = (
    '--ip-address and --mask-length must be set together.')

_MD5_AUTHENTICATION_KEY_SUFFIX = '-key'

_MD5_AUTHENTICATION_KEY_SUBSTRING = '-key-'

_MAX_LENGTH_OF_MD5_AUTHENTICATION_KEY = 63


class RouterError(core_exceptions.Error):
  """Error superclass for all router surface-related errors."""


class PeerNotFoundError(RouterError):
  """Raised when a peer is specified but not found in the router."""

  def __init__(self, name):
    self.name = name
    msg = 'peer `{0}` not found'.format(name)
    super(PeerNotFoundError, self).__init__(msg)


class InterfaceNotFoundError(RouterError):
  """Raised when an interface is specified but not found in the router."""

  def __init__(self, name):
    self.name = name
    msg = 'interface `{0}` not found'.format(name)
    super(InterfaceNotFoundError, self).__init__(msg)


class RequireIpAddressAndMaskLengthError(RouterError):
  """Raised when ip-address or mask-length is specified without the other."""

  def __init__(self):
    msg = _REQUIRE_IP_ADDRESS_AND_MASK_LENGTH_ERROR_MESSAGE
    super(RequireIpAddressAndMaskLengthError, self).__init__(msg)


class CustomWithDefaultError(RouterError):
  """Raised when custom advertisements are specified with default mode."""

  def __init__(self, messages, resource_class):
    resource_str = _GetResourceClassStr(messages, resource_class)
    error_msg = _CUSTOM_WITH_DEFAULT_ERROR_MESSAGE.format(resource=resource_str)
    super(CustomWithDefaultError, self).__init__(error_msg)


class GroupNotFoundError(RouterError):
  """Raised when an advertised group is not found in a resource."""

  def __init__(self, messages, resource_class, group):
    resource_str = _GetResourceClassStr(messages, resource_class)
    error_msg = _GROUP_NOT_FOUND_ERROR_MESSAGE.format(
        group=group, resource=resource_str)
    super(GroupNotFoundError, self).__init__(error_msg)


class IpRangeNotFoundError(RouterError):
  """Raised when an ip range is not found in a resource."""

  def __init__(self, messages, resource_class, error_message, ip_range):
    """Initializes the instance adapting the error message provided.

    Args:
      messages: API messages holder.
      resource_class: The class of the resource where the ip range is not found.
      error_message: The error message to be formatted with resource_class and
        ip_range.
      ip_range: The ip range that is not found in a resource.
    """
    resource_str = _GetResourceClassStr(messages, resource_class)
    error_msg = error_message.format(ip_range=ip_range, resource=resource_str)
    super(IpRangeNotFoundError, self).__init__(error_msg)


def _GetResourceClassStr(messages, resource_class):
  if resource_class is messages.RouterBgp:
    return 'router'
  elif resource_class is messages.RouterBgpPeer:
    return 'peer'
  else:
    raise ValueError('Invalid resource_class value: {0}'.format(resource_class))


def CheckIncompatibleFlagsOrRaise(args):
  """Checks for incompatible flags in arguments and raises an error if found."""
  if (HasReplaceAdvertisementFlags(args) and
      HasIncrementalAdvertisementFlags(args)):
    raise parser_errors.ArgumentError(
        _INCOMPATIBLE_INCREMENTAL_FLAGS_ERROR_MESSAGE)


def HasReplaceAdvertisementFlags(args):
  """Returns whether replace-style flags are specified in arguments."""
  return (args.advertisement_mode or
          args.set_advertisement_groups is not None or
          args.set_advertisement_ranges is not None)


def HasIncrementalAdvertisementFlags(args):
  """Returns whether incremental-style flags are specified in arguments."""
  return (args.add_advertisement_groups or args.remove_advertisement_groups or
          args.add_advertisement_ranges or args.remove_advertisement_ranges)


def ParseAdvertisements(messages, resource_class, args):
  """Parses and validates a completed advertisement configuration from flags.

  Args:
    messages: API messages holder.
    resource_class: RouterBgp or RouterBgpPeer class type to parse for.
    args: Flag arguments to generate configuration from.

  Returns:
    The validated tuple of mode, groups and prefixes.  If mode is DEFAULT,
    validates that no custom advertisements were specified and returns empty
    lists for each.

  Raises:
    CustomWithDefaultError: If custom advertisements were specified at the same
    time as DEFAULT mode.
  """

  mode = None
  if args.advertisement_mode is not None:
    mode = routers_utils.ParseMode(resource_class, args.advertisement_mode)
  groups = None
  if args.set_advertisement_groups is not None:
    groups = routers_utils.ParseGroups(resource_class,
                                       args.set_advertisement_groups)
  prefixes = None
  if args.set_advertisement_ranges is not None:
    prefixes = routers_utils.ParseIpRanges(messages,
                                           args.set_advertisement_ranges)

  if (mode is not None and
      mode is resource_class.AdvertiseModeValueValuesEnum.DEFAULT):
    if groups or prefixes:
      raise CustomWithDefaultError(messages, resource_class)
    else:
      # Switching to default mode clears out any existing custom advertisements
      return mode, [], []
  else:
    return mode, groups, prefixes


def ValidateCustomMode(messages, resource_class, resource):
  """Validate that a router/peer is in custom mode."""

  if (resource.advertiseMode
      is not resource_class.AdvertiseModeValueValuesEnum.CUSTOM):
    raise CustomWithDefaultError(messages, resource_class)


def PromptIfSwitchToDefaultMode(messages, resource_class, existing_mode,
                                new_mode):
  """If necessary, prompts the user for switching modes."""

  if (existing_mode is not None and
      existing_mode is resource_class.AdvertiseModeValueValuesEnum.CUSTOM and
      new_mode is not None and
      new_mode is resource_class.AdvertiseModeValueValuesEnum.DEFAULT):
    resource_str = _GetResourceClassStr(messages, resource_class)
    console_io.PromptContinue(
        message=_MODE_SWITCH_MESSAGE.format(resource=resource_str),
        cancel_on_no=True)


def FindBgpPeerOrRaise(resource, peer_name):
  """Searches for and returns a BGP peer from within a router resource.

  Args:
    resource: The router resource to find the peer for.
    peer_name: The name of the peer to find.

  Returns:
    A reference to the specified peer, if found.

  Raises:
    PeerNotFoundError: If the specified peer was not found in the router.
  """
  for peer in resource.bgpPeers:
    if peer.name == peer_name:
      return peer
  raise PeerNotFoundError(peer_name)


def RemoveGroupsFromAdvertisements(messages, resource_class, resource, groups):
  """Remove all specified groups from a resource's advertisements.

  Raises an error if any of the specified advertised groups were not found in
  the resource's advertisement set.

  Args:
    messages: API messages holder.
    resource_class: RouterBgp or RouterBgpPeer class type being modified.
    resource: the resource (router/peer) being modified.
    groups: the advertised groups to remove.

  Raises:
    GroupNotFoundError: if any group was not found in the resource.
  """

  for group in groups:
    if group not in resource.advertisedGroups:
      raise GroupNotFoundError(messages, resource_class, group)
  resource.advertisedGroups = [
      g for g in resource.advertisedGroups if g not in groups
  ]


def RemoveIpRangesFromAdvertisements(messages, resource_class, resource,
                                     ip_ranges):
  """Removes all specified IP ranges from a resource's advertisements.

  Raises an error if any of the specified advertised IP ranges were not found in
  the resource's advertisement set. The IP range search is done by exact text
  match (ignoring descriptions).

  Args:
    messages: API messages holder.
    resource_class: RouterBgp or RouterBgpPeer class type being modified.
    resource: the resource (router/peer) being modified.
    ip_ranges: the advertised IP ranges to remove.

  Raises:
    IpRangeNotFoundError: if any IP range was not found in the resource.
  """
  for ip_range in ip_ranges:
    if ip_range not in [r.range for r in resource.advertisedIpRanges]:
      raise IpRangeNotFoundError(
          messages,
          resource_class,
          _ADVERTISED_IP_RANGE_NOT_FOUND_ERROR_MESSAGE,
          ip_range,
      )
  resource.advertisedIpRanges = [
      r for r in resource.advertisedIpRanges if r.range not in ip_ranges
  ]


def RemoveIpRangesFromCustomLearnedRoutes(messages, peer, ip_ranges):
  """Removes all specified IP address ranges from a peer's custom learned routes.

  Raises an error if any of the specified custom learned route IP address ranges
  were not found in the peer's IP ranges set. The IP address range search is
  done by exact text match.

  Args:
    messages: API messages holder.
    peer: the peer being modified.
    ip_ranges: the custom learned route IP address ranges to remove.

  Raises:
    IpRangeNotFoundError: if any IP address range was not found in the peer.
  """
  for ip_range in ip_ranges:
    if ip_range not in [r.range for r in peer.customLearnedIpRanges]:
      raise IpRangeNotFoundError(
          messages,
          messages.RouterBgpPeer,
          _CUSTOM_LEARNED_ROUTE_IP_RANGE_NOT_FOUND_ERROR_MESSAGE,
          ip_range,
      )
  peer.customLearnedIpRanges = [
      r for r in peer.customLearnedIpRanges if r.range not in ip_ranges
  ]


def GenerateMd5AuthenticationKeyName(router_message, args):
  """Generates an MD5 authentication key name for the BGP peer.

  Args:
    router_message: the Cloud Router that contains the relevant BGP peer.
    args: contains arguments passed to the command

  Returns:
    Generated MD5 authentication key name
  """
  md5_authentication_key_names = set()
  for bgp_peer in router_message.bgpPeers:
    if bgp_peer.md5AuthenticationKeyName is not None:
      md5_authentication_key_names.add(bgp_peer.md5AuthenticationKeyName)
  substrings_max_length = _MAX_LENGTH_OF_MD5_AUTHENTICATION_KEY - len(
      _MD5_AUTHENTICATION_KEY_SUFFIX)
  md5_authentication_key_name = (
      args.peer_name[:substrings_max_length] + _MD5_AUTHENTICATION_KEY_SUFFIX)
  md5_authentication_key_name_suffix = 2
  while md5_authentication_key_name in md5_authentication_key_names:
    substrings_max_length = (
        _MAX_LENGTH_OF_MD5_AUTHENTICATION_KEY -
        len(_MD5_AUTHENTICATION_KEY_SUBSTRING) -
        len(six.text_type(md5_authentication_key_name_suffix)))
    md5_authentication_key_name = (
        args.peer_name[:substrings_max_length] +
        _MD5_AUTHENTICATION_KEY_SUBSTRING +
        six.text_type(md5_authentication_key_name_suffix))
    md5_authentication_key_name_suffix += 1
  return md5_authentication_key_name
