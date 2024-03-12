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
"""Commands for reading and manipulating firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class OrgFirewallPolicies(base.Group):
  """Manage Compute Engine organization firewall policies.

  Manage Compute Engine organization firewall policies. Organization
  firewall policies are used to control incoming/outgoing traffic.
  """
  category = base.COMPUTE_CATEGORY


OrgFirewallPolicies.detailed_help = {
    'brief': ('Manage Compute Engine organization firewall policies.'),
}
