# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple org security policies subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
import sys

from googlecloudsdk.core import log

ORGANIZATION_PREFIX = 'organizations/'


def ResolveOrganizationSecurityPolicyId(org_security_policy, display_name,
                                        organization_id):
  """Returns the security policy id that matches the display_name in the org.

  Args:
    org_security_policy: the organization security policy.
    display_name: the display name of the security policy to be resolved.
    organization_id: the organization ID which the security policy belongs to.

  Returns:
    Security policy resource ID.
  """

  response = org_security_policy.List(
      parent_id=organization_id, only_generate_request=False)
  sp_id = None
  for sp in response[0].items:
    if sp.displayName == display_name:
      sp_id = sp.name
      break
  if sp_id is None:
    log.error(
        'Invalid display name: {0}. No Security Policy with this display name exists.'
        .format(display_name))
    sys.exit()
  return sp_id


def GetSecurityPolicyId(org_security_policy_client,
                        security_policy,
                        organization=None):
  """Returns the security policy id that matches the display_name in the org.

  Args:
    org_security_policy_client: the organization security policy client.
    security_policy: the display name or ID of the security policy to be
      resolved.
    organization: the organization ID which the security policy belongs to.

  Returns:
    Security policy resource ID.
  """

  # If it is not numeric ID with length between 9 and 15, then do the lookup.
  if not re.match(r'\d{9,15}', security_policy):
    if organization is None:
      log.error(
          'Must set --organization=ORGANIZATION when display name [%s]'
          'is used.', security_policy)
      sys.exit()
    return ResolveOrganizationSecurityPolicyId(
        org_security_policy_client, security_policy,
        ORGANIZATION_PREFIX + organization)
  return security_policy
