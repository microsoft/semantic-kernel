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
"""API helpers for interacting with IAM."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.command_lib.iam import iam_util


class Client(object):
  """A client for interacting with IAM."""

  def __init__(self, api_version=None):
    self.client = apis.GetClientInstance(api_version)
    self.messages = apis.GetMessagesModule(api_version)

  def Get(self, any_ref):
    """Gets the IamPolicy associated with a resource."""
    return self.client.projects_policy.GetIamPolicy(
        self.messages.BinaryauthorizationProjectsPolicyGetIamPolicyRequest(
            resource=any_ref.RelativeName(),
            options_requestedPolicyVersion=iam_util
            .MAX_LIBRARY_IAM_SUPPORTED_VERSION))

  def Set(self, any_ref, policy):
    """Sets a resource's IamPolicy to the one provided.

    If 'policy' has no etag specified, this will BLINDLY OVERWRITE the IAM
    policy!

    Args:
        any_ref: A resources.Resource naming the resource.
        policy: A protorpc.Message instance of an IamPolicy object.

    Returns:
        The IAM Policy.
    """
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
    return self.client.projects_policy.SetIamPolicy(
        self.messages.BinaryauthorizationProjectsPolicySetIamPolicyRequest(
            resource=any_ref.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy,),
        ))

  def AddBinding(self, any_ref, member, role):
    """Does an atomic Read-Modify-Write, adding the member to the role."""
    policy = self.Get(any_ref)
    iam_util.AddBindingToIamPolicy(self.messages.Binding, policy, member, role)
    return self.Set(any_ref, policy)

  def RemoveBinding(self, any_ref, member, role):
    """Does an atomic Read-Modify-Write, removing the member from the role."""
    policy = self.Get(any_ref)
    iam_util.RemoveBindingFromIamPolicy(policy, member, role)
    return self.Set(any_ref, policy)
