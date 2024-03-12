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
"""Common utility functions for network operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.util import times
import ipaddress
import six

IP_VERSION_4 = 4
IP_VERSION_6 = 6
IP_VERSION_UNKNOWN = 0


def GetIpVersion(ip_address):
  """Given an ip address, determine IP version.

  Args:
    ip_address: string, IP address to test IP version of

  Returns:
    int, the IP version if it could be determined or IP_VERSION_UNKNOWN
    otherwise.
  """
  try:
    # ipaddress only allows unicode input
    version = ipaddress.ip_address(six.text_type(ip_address)).version
    if version not in (IP_VERSION_4, IP_VERSION_6):
      raise ValueError('Reported IP version not recognized.')
    return version
  except ValueError:  # ipaddr library could not resolve address
    return IP_VERSION_UNKNOWN


def GetCurrentTime():
  """Returns the current UTC datetime."""
  return times.Now(tzinfo=times.UTC)
