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
"""VMware Engine external access rules client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util


class ExternalAccessRulesClient(util.VmwareClientBase):
  """VMware Engine network policy client."""

  def __init__(self):
    super(ExternalAccessRulesClient, self).__init__()
    self.service = self.client.projects_locations_networkPolicies_externalAccessRules
    self.ip_regex = re.compile(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$')
    self.ip_ranges_regex = re.compile(
        r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}/\d{1,2}$')

  def parse_ip_range(self, ip_range):
    if self.ip_regex.match(ip_range) is not None:
      return self.messages.IpRange(ipAddress=ip_range)
    if self.ip_ranges_regex.match(ip_range) is not None:
      return self.messages.IpRange(ipAddressRange=ip_range)
    return self.messages.IpRange(externalAddress=ip_range)

  def Get(self, resource):
    request = self.messages.VmwareengineProjectsLocationsNetworkPoliciesExternalAccessRulesGetRequest(
        name=resource.RelativeName())
    response = self.service.Get(request)
    return response

  def Create(self,
             resource,
             priority,
             ip_protocol,
             source_ranges,
             destination_ranges,
             source_ports,
             destination_ports,
             description=None,
             action=None):
    parent = resource.Parent().RelativeName()
    external_access_rule_id = resource.Name()
    external_access_rule = self.messages.ExternalAccessRule(
        description=description,
        priority=priority,
        ipProtocol=ip_protocol)

    if source_ports is None:
      external_access_rule.sourcePorts = []
    else:
      external_access_rule.sourcePorts = source_ports

    if destination_ports is None:
      external_access_rule.destinationPorts = []
    else:
      external_access_rule.destinationPorts = destination_ports

    if action is None or action.strip().upper() == 'ALLOW':
      external_access_rule.action = self.messages.ExternalAccessRule.ActionValueValuesEnum.ALLOW
    elif action.strip().upper() == 'DENY':
      external_access_rule.action = self.messages.ExternalAccessRule.ActionValueValuesEnum.DENY

    external_access_rule.sourceIpRanges = [
        self.parse_ip_range(ip) for ip in source_ranges
    ]
    external_access_rule.destinationIpRanges = [
        self.parse_ip_range(ip) for ip in destination_ranges
    ]
    request = self.messages.VmwareengineProjectsLocationsNetworkPoliciesExternalAccessRulesCreateRequest(
        parent=parent,
        externalAccessRule=external_access_rule,
        externalAccessRuleId=external_access_rule_id,
    )
    return self.service.Create(request)

  def Update(self,
             resource,
             priority=None,
             ip_protocol=None,
             source_ranges=None,
             destination_ranges=None,
             source_ports=None,
             destination_ports=None,
             description=None,
             action=None):
    external_access_rule = self.Get(resource)
    update_mask = []
    if description is not None:
      external_access_rule.description = description
      update_mask.append('description')
    if priority is not None:
      external_access_rule.priority = priority
      update_mask.append('priority')
    if ip_protocol is not None:
      external_access_rule.ipProtocol = ip_protocol
      update_mask.append('ip_protocol')
    if source_ports is not None:
      external_access_rule.sourcePorts = source_ports
      update_mask.append('source_ports')
    if destination_ports is not None:
      external_access_rule.destinationPorts = destination_ports
      update_mask.append('destination_ports')

    if action is not None:
      if action.strip().upper() == 'ALLOW':
        external_access_rule.action = self.messages.ExternalAccessRule.ActionValueValuesEnum.ALLOW
      elif action.strip().upper() == 'DENY':
        external_access_rule.action = self.messages.ExternalAccessRule.ActionValueValuesEnum.DENY
      update_mask.append('action')

    if source_ranges is not None and source_ranges:
      external_access_rule.sourceIpRanges = [
          self.parse_ip_range(ip) for ip in source_ranges
      ]
      update_mask.append('source_ip_ranges')
    if destination_ranges is not None and destination_ranges:
      external_access_rule.destinationIpRanges = [
          self.parse_ip_range(ip) for ip in destination_ranges
      ]
      update_mask.append('destination_ip_ranges')
    request = self.messages.VmwareengineProjectsLocationsNetworkPoliciesExternalAccessRulesPatchRequest(
        externalAccessRule=external_access_rule,
        name=resource.RelativeName(),
        updateMask=','.join(update_mask),
    )
    return self.service.Patch(request)

  def Delete(self, resource):
    return self.service.Delete(
        self.messages.VmwareengineProjectsLocationsNetworkPoliciesExternalAccessRulesDeleteRequest(
            name=resource.RelativeName()
        )
    )

  def List(self, network_policy_resource):
    network_policy = network_policy_resource.RelativeName()
    request = self.messages.VmwareengineProjectsLocationsNetworkPoliciesExternalAccessRulesListRequest(
        parent=network_policy
    )
    return list_pager.YieldFromList(
        self.service,
        request,
        batch_size_attribute='pageSize',
        field='externalAccessRules')
