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
"""Bigtable instance API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.command_lib.iam import iam_util


def Upgrade(instance):
  """Upgrade development instance to production.

  Args:
    instance: str instance id to upgrade.

  Returns:
    Operation: the partial update's LRO response.
  """
  client = util.GetAdminClient()
  msgs = util.GetAdminMessages()
  instance_ref = util.GetInstanceRef(instance)

  instance = msgs.Instance(type=msgs.Instance.TypeValueValuesEnum.PRODUCTION)

  return client.projects_instances.PartialUpdateInstance(
      msgs.BigtableadminProjectsInstancesPartialUpdateInstanceRequest(
          instance=instance,
          name=instance_ref.RelativeName(),
          updateMask='type'))


def GetIamPolicy(instance_ref):
  """Get IAM policy for a given instance."""
  client = util.GetAdminClient()
  msgs = util.GetAdminMessages()
  req = msgs.BigtableadminProjectsInstancesGetIamPolicyRequest(
      resource=instance_ref.RelativeName(),
      getIamPolicyRequest=msgs.GetIamPolicyRequest(
          options=msgs.GetPolicyOptions(requestedPolicyVersion=iam_util
                                        .MAX_LIBRARY_IAM_SUPPORTED_VERSION)))
  return client.projects_instances.GetIamPolicy(req)


def SetIamPolicy(instance_ref, policy):
  """Sets the given policy on the instance, overwriting what exists."""
  client = util.GetAdminClient()
  msgs = util.GetAdminMessages()
  policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
  req = msgs.BigtableadminProjectsInstancesSetIamPolicyRequest(
      resource=instance_ref.RelativeName(),
      setIamPolicyRequest=msgs.SetIamPolicyRequest(policy=policy))
  return client.projects_instances.SetIamPolicy(req)
