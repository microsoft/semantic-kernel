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
"""Common constants and methods for Org Policies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import org_policies


def OrgPoliciesService(args):
  client = org_policies.OrgPoliciesClient()
  if args.project:
    return client.projects
  elif args.organization:
    return client.organizations
  elif args.folder:
    return client.folders
  else:
    return None


def GetOrgPolicyRequest(args):
  """Constructs a resource-dependent GetOrgPolicyRequest.

  Args:
    args: Command line arguments.

  Returns:
    Resource-dependent GetOrgPolicyRequest.
  """
  messages = org_policies.OrgPoliciesMessages()
  request = messages.GetOrgPolicyRequest(
      constraint=org_policies.FormatConstraint(args.id))
  resource_id = GetResource(args)
  if args.project:
    return messages.CloudresourcemanagerProjectsGetOrgPolicyRequest(
        projectsId=resource_id, getOrgPolicyRequest=request)
  elif args.organization:
    return messages.CloudresourcemanagerOrganizationsGetOrgPolicyRequest(
        organizationsId=resource_id, getOrgPolicyRequest=request)
  elif args.folder:
    return messages.CloudresourcemanagerFoldersGetOrgPolicyRequest(
        foldersId=resource_id, getOrgPolicyRequest=request)
  return None


def SetOrgPolicyRequest(args, policy):
  """Constructs a resource-dependent SetOrgPolicyRequest.

  Args:
    args: Command line arguments.
    policy: OrgPolicy for resource-dependent SetOrgPolicyRequest.

  Returns:
    Resource-dependent SetOrgPolicyRequest.
  """
  messages = org_policies.OrgPoliciesMessages()
  resource_id = GetResource(args)
  request = messages.SetOrgPolicyRequest(policy=policy)

  if args.project:
    return messages.CloudresourcemanagerProjectsSetOrgPolicyRequest(
        projectsId=resource_id, setOrgPolicyRequest=request)
  elif args.organization:
    return messages.CloudresourcemanagerOrganizationsSetOrgPolicyRequest(
        organizationsId=resource_id, setOrgPolicyRequest=request)
  elif args.folder:
    return messages.CloudresourcemanagerFoldersSetOrgPolicyRequest(
        foldersId=resource_id, setOrgPolicyRequest=request)
  return None


def GetResource(args):
  if args.project:
    return args.project
  elif args.organization:
    return args.organization
  elif args.folder:
    return args.folder
  else:
    return None
