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
"""Functions for creating a client to talk to the App Engine Admin API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.app.api import appengine_api_client_base as base
from googlecloudsdk.calliope import base as calliope_base


VERSION_MAP = {
    calliope_base.ReleaseTrack.GA: 'v1',
    calliope_base.ReleaseTrack.ALPHA: 'v1alpha',
    calliope_base.ReleaseTrack.BETA: 'v1beta'
}


def GetApiClientForTrack(release_track):
  api_version = VERSION_MAP[release_track]
  return AppengineFirewallApiClient.GetApiClient(api_version)


class AppengineFirewallApiClient(base.AppengineApiClientBase):
  """Client used by gcloud to communicate with the App Engine API."""

  def __init__(self, client):
    base.AppengineApiClientBase.__init__(self, client)

  def Create(self, priority, source_range, action, description):
    """Creates a firewall rule for the given application.

    Args:
      priority: int, the priority of the rule between [1, 2^31-1].
                The default rule may not be created, only updated.
      source_range: str, the ip address or range to take action on.
      action: firewall_rules_util.Action, optional action to take on matched
        addresses.
      description: str, an optional string description of the rule.

    Returns:
      The new firewall rule.
    """
    rule = self.messages.FirewallRule(
        priority=priority,
        action=action,
        description=description,
        sourceRange=source_range)

    request = self.messages.AppengineAppsFirewallIngressRulesCreateRequest(
        parent=self._FormatApp(), firewallRule=rule)

    return self.client.apps_firewall_ingressRules.Create(request)

  def Delete(self, resource):
    """Deletes a firewall rule for the given application.

    Args:
      resource: str, the resource path to the firewall rule.
    """
    request = self.messages.AppengineAppsFirewallIngressRulesDeleteRequest(
        name=resource.RelativeName())

    self.client.apps_firewall_ingressRules.Delete(request)

  def List(self, matching_address=None):
    """Lists all ingress firewall rules for the given application.

    Args:
      matching_address: str, an optional ip address to filter matching rules.

    Returns:
      A list of FirewallRule objects.
    """

    request = self.messages.AppengineAppsFirewallIngressRulesListRequest(
        parent=self._FormatApp(), matchingAddress=matching_address)

    return list_pager.YieldFromList(
        self.client.apps_firewall_ingressRules,
        request,
        field='ingressRules',
        batch_size_attribute='pageSize')

  def Get(self, resource):
    """Gets a firewall rule for the given application.

    Args:
      resource: str, the resource path to the firewall rule.

    Returns:
      A FirewallRule object.
    """
    request = self.messages.AppengineAppsFirewallIngressRulesGetRequest(
        name=resource.RelativeName())

    response = self.client.apps_firewall_ingressRules.Get(request)

    return response

  def Update(self,
             resource,
             priority,
             source_range=None,
             action=None,
             description=None):
    """Updates a firewall rule for the given application.

    Args:
      resource: str, the resource path to the firewall rule.
      priority: int, the priority of the rule.
      source_range: str, optional ip address or range to take action on.
      action: firewall_rules_util.Action, optional action to take on matched
        addresses.
      description: str, optional string description of the rule.

    Returns:
      The updated firewall rule.

    Raises:
      NoFieldsSpecifiedError: when no fields have been specified for the update.
    """

    mask_fields = []

    if action:
      mask_fields.append('action')
    if source_range:
      mask_fields.append('sourceRange')
    if description:
      mask_fields.append('description')

    rule = self.messages.FirewallRule(
        priority=priority,
        action=action,
        description=description,
        sourceRange=source_range)

    if not mask_fields:
      raise util.NoFieldsSpecifiedError()

    request = self.messages.AppengineAppsFirewallIngressRulesPatchRequest(
        name=resource.RelativeName(),
        firewallRule=rule,
        updateMask=','.join(mask_fields))

    return self.client.apps_firewall_ingressRules.Patch(request)
