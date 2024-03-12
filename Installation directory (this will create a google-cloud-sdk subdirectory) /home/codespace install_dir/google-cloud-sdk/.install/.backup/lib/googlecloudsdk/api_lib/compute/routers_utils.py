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
"""Common classes and functions for routers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import operator

from six.moves import map  # pylint: disable=redefined-builtin


def ParseMode(resource_class, mode):
  return resource_class.AdvertiseModeValueValuesEnum(mode)


def ParseGroups(resource_class, groups):
  return list(
      map(resource_class.AdvertisedGroupsValueListEntryValuesEnum, groups))


def ParseIpRanges(messages, ip_ranges):
  """Parses a dict of IP ranges into AdvertisedIpRange objects.

  Args:
    messages: API messages holder.
    ip_ranges: A dict of IP ranges of the form ip_range=description, where
      ip_range is a CIDR-formatted IP and description is an optional text label.

  Returns:
    A list of AdvertisedIpRange objects containing the specified IP ranges.
  """
  ranges = [
      messages.RouterAdvertisedIpRange(range=ip_range, description=description)
      for ip_range, description in ip_ranges.items()
  ]
  # Sort the resulting list so that requests have a deterministic ordering
  # for test validations and user output.
  ranges.sort(key=operator.attrgetter('range', 'description'))
  return ranges


def ParseCustomLearnedIpRanges(messages, ip_ranges):
  """Parses a list of IP address ranges into CustomLearnedIpRange objects.

  Args:
    messages: API messages holder.
    ip_ranges: A list of ip_ranges, where each ip_range is a CIDR-formatted IP.

  Returns:
    A list of CustomLearnedIpRange objects containing the specified IP ranges.
  """
  ranges = [
      messages.RouterBgpPeerCustomLearnedIpRange(range=ip_range)
      for ip_range in ip_ranges
  ]
  # Sort the resulting list so that requests have a deterministic ordering
  # for test validations and user output.
  ranges.sort(key=operator.attrgetter('range'))
  return ranges
