# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""API library for cloudresourcemanager organizations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.command_lib.iam import iam_util


class Client(object):
  """Client class for cloudresourcemanager organizations API."""

  def __init__(self, client=None, messages=None):
    self.client = client or projects_util.GetClient()
    self.messages = messages or self.client.MESSAGES_MODULE

  def List(self, filter_=None, limit=None, page_size=None):
    req = self.messages.SearchOrganizationsRequest(filter=filter_)
    return list_pager.YieldFromList(
        self.client.organizations, req,
        method='Search',
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='organizations')

  def Get(self, organization_id=None):
    """Returns an Organization resource identified by the specified organization id.

    Args:
      organization_id: organization id

    Returns:
      An instance of Organization
    """
    return self.client.organizations.Get(
        self.client.MESSAGES_MODULE.CloudresourcemanagerOrganizationsGetRequest(
            organizationsId=organization_id))

  def GetByDomain(self, domain):
    """Returns an Organization resource identified by the domain name.

    If no organization is returned, or if more than one organization is
    returned, this method will return None.

    Args:
      domain: A string representing an organizations associated domain.
              e.g. 'example.com'

    Returns:
      An instance of Organization or None if a unique organization cannot be
      determined.
    """
    domain_filter = 'domain:{0}'.format(domain)
    try:
      orgs_list = list(self.List(filter_=domain_filter))
    except exceptions.HttpBadRequestError:
      return None
    if len(orgs_list) == 1:
      return orgs_list[0]
    else:
      return None

  def GetIamPolicy(self, organization_id):
    """Returns IAM policy for a organization.

    Args:
      organization_id: organization id

    Returns:
      IAM policy
    """
    request = self.messages.CloudresourcemanagerOrganizationsGetIamPolicyRequest(
        getIamPolicyRequest=self.messages.GetIamPolicyRequest(
            options=self.messages.GetPolicyOptions(
                requestedPolicyVersion=iam_util
                .MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
        organizationsId=organization_id)

    return self.client.organizations.GetIamPolicy(request)

  def SetIamPolicy(self, organization_id, policy_file):
    """Sets the IAM policy for an organization.

    Args:
      organization_id: organization id.
      policy_file: A JSON or YAML file containing the IAM policy.

    Returns:
      The output from the SetIamPolicy API call.
    """

    policy, update_mask = iam_util.ParsePolicyFileWithUpdateMask(
        policy_file, self.messages.Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    # To preserve the existing set-iam-policy behavior of always overwriting
    # bindings and etag, add bindings and etag to update_mask.
    if 'bindings' not in update_mask:
      update_mask += ',bindings'
    if 'etag' not in update_mask:
      update_mask += ',etag'

    set_iam_policy_request = self.messages.SetIamPolicyRequest(
        policy=policy,
        updateMask=update_mask)

    policy_request = (
        self.messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
            organizationsId=organization_id,
            setIamPolicyRequest=set_iam_policy_request))
    result = self.client.organizations.SetIamPolicy(policy_request)
    iam_util.LogSetIamPolicy(organization_id, 'organization')
    return result

