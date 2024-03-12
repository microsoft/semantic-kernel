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
"""Region Network Firewall Policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

OP_COLLECTION_NAME = 'compute.regionOperations'
API_COLLECTION_NAME = 'compute.regionNetworkFirewallPolicies'


class RegionNetworkFirewallPolicy(object):
  """Abstracts a region network firewall policy resource."""

  def __init__(self, ref, compute_client=None):
    self.ref = ref
    self._compute_client = compute_client

  @property
  def _client(self):
    return self._compute_client.apitools_client

  @property
  def _messages(self):
    return self._compute_client.messages

  @property
  def _service(self):
    return self._client.regionNetworkFirewallPolicies

  def _HasProject(self, collection):
    collection_info = self._resources.GetCollectionInfo(collection,
                                                        self._version)
    return ('projects' in collection_info.path or
            'projects' in collection_info.base_url)

  def _MakeAddAssociationRequestTuple(self, association, firewall_policy,
                                      replace_existing_association):
    return (self._client.regionNetworkFirewallPolicies, 'AddAssociation',
            self._messages
            .ComputeRegionNetworkFirewallPoliciesAddAssociationRequest(
                firewallPolicyAssociation=association,
                firewallPolicy=firewall_policy,
                replaceExistingAssociation=replace_existing_association,
                project=self.ref.project,
                region=self.ref.region))

  def _MakePatchAssociationRequestTuple(self, association, firewall_policy):
    return (
        self._client.regionNetworkFirewallPolicies,
        'PatchAssociation',
        self._messages.ComputeRegionNetworkFirewallPoliciesPatchAssociationRequest(
            firewallPolicyAssociation=association,
            firewallPolicy=firewall_policy,
            project=self.ref.project,
            region=self.ref.region,
        ),
    )

  def _MakeCloneRulesRequestTuple(self, source_firewall_policy):
    return (
        self._client.regionNetworkFirewallPolicies, 'CloneRules',
        self._messages.ComputeRegionNetworkFirewallPoliciesCloneRulesRequest(
            firewallPolicy=self.ref.Name(),
            sourceFirewallPolicy=source_firewall_policy,
            project=self.ref.project,
            region=self.ref.region))

  def _MakeCreateRequestTuple(self, firewall_policy):
    return (self._client.regionNetworkFirewallPolicies, 'Insert',
            self._messages.ComputeRegionNetworkFirewallPoliciesInsertRequest(
                firewallPolicy=firewall_policy,
                project=self.ref.project,
                region=self.ref.region))

  def _MakeDeleteRequestTuple(self, firewall_policy):
    return (self._client.regionNetworkFirewallPolicies, 'Delete',
            self._messages.ComputeRegionNetworkFirewallPoliciesDeleteRequest(
                firewallPolicy=firewall_policy,
                project=self.ref.project,
                region=self.ref.region))

  def _MakeDescribeRequestTuple(self):
    return (self._client.regionNetworkFirewallPolicies, 'Get',
            self._messages.ComputeRegionNetworkFirewallPoliciesGetRequest(
                firewallPolicy=self.ref.Name(),
                project=self.ref.project,
                region=self.ref.region))

  def _MakeDeleteAssociationRequestTuple(self, firewall_policy, name):
    return (self._client.regionNetworkFirewallPolicies, 'RemoveAssociation',
            self._messages
            .ComputeRegionNetworkFirewallPoliciesRemoveAssociationRequest(
                firewallPolicy=firewall_policy,
                name=name,
                project=self.ref.project,
                region=self.ref.region))

  def _MakeUpdateRequestTuple(self, firewall_policy=None):
    return (self._client.regionNetworkFirewallPolicies, 'Patch',
            self._messages.ComputeRegionNetworkFirewallPoliciesPatchRequest(
                firewallPolicy=self.ref.Name(),
                firewallPolicyResource=firewall_policy,
                project=self.ref.project,
                region=self.ref.region))

  def CloneRules(self,
                 source_firewall_policy=None,
                 only_generate_request=False):
    """Sends request to clone all the rules from another firewall policy."""
    requests = [
        self._MakeCloneRulesRequestTuple(
            source_firewall_policy=source_firewall_policy)
    ]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def Create(self, firewall_policy=None, only_generate_request=False):
    """Sends request to create a region network firewall policy."""
    requests = [self._MakeCreateRequestTuple(firewall_policy=firewall_policy)]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def Delete(self, firewall_policy=None, only_generate_request=False):
    """Sends request to delete a region network firewall policy."""
    requests = [self._MakeDeleteRequestTuple(firewall_policy=firewall_policy)]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def Describe(self, only_generate_request=False):
    """Sends request to describe a region network firewall policy."""
    requests = [self._MakeDescribeRequestTuple()]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def Update(self, firewall_policy=None, only_generate_request=False):
    """Sends request to update a region network firewall policy."""
    requests = [self._MakeUpdateRequestTuple(firewall_policy)]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def AddAssociation(self,
                     association=None,
                     firewall_policy=None,
                     replace_existing_association=False,
                     only_generate_request=False):
    """Sends request to add an association."""
    requests = [
        self._MakeAddAssociationRequestTuple(association, firewall_policy,
                                             replace_existing_association)
    ]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def PatchAssociation(
      self,
      association=None,
      firewall_policy=None,
      only_generate_request=False,
  ):
    """Sends request to patch an association."""
    requests = [
        self._MakePatchAssociationRequestTuple(association, firewall_policy)
    ]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def DeleteAssociation(self,
                        firewall_policy=None,
                        name=None,
                        only_generate_request=False):
    """Sends request to delete an association."""
    requests = [self._MakeDeleteAssociationRequestTuple(firewall_policy, name)]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests


class RegionNetworkFirewallPolicyRule(RegionNetworkFirewallPolicy):
  """Abstracts Region Network FirewallPolicy Rule."""

  def __init__(self, ref=None, compute_client=None):
    super(RegionNetworkFirewallPolicyRule, self).__init__(
        ref=ref, compute_client=compute_client)

  def _MakeCreateRuleRequestTuple(self,
                                  firewall_policy=None,
                                  firewall_policy_rule=None):
    return (self._client.regionNetworkFirewallPolicies, 'AddRule',
            self._messages.ComputeRegionNetworkFirewallPoliciesAddRuleRequest(
                firewallPolicy=firewall_policy,
                firewallPolicyRule=firewall_policy_rule,
                project=self.ref.project,
                region=self.ref.region))

  def _MakeDeleteRuleRequestTuple(self, priority=None, firewall_policy=None):
    return (
        self._client.regionNetworkFirewallPolicies, 'RemoveRule',
        self._messages.ComputeRegionNetworkFirewallPoliciesRemoveRuleRequest(
            firewallPolicy=firewall_policy,
            priority=priority,
            project=self.ref.project,
            region=self.ref.region))

  def _MakeDescribeRuleRequestTuple(self, priority=None, firewall_policy=None):
    return (self._client.regionNetworkFirewallPolicies, 'GetRule',
            self._messages.ComputeRegionNetworkFirewallPoliciesGetRuleRequest(
                firewallPolicy=firewall_policy,
                priority=priority,
                project=self.ref.project,
                region=self.ref.region))

  def _MakeUpdateRuleRequestTuple(self,
                                  priority=None,
                                  firewall_policy=None,
                                  firewall_policy_rule=None):
    return (self._client.regionNetworkFirewallPolicies, 'PatchRule',
            self._messages.ComputeRegionNetworkFirewallPoliciesPatchRuleRequest(
                priority=priority,
                firewallPolicy=firewall_policy,
                firewallPolicyRule=firewall_policy_rule,
                project=self.ref.project,
                region=self.ref.region))

  def Create(self,
             firewall_policy=None,
             firewall_policy_rule=None,
             only_generate_request=False):
    """Sends request to create a region network firewall policy rule."""
    requests = [
        self._MakeCreateRuleRequestTuple(
            firewall_policy=firewall_policy,
            firewall_policy_rule=firewall_policy_rule)
    ]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def Delete(self,
             priority=None,
             firewall_policy=None,
             only_generate_request=False):
    """Sends request to delete a region network firewall policy rule."""

    requests = [
        self._MakeDeleteRuleRequestTuple(
            priority=priority, firewall_policy=firewall_policy)
    ]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def Describe(self,
               priority=None,
               firewall_policy=None,
               only_generate_request=False):
    """Sends request to describe a region firewall policy rule."""
    requests = [
        self._MakeDescribeRuleRequestTuple(
            priority=priority, firewall_policy=firewall_policy)
    ]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def Update(self,
             priority=None,
             firewall_policy=None,
             firewall_policy_rule=None,
             only_generate_request=False):
    """Sends request to update a region network firewall policy rule."""

    requests = [
        self._MakeUpdateRuleRequestTuple(
            priority=priority,
            firewall_policy=firewall_policy,
            firewall_policy_rule=firewall_policy_rule)
    ]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests
