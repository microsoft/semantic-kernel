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
"""Code that's shared between multiple org firewall policies subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
import sys

from googlecloudsdk.api_lib import network_security
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import reference_utils
from googlecloudsdk.core import log

ORGANIZATION_PREFIX = 'organizations/'


def ResolveFirewallPolicyId(firewall_policy, short_name, organization_id):
  """Returns the firewall policy id that matches the short_name in the org.

  Args:
    firewall_policy: the organization firewall policy.
    short_name: the short name of the firewall policy to be resolved.
    organization_id: the organization ID which the firewall policy belongs to.

  Returns:
    Firewall policy resource ID.
  """

  response = firewall_policy.List(
      parent_id=organization_id, only_generate_request=False)
  fp_id = None
  for fp in response[0].items:
    if fp.displayName == short_name:
      fp_id = fp.name
      break
  if fp_id is None:
    log.error(
        'Invalid short name: {0}. No Security Policy with this short name exists.'
        .format(short_name))
    sys.exit()
  return fp_id


def GetFirewallPolicyId(firewall_policy_client,
                        firewall_policy,
                        organization=None):
  """Returns the firewall policy id that matches the short_name in the org.

  Args:
    firewall_policy_client: the organization firewall policy client.
    firewall_policy: the short name or ID of the firewall policy to be resolved.
    organization: the organization ID which the firewall policy belongs to.

  Returns:
    Firewall policy resource ID.
  """

  # If it is not numeric ID with length between 9 and 15, then do the lookup.
  if not re.match(r'\d{9,15}', firewall_policy):
    if organization is None:
      log.error(
          'Must set --organization=ORGANIZATION when short name [%s]'
          'is used.', firewall_policy)
      sys.exit()
    return ResolveFirewallPolicyId(firewall_policy_client, firewall_policy,
                                   ORGANIZATION_PREFIX + organization)
  return firewall_policy


def GetFirewallPolicyOrganization(firewall_policy_client, firewall_policy_id,
                                  optional_organization):
  """Returns ID of the organization the given firewall policy belongs to.

  Args:
    firewall_policy_client: the organization firewall policy client.
    firewall_policy_id: the short name or ID of the firewall policy to be
      resolved.
    optional_organization: organization if provided.

  Returns:
    Firewall policy resource ID.
  """
  if not re.match(r'\d{9,15}',
                  firewall_policy_id) and optional_organization is None:
    raise exceptions.RequiredArgumentException(
        '--organization',
        'Must set --organization=ORGANIZATION when short name [{0}]'
        'is used.'.format(firewall_policy_id))
  organization = optional_organization
  if not organization:
    fetched_policies = firewall_policy_client.Describe(fp_id=firewall_policy_id)
    if not fetched_policies:
      raise compute_exceptions.InvalidResourceError(
          'Firewall Policy [{0}] does not exist.'.format(firewall_policy_id))
    organization = fetched_policies[0].parent
  if '/' in organization:
    organization = organization.split('/')[1]
  return organization


def BuildSecurityProfileGroupUrl(security_profile_group, optional_organization,
                                 firewall_policy_client, firewall_policy_id):
  """Returns Full URL reference of Security Profile Group.

  Args:
    security_profile_group: reference string provided by the user.
    optional_organization: organization if provided.
    firewall_policy_client: the organization firewall policy client.
    firewall_policy_id: the short name or ID of the firewall policy to be
      resolved.

  Returns:
    URL to Security Profile Group.
  """

  # Probably Full URL or Full Resource Name -> pass without change
  if '/' in security_profile_group:
    return security_profile_group
  # Create full resource name
  organization = GetFirewallPolicyOrganization(
      firewall_policy_client=firewall_policy_client,
      firewall_policy_id=firewall_policy_id,
      optional_organization=optional_organization)
  return reference_utils.BuildFullResourceUrlForOrgBasedResource(
      base_uri=network_security.GetApiBaseUrl(
          network_security.base.ReleaseTrack.GA
      ),
      org_id=organization,
      collection_name='securityProfileGroups',
      resource_name=security_profile_group,
  )


def BuildAddressGroupUrl(address_group, optional_organization,
                         firewall_policy_client, firewall_policy_id):
  """Returns partial URL reference of Address Group.

  Args:
    address_group: reference string provided by the user.
    optional_organization: organization if provided.
    firewall_policy_client: the organization firewall policy client.
    firewall_policy_id: the short name or ID of the firewall policy to be
      resolved.

  Returns:
    partial URL to Address Group.
  """

  # Probably a URL -> pass without change
  if '/' in address_group:
    return address_group
  # Create partial URL
  organization = GetFirewallPolicyOrganization(
      firewall_policy_client=firewall_policy_client,
      firewall_policy_id=firewall_policy_id,
      optional_organization=optional_organization)
  return reference_utils.BuildFullResourceUrlForOrgBasedResource(
      base_uri='',  # Empty string for partial URLs
      org_id=organization,
      collection_name='addressGroups',
      resource_name=address_group)
