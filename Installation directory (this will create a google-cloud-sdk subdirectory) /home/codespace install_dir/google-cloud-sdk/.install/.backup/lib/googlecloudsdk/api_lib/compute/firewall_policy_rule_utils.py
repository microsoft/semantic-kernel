# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Common classes and functions for organization firewall policy rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute import  exceptions

ALLOWED_METAVAR = 'PROTOCOL[:PORT[-PORT]]'
LEGAL_SPECS = re.compile(
    r"""

    (?P<protocol>[a-zA-Z0-9+.-]+) # The protocol group.

    (:(?P<ports>\d+(-\d+)?))?     # The optional ports group.
                                  # May specify a range.

    $                             # End of input marker.
    """, re.VERBOSE)


def ParseLayer4Configs(layer4_conifigs, message_classes):
  """Parses protocol:port mappings for --layer4-configs command line."""
  layer4_config_list = []
  for spec in layer4_conifigs or []:
    match = LEGAL_SPECS.match(spec)
    if not match:
      raise exceptions.ArgumentError(
          'Organization firewall policy rules must be of the form {0}; '
          'received [{1}].'.format(ALLOWED_METAVAR, spec))
    if match.group('ports'):
      ports = [match.group('ports')]
    else:
      ports = []
    layer4_conifig = (
        message_classes.FirewallPolicyRuleMatcherLayer4Config(
            ipProtocol=match.group('protocol'), ports=ports))
    layer4_config_list.append(layer4_conifig)
  return layer4_config_list


def ConvertPriorityToInt(priority):
  try:
    int_priority = int(priority)
  except ValueError:
    raise calliope_exceptions.InvalidArgumentException(
        'priority', 'priority must be a valid non-negative integer.')
  if int_priority < 0:
    raise calliope_exceptions.InvalidArgumentException(
        'priority', 'priority must be a valid non-negative integer.')
  return int_priority
