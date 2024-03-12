# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Convenience functions for dealing with alias IP ranges."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as calliope_exceptions

_INVALID_FORMAT_MESSAGE_FOR_INSTANCE = (
    'An alias IP range must contain range name and IP range separated by '
    'a colon, or only the IP range.  The IP range portion can be '
    'expressed as a full IP CIDR range (e.g. 10.1.1.0/24), or a single IP '
    'address (e.g. 10.1.1.1), or an IP CIDR net mask (e.g. /24)')

_INVALID_FORMAT_MESSAGE_FOR_INSTANCE_TEMPLATE = (
    'An alias IP range must contain range name and IP CIDR net mask (e.g. '
    '/24) separated by a colon, or only the IP CIDR net mask (e.g. /24).')


def CreateAliasIpRangeMessagesFromString(
    messages, instance, alias_ip_ranges_string):
  """Returns a list of AliasIpRange messages by parsing the input string.

  Args:
    messages: GCE API messages.
    instance: If True, this call is for parsing instance flags; otherwise
        it is for instance template.
    alias_ip_ranges_string: Command line string that specifies a list of
        alias IP ranges. Alias IP ranges are separated by semicolons.
        Each alias IP range has the format <alias-ip-range> or
        {range-name}:<alias-ip-range>.  The range-name is the name of the
        range within the network interface's subnet from which to allocate
        an alias range. alias-ip-range can be a CIDR range, an IP address,
        or a net mask (e.g. "/24"). Note that the validation is done on
        the server. This method just creates the request message by parsing
        the input string.
        Example string:
        "/24;range2:192.168.100.0/24;range3:192.168.101.0/24"

  Returns:
    A list of AliasIpRange messages.
  """
  if not alias_ip_ranges_string:
    return []
  alias_ip_range_strings = alias_ip_ranges_string.split(';')
  return [_CreateAliasIpRangeMessageFromString(messages, instance, s) for
          s in alias_ip_range_strings]


def _CreateAliasIpRangeMessageFromString(
    messages, instance, alias_ip_range_string):
  """Returns a new AliasIpRange message by parsing the input string."""
  alias_ip_range = messages.AliasIpRange()

  tokens = alias_ip_range_string.split(':')
  if len(tokens) == 1:
    # Only IP CIDR is specified.
    alias_ip_range.ipCidrRange = tokens[0]
  elif len(tokens) == 2:
    # Both the range name and the CIDR are specified
    alias_ip_range.subnetworkRangeName = tokens[0]
    alias_ip_range.ipCidrRange = tokens[1]
  else:
    # There are too many or too few tokens.
    raise calliope_exceptions.InvalidArgumentException(
        'aliases',
        _INVALID_FORMAT_MESSAGE_FOR_INSTANCE if instance
        else _INVALID_FORMAT_MESSAGE_FOR_INSTANCE_TEMPLATE)
  return alias_ip_range
