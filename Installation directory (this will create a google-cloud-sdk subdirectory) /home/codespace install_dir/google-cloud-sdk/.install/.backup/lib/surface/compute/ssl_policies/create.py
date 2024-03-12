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
"""Command to create a new SSL policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.ssl_policies import ssl_policies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_policies import flags


class Create(base.CreateCommand):
  """Create a new Compute Engine SSL policy.

  *{command}* creates a new SSL policy.

  An SSL policy specifies the server-side support for SSL features. An SSL
  policy can be attached to a TargetHttpsProxy or a TargetSslProxy. This affects
  connections between clients and the load balancer. SSL
  policies do not affect the connection between the load balancers and the
  backends. SSL policies are used by Application Load Balancers and proxy
  Network Load Balancers.
  """

  SSL_POLICY_ARG = flags.GetSslPolicyMultiScopeArgument()

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command."""
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    parser.display_info.AddCacheUpdater(flags.SslPoliciesCompleter)
    cls.SSL_POLICY_ARG.AddArgument(parser, operation_type='create')
    flags.GetDescriptionFlag().AddToParser(parser)
    flags.GetProfileFlag(default='COMPATIBLE').AddToParser(parser)
    flags.GetMinTlsVersionFlag(default='1.0').AddToParser(parser)
    flags.GetCustomFeaturesFlag().AddToParser(parser)

  def Run(self, args):
    """Issues the request to create a new SSL policy."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = ssl_policies_utils.SslPolicyHelper(holder)
    ssl_policy_ref = self.SSL_POLICY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    custom_features = args.custom_features if args.IsSpecified(
        'custom_features') else []

    ssl_policy_to_insert = helper.GetSslPolicyForInsert(
        name=ssl_policy_ref.Name(),
        description=args.description,
        profile=args.profile,
        min_tls_version=flags.ParseTlsVersion(args.min_tls_version),
        custom_features=custom_features)
    operation_ref = helper.Create(ssl_policy_ref, ssl_policy_to_insert)
    return helper.WaitForOperation(ssl_policy_ref, operation_ref,
                                   'Creating SSL policy')
