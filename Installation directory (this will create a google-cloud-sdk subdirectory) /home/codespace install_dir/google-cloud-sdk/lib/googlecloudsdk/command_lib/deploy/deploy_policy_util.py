# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Utilities for the cloud deploy deploy policy resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import deploy_policy
from googlecloudsdk.core import resources


def PatchDeployPolicy(resource):
  """Patches a deploy policy resource.

  Args:
    resource: apitools.base.protorpclite.messages.Message, deploy policy
      message.

  Returns:
    The operation message
  """
  return deploy_policy.DeployPoliciesClient().Patch(resource)


def DeleteDeployPolicy(name):
  """Deletes a deploy policy resource.

  Args:
    name: str, deploy policy name.

  Returns:
    The operation message
  """
  return deploy_policy.DeployPoliciesClient().Delete(name)


def CreateDeployPolicyNamesFromIDs(pipeline_ref, deploy_policy_ids):
  """Creates deploy policy canonical resource names from ids.

  Args:
    pipeline_ref: pipeline resource reference.
    deploy_policy_ids: list of deploy policy ids (e.g. ['deploy-policy-1',
      'deploy-policy-2'])

  Returns:
    A list of deploy policy canonical resource names.
  """
  pipeline_dict = pipeline_ref.AsDict()
  project_id = pipeline_dict.get('projectsId')
  location_id = pipeline_dict.get('locationsId')

  policies = []
  if deploy_policy_ids:
    for policy in deploy_policy_ids:
      deploy_policy_resource_ref = resources.REGISTRY.Parse(
          policy,
          collection='clouddeploy.projects.locations.deployPolicies',
          params={
              'projectsId': project_id,
              'locationsId': location_id,
              'deployPoliciesId': policy,
          },
      )
      policies.append(deploy_policy_resource_ref.RelativeName())
  return policies
