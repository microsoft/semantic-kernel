# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Client for interaction with Gateway CRUD on API Gateway API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import types

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.iam import iam_util


def GetClientInstance(version='v1', no_http=False):
  return apis.GetClientInstance('apigateway', version, no_http=no_http)


def GetMessagesModule(version='v1'):
  return apis.GetMessagesModule('apigateway', version)


class BaseClient(object):
  """Base for building API Clients."""

  def __init__(self, client=None, message_base=None, service_name=None):
    self.client = client or GetClientInstance()
    self.messages = self.client.MESSAGES_MODULE
    self.service = getattr(self.client, service_name, None)

    # Define standard request types if they exist for the base message
    self.get_request = getattr(self.messages, message_base + 'GetRequest', None)
    self.create_request = getattr(self.messages,
                                  message_base + 'CreateRequest',
                                  None)
    self.list_request = getattr(self.messages,
                                message_base + 'ListRequest',
                                None)
    self.patch_request = getattr(self.messages,
                                 message_base + 'PatchRequest',
                                 None)
    self.delete_request = getattr(self.messages,
                                  message_base + 'DeleteRequest',
                                  None)

    # Define IAM request types if they exist for the base message
    self.get_iam_policy_request = getattr(self.messages,
                                          message_base + 'GetIamPolicyRequest',
                                          None)
    self.set_iam_policy_request = getattr(self.messages,
                                          message_base + 'SetIamPolicyRequest',
                                          None)

  def DefineGet(self):
    """Defines basic get function on an assigned class."""
    def Get(self, object_ref):
      """Gets an object.

      Args:
        self: The self of the class this is set on.
        object_ref: Resource, resource reference for object to get.

      Returns:
        The object requested.
      """
      req = self.get_request(name=object_ref.RelativeName())

      return self.service.Get(req)

    # Bind the function to the method and set the attribute
    setattr(self, 'Get', types.MethodType(Get, self))

  def DefineDelete(self):
    """Defines basic delete function on an assigned class."""
    def Delete(self, object_ref):
      """Deletes a given object given an object name.

      Args:
        self: The self of the class this is set on.
        object_ref: Resource, resource reference for object to delete.

      Returns:
        Long running operation.
      """
      req = self.delete_request(name=object_ref.RelativeName())

      return self.service.Delete(req)

    # Bind the function to the method and set the attribute
    setattr(self, 'Delete', types.MethodType(Delete, self))

  def DefineList(self, field_name, is_operations=False):
    """Defines the List functionality on the calling class.

    Args:
      field_name: The name of the field on the list response to list
      is_operations: Operations have a slightly altered message structure, set
                     to true in operations client
    """
    def List(self, parent_name, filters=None, limit=None, page_size=None,
             sort_by=None):
      """Lists the objects under a given parent.

      Args:
        self: the self object function will be bound to.
        parent_name: Resource name of the parent to list under.
        filters: Filters to be applied to results (optional).
        limit: Limit to the number of results per page (optional).
        page_size: the number of results per page (optional).
        sort_by: Instructions about how to sort the results (optional).

      Returns:
        List Pager.
      """
      if is_operations:
        req = self.list_request(filter=filters, name=parent_name)

      else:
        req = self.list_request(filter=filters, parent=parent_name,
                                orderBy=sort_by)

      return list_pager.YieldFromList(
          self.service,
          req,
          limit=limit,
          batch_size_attribute='pageSize',
          batch_size=page_size,
          field=field_name)

    # Bind the function to the method and set the attribute
    setattr(self, 'List', types.MethodType(List, self))

  def DefineUpdate(self, update_field_name):
    """Defines the Update functionality on the calling class.

    Args:
      update_field_name: the field on the patch_request to assign updated object
                         to
    """
    def Update(self, updating_object, update_mask=None):
      """Updates an object.

      Args:
        self: The self of the class this is set on.
        updating_object: Object which is being updated.
        update_mask: A string saying which fields have been updated.

      Returns:
        Long running operation.
      """
      req = self.patch_request(name=updating_object.name,
                               updateMask=update_mask)
      setattr(req, update_field_name, updating_object)

      return self.service.Patch(req)

    # Bind the function to the method and set the attribute
    setattr(self, 'Update', types.MethodType(Update, self))

  def DefineIamPolicyFunctions(self):
    """Defines all of the IAM functionality on the calling class."""
    def GetIamPolicy(self, object_ref):
      """Gets an IAM Policy on an object.

      Args:
        self: The self of the class this is set on.
        object_ref: Resource, reference for object IAM policy belongs to.

      Returns:
        The IAM policy.
      """
      req = self.get_iam_policy_request(resource=object_ref.RelativeName())

      return self.service.GetIamPolicy(req)

    def SetIamPolicy(self, object_ref, policy, update_mask=None):
      """Sets an IAM Policy on an object.

      Args:
        self: The self of the class this is set on.
        object_ref: Resource, reference for object IAM policy belongs to.
        policy: the policy to be set.
        update_mask: fields being update on the IAM policy.

      Returns:
        The IAM policy.
      """
      policy_request = self.messages.ApigatewaySetIamPolicyRequest(
          policy=policy,
          updateMask=update_mask)
      req = self.set_iam_policy_request(
          apigatewaySetIamPolicyRequest=policy_request,
          resource=object_ref.RelativeName())
      return self.service.SetIamPolicy(req)

    def AddIamPolicyBinding(self, object_ref, member, role):
      """Adds an IAM role to a member on an object.

      Args:
        self: The self of the class this is set on.
        object_ref: Resource, reference for object IAM policy belongs to.
        member: the member the binding is being added to.
        role: the role which to bind to the member.

      Returns:
        The IAM policy.
      """
      policy = self.GetIamPolicy(object_ref)
      iam_util.AddBindingToIamPolicy(self.messages.ApigatewayBinding, policy,
                                     member, role)
      return self.SetIamPolicy(object_ref, policy, 'bindings,etag')

    def RemoveIamPolicyBinding(self, object_ref, member, role):
      """Adds an IAM role for a member on an object.

      Args:
        self: The self of the class this is set on
        object_ref: Resource, reference for object IAM policy belongs to
        member: the member the binding is removed for
        role: the role which is being removed from the member

      Returns:
        The IAM policy
      """
      policy = self.GetIamPolicy(object_ref)
      iam_util.RemoveBindingFromIamPolicy(policy, member, role)
      return self.SetIamPolicy(object_ref, policy, 'bindings,etag')

    # Bind the function to the method and set the attribute
    setattr(self, 'GetIamPolicy', types.MethodType(GetIamPolicy, self))
    setattr(self, 'SetIamPolicy', types.MethodType(SetIamPolicy, self))
    setattr(self, 'AddIamPolicyBinding', types.MethodType(AddIamPolicyBinding,
                                                          self))
    setattr(self, 'RemoveIamPolicyBinding', types.MethodType(
        RemoveIamPolicyBinding, self))
