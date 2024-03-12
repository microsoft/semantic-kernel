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
"""API helpers for interacting with platform policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.binauthz import apis


class Client(object):
  """API helpers for interacting with platform policies."""

  def __init__(self, api_version=None):
    self.client = apis.GetClientInstance(api_version)
    self.messages = apis.GetMessagesModule(api_version)

  def Describe(self, policy_ref):
    """Describes a policy.

    Args:
      policy_ref: the resource name of the policy being described.

    Returns:
      The policy resource.
    """
    get_req = (
        self.messages.BinaryauthorizationProjectsPlatformsPoliciesGetRequest(
            name=policy_ref,
        )
    )
    return self.client.projects_platforms_policies.Get(get_req)

  def Update(self, policy_ref, policy):
    """Updates a policy.

    Args:
      policy_ref: the resource name of the policy being updated.
      policy: the contents of the new policy.

    Returns:
      The updated policy resource.
    """
    policy.name = policy_ref
    return self.client.projects_platforms_policies.ReplacePlatformPolicy(policy)

  def List(
      self,
      platform_ref,
      page_size=100,
      limit=None,
  ):
    """Lists policies.

    Args:
      platform_ref: the resource name of the platform whose policies are being
        listed.
      page_size: The number of policies to retrieve in one request (when None,
        use the default size).
      limit: int, The maximum number of policies to yield (when None, unlimted).

    Returns:
      A list of policies for the given platform.
    """
    return list_pager.YieldFromList(
        self.client.projects_platforms_policies,
        self.messages.BinaryauthorizationProjectsPlatformsPoliciesListRequest(
            parent=platform_ref),
        field='platformPolicies',
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size or 100  # Default batch_size.
    )

  def Create(self, policy_resource_name, policy):
    """Creates a policy.

    Args:
      policy_resource_name: Resource object representing the resource name of
        the policy to create.
      policy: The policy to create.

    Returns:
      The policy resource.
    """
    request = (
        self.messages.BinaryauthorizationProjectsPlatformsPoliciesCreateRequest(
            parent=policy_resource_name.Parent().RelativeName(),
            policyId=policy_resource_name.Name(),
            platformPolicy=policy))
    return self.client.projects_platforms_policies.Create(request)

  def Delete(self, policy_ref):
    """Deletes a policy.

    Args:
      policy_ref: the resource name of the policy being deleted.

    Returns:
      The resource name of the deleted policy.
    """
    request = (
        self.messages.BinaryauthorizationProjectsPlatformsPoliciesDeleteRequest(
            name=policy_ref
        )
    )
    return self.client.projects_platforms_policies.Delete(request)

  def Evaluate(self, policy_ref, resource, generate_deploy_attestations=False):
    """Evaluate a policy against a Kubernetes resource.

    Args:
      policy_ref: the resource name of the policy.
      resource: the Kubernetes resource in JSON or YAML form.
      generate_deploy_attestations: whether to sign results or not.

    Returns:
      The result of the evaluation in EvaluateGkePolicyResponse form.
    """
    request = encoding.DictToMessage(
        {
            'evaluateGkePolicyRequest': {
                'resource': resource,
            },
            'name': policy_ref,
        },
        self.messages.BinaryauthorizationProjectsPlatformsGkePoliciesEvaluateRequest,
    )
    if generate_deploy_attestations:
      request.evaluateGkePolicyRequest.attestationMode = (
          self.messages.EvaluateGkePolicyRequest.AttestationModeValueValuesEnum.GENERATE_DEPLOY
      )

    return self.client.projects_platforms_gke_policies.Evaluate(request)
