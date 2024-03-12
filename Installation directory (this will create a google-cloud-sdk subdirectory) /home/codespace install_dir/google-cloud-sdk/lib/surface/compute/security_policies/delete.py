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
"""Command for deleting security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.security_policies import flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete security policies.

  *{command}* deletes Compute Engine security policies. Security
  policies can only be deleted when no other resources (e.g.,
  backend services) refer to them.

  ## EXAMPLES

  To delete a security policy, run:

    $ {command} my-policy
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SECURITY_POLICY_ARG = flags.SecurityPolicyMultiScopeArgument(
        plural=True)
    cls.SECURITY_POLICY_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.GlobalSecurityPoliciesCompleter)

  def Collection(self):
    return 'compute.securityPolicies'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    refs = self.SECURITY_POLICY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    utils.PromptForDeletion(refs)

    requests = []
    for ref in refs:
      security_policy = client.SecurityPolicy(ref, compute_client=holder.client)
      requests.extend(security_policy.Delete(only_generate_request=True))

    return holder.client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(base.DeleteCommand):
  """Delete security policies.

  *{command}* deletes Compute Engine security policies. Security
  policies can only be deleted when no other resources (e.g.,
  backend services) refer to them.

  ## EXAMPLES

  To delete a security policy, run:

    $ {command} my-policy
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SECURITY_POLICY_ARG = flags.SecurityPolicyMultiScopeArgument(
        plural=True)
    cls.SECURITY_POLICY_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.SecurityPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    refs = self.SECURITY_POLICY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    utils.PromptForDeletion(refs)

    requests = []
    for ref in refs:
      security_policy = client.SecurityPolicy(ref, compute_client=holder.client)
      requests.extend(security_policy.Delete(only_generate_request=True))

    return holder.client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(base.DeleteCommand):
  """Delete security policies.

  *{command}* deletes Compute Engine security policies. Security
  policies can only be deleted when no other resources (e.g.,
  backend services) refer to them.

  ## EXAMPLES

  To delete a security policy, run:

    $ {command} my-policy
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SECURITY_POLICY_ARG = flags.SecurityPolicyMultiScopeArgument(
        plural=True)
    cls.SECURITY_POLICY_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.SecurityPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    refs = self.SECURITY_POLICY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    utils.PromptForDeletion(refs)

    requests = []
    for ref in refs:
      security_policy = client.SecurityPolicy(ref, compute_client=holder.client)
      requests.extend(security_policy.Delete(only_generate_request=True))

    return holder.client.MakeRequests(requests)
