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
"""Command to describe SSL policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.ssl_policies import ssl_policies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_policies import flags


class Describe(base.DescribeCommand):
  """Describe a Compute Engine ssl policy.

  *{command}* is used to display all data associated with a Compute Engine
  SSL policy in a project.

  An SSL policy specifies the server-side support for SSL features. An SSL
  policy can be attached to a TargetHttpsProxy or a TargetSslProxy. This affects
  connections between clients and the load balancer. SSL
  policies do not affect the connection between the load balancers and the
  backends. SSL policies are used by Application Load Balancers and proxy
  Network Load Balancers.
  """

  SSL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SSL_POLICY_ARG = flags.GetSslPolicyMultiScopeArgument()
    cls.SSL_POLICY_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    """Issues the request to describe a SSL policy."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = ssl_policies_utils.SslPolicyHelper(holder)
    ref = self.SSL_POLICY_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
        default_scope=compute_scope.ScopeEnum.GLOBAL)
    return helper.Describe(ref)
