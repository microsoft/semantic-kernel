# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""CRM API Folders utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions

from googlecloudsdk.api_lib.cloudresourcemanager import organizations
from googlecloudsdk.api_lib.iam import policies as policies_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.resource_manager import exceptions
from googlecloudsdk.core import resources

FOLDERS_API_VERSION = 'v2'


def FoldersClient(api_version=FOLDERS_API_VERSION):
  return apis.GetClientInstance('cloudresourcemanager', api_version)


def FoldersRegistry():
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName('cloudresourcemanager', FOLDERS_API_VERSION)
  return registry


def FoldersService(api_version=FOLDERS_API_VERSION):
  return FoldersClient(api_version).folders


def FoldersMessages(api_version=FOLDERS_API_VERSION):
  return apis.GetMessagesModule('cloudresourcemanager', api_version)


def FolderNameToId(folder_name):
  return folder_name[len('folders/'):]


def FolderIdToName(folder_id):
  return 'folders/{0}'.format(folder_id)


def GetFolder(folder_id):
  return FoldersService().Get(
      FoldersMessages().CloudresourcemanagerFoldersGetRequest(
          foldersId=folder_id))


def GetIamPolicy(folder_id):
  messages = FoldersMessages()
  request = messages.CloudresourcemanagerFoldersGetIamPolicyRequest(
      foldersId=folder_id,
      getIamPolicyRequest=messages.GetIamPolicyRequest(
          options=messages.GetPolicyOptions(requestedPolicyVersion=iam_util.
                                            MAX_LIBRARY_IAM_SUPPORTED_VERSION)))
  return FoldersService().GetIamPolicy(request)


def SetIamPolicy(folder_id, policy, update_mask=None):
  """Calls /google.cloud.resourcemanager.v2.Folders.SetIamPolicy."""
  messages = FoldersMessages()
  set_iam_policy_request = messages.SetIamPolicyRequest(
      policy=policy, updateMask=update_mask)
  request = messages.CloudresourcemanagerFoldersSetIamPolicyRequest(
      foldersId=folder_id, setIamPolicyRequest=set_iam_policy_request)

  return FoldersService().SetIamPolicy(request)


def GetUri(resource):
  """Returns the uri for resource."""
  folder_id = FolderNameToId(resource.name)
  folder_ref = FoldersRegistry().Parse(
      None,
      params={'foldersId': folder_id},
      collection='cloudresourcemanager.folders')
  return folder_ref.SelfLink()


def GetAncestorsIamPolicy(folder_id, include_deny, release_track):
  """Gets IAM policies for given folder and its ancestors."""
  policies = []
  resource = GetFolder(folder_id)

  try:
    while resource is not None:
      resource_id = resource.name.split('/')[1]
      policies.append({
          'type': 'folder',
          'id': resource_id,
          'policy': GetIamPolicy(resource_id),
      })

      if include_deny:
        deny_policies = policies_api.ListDenyPolicies(resource_id, 'folder',
                                                      release_track)
        for deny_policy in deny_policies:
          policies.append({
              'type': 'folder',
              'id': resource_id,
              'policy': deny_policy
          })

      parent_id = resource.parent.split('/')[1]
      if resource.parent.startswith('folder'):
        resource = GetFolder(parent_id)
      else:
        policies.append({
            'type': 'organization',
            'id': parent_id,
            'policy': organizations.Client().GetIamPolicy(parent_id),
        })
        if include_deny:
          deny_policies = policies_api.ListDenyPolicies(parent_id,
                                                        'organization',
                                                        release_track)
          for deny_policy in deny_policies:
            policies.append({
                'type': 'organization',
                'id': resource_id,
                'policy': deny_policy
            })
        resource = None
  except api_exceptions.HttpForbiddenError:
    raise exceptions.AncestorsIamPolicyAccessDeniedError(
        'User is not permitted to access IAM policy for one or more of the'
        ' ancestors')

  return policies
