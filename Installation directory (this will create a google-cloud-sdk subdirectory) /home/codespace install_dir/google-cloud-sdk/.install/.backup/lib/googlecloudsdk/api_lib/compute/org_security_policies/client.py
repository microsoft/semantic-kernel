# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Organization Security policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter

OP_COLLECTION_NAME = 'compute.globalOrganizationOperations'
API_COLLECTION_NAME = 'compute.organizationSecurityPolicies'


class DeletePoller(poller.Poller):

  def GetResult(self, operation):
    # For delete operations, once the operation status is DONE, there is
    # nothing further to fetch.
    return


class OrgSecurityPolicy(object):
  """Abstracts Organization SecurityPolicy resource."""

  def __init__(self,
               ref=None,
               compute_client=None,
               resources=None,
               version='beta'):
    self.ref = ref
    self._compute_client = compute_client
    self._resources = resources
    self._version = version
    self._op_has_project = self._HasProject(OP_COLLECTION_NAME)
    self._api_has_project = self._HasProject(API_COLLECTION_NAME)

  def _HasProject(self, collection):
    collection_info = self._resources.GetCollectionInfo(collection,
                                                        self._version)
    return 'projects' in collection_info.path or 'projects' in collection_info.base_url

  @property
  def _client(self):
    return self._compute_client.apitools_client

  @property
  def _messages(self):
    return self._compute_client.messages

  @property
  def _service(self):
    return self._client.organizationSecurityPolicies

  def _MakeAddAssociationRequestTuple(self, association, security_policy_id,
                                      replace_existing_association):
    return (
        self._client.organizationSecurityPolicies, 'AddAssociation',
        self._messages.ComputeOrganizationSecurityPoliciesAddAssociationRequest(
            securityPolicyAssociation=association,
            securityPolicy=security_policy_id,
            replaceExistingAssociation=replace_existing_association))

  def _MakeDeleteAssociationRequestTuple(self, security_policy_id):
    return (self._client.organizationSecurityPolicies, 'RemoveAssociation',
            self._messages
            .ComputeOrganizationSecurityPoliciesRemoveAssociationRequest(
                name=self.ref.Name(), securityPolicy=security_policy_id))

  def _MakeListAssociationsRequestTuple(self, target_resource):
    return (self._client.organizationSecurityPolicies, 'ListAssociations',
            self._messages
            .ComputeOrganizationSecurityPoliciesListAssociationsRequest(
                targetResource=target_resource))

  def _MakeDeleteRequestTuple(self, sp_id=None):
    return (self._client.organizationSecurityPolicies, 'Delete',
            self._messages.ComputeOrganizationSecurityPoliciesDeleteRequest(
                securityPolicy=sp_id))

  def _MakeUpdateRequestTuple(self, sp_id=None, security_policy=None):
    if sp_id:
      return (self._client.organizationSecurityPolicies, 'Patch',
              self._messages.ComputeOrganizationSecurityPoliciesPatchRequest(
                  securityPolicy=sp_id, securityPolicyResource=security_policy))
    return (self._client.organizationSecurityPolicies, 'Patch',
            self._messages.ComputeOrganizationSecurityPoliciesPatchRequest(
                securityPolicy=self.ref.Name(),
                securityPolicyResource=security_policy))

  def _MakeDescribeRequestTuple(self, sp_id=None):
    if sp_id:
      return (self._client.organizationSecurityPolicies, 'Get',
              self._messages.ComputeOrganizationSecurityPoliciesGetRequest(
                  securityPolicy=sp_id))
    return (self._client.organizationSecurityPolicies, 'Get',
            self._messages.ComputeOrganizationSecurityPoliciesGetRequest(
                securityPolicy=self.ref.Name()))

  def _MakeMoveRequestTuple(self, sp_id=None, parent_id=None):
    return (self._client.organizationSecurityPolicies, 'Move',
            self._messages.ComputeOrganizationSecurityPoliciesMoveRequest(
                securityPolicy=sp_id, parentId=parent_id))

  def _MakeCopyRulesRequestTuple(self,
                                 dest_sp_id=None,
                                 source_security_policy=None):
    return (self._client.organizationSecurityPolicies, 'CopyRules',
            self._messages.ComputeOrganizationSecurityPoliciesCopyRulesRequest(
                securityPolicy=dest_sp_id,
                sourceSecurityPolicy=source_security_policy))

  def _MakeListRequestTuple(self, parent_id):
    return (self._client.organizationSecurityPolicies, 'List',
            self._messages.ComputeOrganizationSecurityPoliciesListRequest(
                parentId=parent_id))

  def _MakeCreateRequestTuple(self, security_policy, parent_id):
    return (self._client.organizationSecurityPolicies, 'Insert',
            self._messages.ComputeOrganizationSecurityPoliciesInsertRequest(
                parentId=parent_id, securityPolicy=security_policy))

  def AddAssociation(self,
                     association=None,
                     security_policy_id=None,
                     replace_existing_association=False,
                     batch_mode=False,
                     only_generate_request=False):
    """Sends request to add an association."""

    if batch_mode:
      requests = [
          self._MakeAddAssociationRequestTuple(association, security_policy_id,
                                               replace_existing_association)
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.AddAssociation(
        self._MakeAddAssociationRequestTuple(association, security_policy_id,
                                             replace_existing_association)[2])
    return self.WaitOperation(
        op_res, message='Add association of the organization Security Policy.')

  def DeleteAssociation(self,
                        security_policy_id=None,
                        batch_mode=False,
                        only_generate_request=False):
    """Sends request to delete an association."""

    if batch_mode:
      requests = [self._MakeDeleteAssociationRequestTuple(security_policy_id)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.RemoveAssociation(
        self._MakeDeleteAssociationRequestTuple(security_policy_id)[2])
    return self.WaitOperation(
        op_res,
        message='Delete association of the organization Security Policy.')

  def ListAssociations(self,
                       target_resource=None,
                       batch_mode=False,
                       only_generate_request=False):
    """Sends request to list all the associations."""

    if batch_mode:
      requests = [self._MakeListAssociationsRequestTuple(target_resource)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    return [
        self._service.ListAssociations(
            self._MakeListAssociationsRequestTuple(target_resource)[2])
    ]

  def Delete(self, sp_id=None, batch_mode=False, only_generate_request=False):
    """Sends request to delete a security policy."""

    if batch_mode:
      requests = [self._MakeDeleteRequestTuple(sp_id=sp_id)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.Delete(self._MakeDeleteRequestTuple(sp_id=sp_id)[2])
    operation_poller = DeletePoller(self._service, self.ref)
    return self.WaitOperation(
        op_res,
        operation_poller=operation_poller,
        message='Delete the organization Security Policy.')

  def WaitOperation(self, operation, operation_poller=None, message=None):
    if not operation_poller:
      operation_poller = poller.Poller(
          self._service, self.ref, has_project=self._api_has_project)
    if self._op_has_project and 'projects' not in operation.selfLink:
      operation.selfLink = operation.selfLink.replace('locations',
                                                      'projects/locations')
    operation_ref = self._resources.Parse(
        operation.selfLink, collection=OP_COLLECTION_NAME)
    return waiter.WaitFor(operation_poller, operation_ref, message)

  def Update(self,
             sp_id=None,
             only_generate_request=False,
             security_policy=None,
             batch_mode=False):
    """Sends request to update a security policy."""

    if batch_mode:
      requests = [
          self._MakeUpdateRequestTuple(
              sp_id=sp_id, security_policy=security_policy)
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.Patch(
        self._MakeUpdateRequestTuple(
            sp_id=sp_id, security_policy=security_policy)[2])
    return self.WaitOperation(
        op_res, message='Update the organization Security Policy.')

  def Move(self,
           only_generate_request=False,
           sp_id=None,
           parent_id=None,
           batch_mode=False):
    """Sends request to move the security policy to anther parent."""
    if batch_mode:
      requests = [self._MakeMoveRequestTuple(sp_id=sp_id, parent_id=parent_id)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.Move(
        self._MakeMoveRequestTuple(sp_id=sp_id, parent_id=parent_id)[2])
    return self.WaitOperation(
        op_res, message='Move the organization Security Policy.')

  def CopyRules(self,
                only_generate_request=False,
                dest_sp_id=None,
                source_security_policy=None,
                batch_mode=False):
    """Sends request to copy all the rules from another security policy."""

    if batch_mode:
      requests = [
          self._MakeCopyRulesRequestTuple(
              dest_sp_id=dest_sp_id,
              source_security_policy=source_security_policy)
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.CopyRules(
        self._MakeCopyRulesRequestTuple(
            dest_sp_id=dest_sp_id,
            source_security_policy=source_security_policy)[2])
    return self.WaitOperation(
        op_res, message='Copy rules for the organization Security Policy.')

  def Describe(self, sp_id=None, batch_mode=False, only_generate_request=False):
    """Sends request to describe a security policy."""

    if batch_mode:
      requests = [self._MakeDescribeRequestTuple(sp_id=sp_id)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    return [self._service.Get(self._MakeDescribeRequestTuple(sp_id=sp_id)[2])]

  def List(self, parent_id=None, batch_mode=False, only_generate_request=False):
    """Sends request to list all the security policies."""

    if batch_mode:
      requests = [self._MakeListRequestTuple(parent_id)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    return [self._service.List(self._MakeListRequestTuple(parent_id)[2])]

  def Create(self,
             security_policy=None,
             parent_id=None,
             batch_mode=False,
             only_generate_request=False):
    """Sends request to create a security policy."""

    if batch_mode:
      requests = [self._MakeCreateRequestTuple(security_policy, parent_id)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.Insert(
        self._MakeCreateRequestTuple(security_policy, parent_id)[2])
    return self.WaitOperation(
        op_res, message='Create the organization Security Policy.')


class OrgSecurityPolicyRule(OrgSecurityPolicy):
  """Abstracts Organization SecurityPolicy Rule."""

  def __init__(self,
               ref=None,
               compute_client=None,
               resources=None,
               version='beta'):
    super(OrgSecurityPolicyRule, self).__init__(
        ref=ref,
        compute_client=compute_client,
        resources=resources,
        version=version)

  def _MakeCreateRuleRequestTuple(self,
                                  security_policy=None,
                                  security_policy_rule=None):
    return (self._client.organizationSecurityPolicies, 'AddRule',
            self._messages.ComputeOrganizationSecurityPoliciesAddRuleRequest(
                securityPolicy=security_policy,
                securityPolicyRule=security_policy_rule))

  def _MakeDeleteRuleRequestTuple(self, priority=None, security_policy=None):
    return (self._client.organizationSecurityPolicies, 'RemoveRule',
            self._messages.ComputeOrganizationSecurityPoliciesRemoveRuleRequest(
                securityPolicy=security_policy, priority=priority))

  def _MakeDescribeRuleRequestTuple(self, priority=None, security_policy=None):
    return (self._client.organizationSecurityPolicies, 'GetRule',
            self._messages.ComputeOrganizationSecurityPoliciesGetRuleRequest(
                securityPolicy=security_policy, priority=priority))

  def _MakeUpdateRuleRequestTuple(self,
                                  priority=None,
                                  security_policy=None,
                                  security_policy_rule=None):
    return (self._client.organizationSecurityPolicies, 'PatchRule',
            self._messages.ComputeOrganizationSecurityPoliciesPatchRuleRequest(
                priority=priority,
                securityPolicy=security_policy,
                securityPolicyRule=security_policy_rule))

  def Create(self,
             security_policy=None,
             security_policy_rule=None,
             batch_mode=False,
             only_generate_request=False):
    """Sends request to create a security policy rule."""

    if batch_mode:
      requests = [
          self._MakeCreateRuleRequestTuple(
              security_policy=security_policy,
              security_policy_rule=security_policy_rule)
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.AddRule(
        self._MakeCreateRuleRequestTuple(
            security_policy=security_policy,
            security_policy_rule=security_policy_rule)[2])
    return self.WaitOperation(
        op_res, message='Add a rule of the organization Security Policy.')

  def Delete(self,
             priority=None,
             security_policy_id=None,
             batch_mode=False,
             only_generate_request=False):
    """Sends request to delete a security policy rule."""

    if batch_mode:
      requests = [
          self._MakeDeleteRuleRequestTuple(
              priority=priority, security_policy=security_policy_id)
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.RemoveRule(
        self._MakeDeleteRuleRequestTuple(
            priority=priority, security_policy=security_policy_id)[2])
    return self.WaitOperation(
        op_res, message='Delete a rule of the organization Security Policy.')

  def Describe(self,
               priority=None,
               security_policy_id=None,
               batch_mode=False,
               only_generate_request=False):
    """Sends request to describe a security policy rule."""

    if batch_mode:
      requests = [
          self._MakeDescribeRuleRequestTuple(
              priority=priority, security_policy=security_policy_id)
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    return self._service.GetRule(
        self._MakeDescribeRuleRequestTuple(
            priority=priority, security_policy=security_policy_id)[2])

  def Update(self,
             priority=None,
             security_policy=None,
             security_policy_rule=None,
             batch_mode=False,
             only_generate_request=False):
    """Sends request to update a security policy rule."""

    if batch_mode:
      requests = [
          self._MakeUpdateRuleRequestTuple(
              priority=priority,
              security_policy=security_policy,
              security_policy_rule=security_policy_rule)
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.PatchRule(
        self._MakeUpdateRuleRequestTuple(
            priority=priority,
            security_policy=security_policy,
            security_policy_rule=security_policy_rule)[2])
    return self.WaitOperation(
        op_res, message='Update a rule of the organization Security Policy.')
