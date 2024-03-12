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

"""Utilities for IAM commands to call IAM APIs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.iam import iam_util


def GetClientAndMessages():
  client = apis.GetClientInstance('iam', 'v1')
  return client, client.MESSAGES_MODULE


def GetIamCredentialsClientAndMessages():
  client = apis.GetClientInstance('iamcredentials', 'v1')
  return client, client.MESSAGES_MODULE


def GetTestablePermissions(iam_client, messages, resource):
  """Returns the testable permissions for a resource.

  Args:
    iam_client: The iam client.
    messages: The iam messages.
    resource: Resource reference.

  Returns:
    List of permissions.
  """
  return list_pager.YieldFromList(
      iam_client.permissions,
      messages.QueryTestablePermissionsRequest(
          fullResourceName=iam_util.GetFullResourceName(resource),
          pageSize=1000),
      batch_size=1000,
      method='QueryTestablePermissions',
      field='permissions',
      batch_size_attribute='pageSize')


class PermissionsHelper(object):
  """Get different kinds of permissions list from permissions provided.

  Attributes:
    messages: The iam messages.
    source_permissions: A list of permissions to inspect.
    testable_permissions_map: A dict maps from permissions name string to
        Permission message provided by the API.
  """

  def __init__(self, iam_client, messages, resource, permissions):
    """Create a PermissionsHelper object.

    To get the testable permissions for the given resource and store as a dict.

    Args:
      iam_client: The iam client.
      messages: The iam messages.
      resource: Resource reference for the project/organization whose
      permissions are being inspected.
      permissions: A list of permissions to inspect.
    """

    self.messages = messages
    self.source_permissions = permissions
    self.testable_permissions_map = {}
    if permissions:
      for permission in GetTestablePermissions(iam_client, messages, resource):
        self.testable_permissions_map[permission.name] = permission

  def GetTestingPermissions(self):
    """Returns the TESTING permissions among the permissions provided."""
    testing_permissions = []
    for permission in self.source_permissions:
      if (permission in self.testable_permissions_map and
          (self.testable_permissions_map[permission].customRolesSupportLevel ==
           self.messages.Permission.CustomRolesSupportLevelValueValuesEnum.
           TESTING)):
        testing_permissions.append(permission)
    return testing_permissions

  def GetValidPermissions(self):
    """Returns the valid permissions among the permissions provided."""
    valid_permissions = []
    for permission in self.source_permissions:
      if (permission in self.testable_permissions_map and
          (self.testable_permissions_map[permission].customRolesSupportLevel !=
           self.messages.Permission.CustomRolesSupportLevelValueValuesEnum.
           NOT_SUPPORTED)):
        valid_permissions.append(permission)
    return valid_permissions

  def GetNotSupportedPermissions(self):
    """Returns the not supported permissions among the permissions provided."""
    not_supported_permissions = []
    for permission in self.source_permissions:
      if (permission in self.testable_permissions_map and
          (self.testable_permissions_map[permission].customRolesSupportLevel ==
           self.messages.Permission.CustomRolesSupportLevelValueValuesEnum.
           NOT_SUPPORTED)):
        not_supported_permissions.append(permission)
    return not_supported_permissions

  def GetApiDisabledPermissons(self):
    """Returns the API disabled permissions among the permissions provided."""
    api_disabled_permissions = []
    for permission in self.source_permissions:
      if (permission in self.testable_permissions_map and
          (self.testable_permissions_map[permission].customRolesSupportLevel !=
           self.messages.Permission.CustomRolesSupportLevelValueValuesEnum.
           NOT_SUPPORTED) and
          self.testable_permissions_map[permission].apiDisabled):
        api_disabled_permissions.append(permission)
    return api_disabled_permissions

  def GetNotApplicablePermissions(self):
    """Returns the not applicable permissions among the permissions provided."""
    not_applicable_permissions = []
    for permission in self.source_permissions:
      if permission not in self.testable_permissions_map:
        not_applicable_permissions.append(permission)
    return not_applicable_permissions
