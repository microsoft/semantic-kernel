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

"""API helpers for interacting with policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis


class Client(object):
  """A client for interacting with policies."""

  def __init__(self, api_version=None):
    self.client = apis.GetClientInstance(api_version)
    self.messages = apis.GetMessagesModule(api_version)

  def Get(self, policy_ref):
    """Get the Policy associated with the current project."""
    return self.client.projects.GetPolicy(
        self.messages.BinaryauthorizationProjectsGetPolicyRequest(
            name=policy_ref.RelativeName(),
        ))

  def Set(self, policy_ref, policy):
    """Set the current project's Policy to the one provided."""
    policy.name = policy_ref.RelativeName()

    return self.client.projects.UpdatePolicy(policy)
