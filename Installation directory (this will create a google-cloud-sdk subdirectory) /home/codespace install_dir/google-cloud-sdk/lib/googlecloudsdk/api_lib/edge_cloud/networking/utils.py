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
"""Utility functions for Distributed Cloud Edge Network."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ipaddress
import re

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources

VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1alpha1',
    base.ReleaseTrack.GA: 'v1',
}


def GetClientInstance(release_track=base.ReleaseTrack.GA, no_http=False):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance('edgenetwork', api_version, no_http=no_http)


def GetMessagesModule(release_track=base.ReleaseTrack.GA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetMessagesModule('edgenetwork', api_version)


def GetResourceParser(release_track=base.ReleaseTrack.GA):
  resource_parser = resources.Registry()
  api_version = VERSION_MAP.get(release_track)
  resource_parser.RegisterApiByName('edgenetwork', api_version)
  return resource_parser


def WaitForOperation(client, operation, resource):
  """Waits for the given google.longrunning.Operation to complete."""
  operation_ref = resources.REGISTRY.Parse(
      operation.name, collection='edgenetwork.projects.locations.operations')
  poller = waiter.CloudOperationPoller(resource,
                                       client.projects_locations_operations)
  waiter.WaitFor(
      poller, operation_ref,
      'Waiting for [{0}] to finish'.format(operation_ref.RelativeName()))


def IsValidIPV4(ip):
  """Accepts an ipv4 address in string form and returns True if valid."""
  match = re.match(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$', ip)
  if not match:
    return False

  octets = [int(x) for x in match.groups()]

  # first octet must not be 0
  if octets[0] == 0:
    return False

  for n in octets:
    if n < 0 or n > 255:
      return False

  return True


def IsValidIPV6(ip):
  """Validates a given ip address to be IPv6 address."""
  try:
    _ = ipaddress.IPv6Address(ip)
  except ValueError:
    return False
  return True


def IPArgument(value):
  """Argparse argument type that checks for a valid ipv4 address."""
  if not IsValidIPV4(value) and not IsValidIPV6(value):
    raise arg_parsers.ArgumentTypeError(
        "invalid IPv4 or IPv6 address: '{0}'".format(value)
    )
  return value


def IPV4Argument(value):
  """Argparse argument type that checks for a valid ipv4 address."""
  if not IsValidIPV4(value):
    raise arg_parsers.ArgumentTypeError(
        "invalid ipv4 value: '{0}'".format(value))

  return value
