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
"""Command to update SSL policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.ssl_policies import ssl_policies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_policies import flags


class Update(base.UpdateCommand):
  """Update a Compute Engine SSL policy.

  *{command}* is used to update SSL policies.

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
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.SSL_POLICY_ARG = flags.GetSslPolicyMultiScopeArgument()
    cls.SSL_POLICY_ARG.AddArgument(parser, operation_type='patch')
    flags.GetProfileFlag().AddToParser(parser)
    flags.GetMinTlsVersionFlag().AddToParser(parser)
    flags.GetCustomFeaturesFlag().AddToParser(parser)

  def Run(self, args):
    """Issues the request to update a SSL policy."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = ssl_policies_utils.SslPolicyHelper(holder)
    ssl_policy_ref = self.SSL_POLICY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)

    include_custom_features, custom_features = Update._GetCustomFeatures(args)
    existing_ssl_policy = helper.Describe(ssl_policy_ref)

    patch_ssl_policy = helper.GetSslPolicyForPatch(
        fingerprint=existing_ssl_policy.fingerprint,
        profile=args.profile,
        min_tls_version=flags.ParseTlsVersion(args.min_tls_version),
        custom_features=custom_features)
    operation_ref = helper.Patch(
        ssl_policy_ref, patch_ssl_policy, include_custom_features and
        not custom_features)
    return helper.WaitForOperation(ssl_policy_ref, operation_ref,
                                   'Updating SSL policy')

  @staticmethod
  def _GetCustomFeatures(args):
    """Returns the custom features specified on the command line.

    Args:
      args: The arguments passed to this command from the command line.

    Returns:
      A tuple. The first element in the tuple indicates whether custom
      features must be included in the request or not. The second element in
      the tuple specifies the list of custom features.
    """
    # Clear custom_features if profile is not CUSTOM
    if args.IsSpecified('profile') and args.profile != 'CUSTOM':
      # pylint: disable=g-explicit-length-test
      if args.IsSpecified('custom_features') and len(args.custom_features) > 0:
        # If user specifies custom_features when profile is not CUSTOM, raise
        # an error right away.
        raise exceptions.InvalidArgumentException(
            '--custom-features', 'Custom features cannot be specified '
            'when using non-CUSTOM profiles.')
      # When switching to non-CUSTOM profile, always clear the custom_features
      # explicitly in the patch request.
      return (True, [])
    elif args.IsSpecified('custom_features'):
      # User specified custom features will be part of the patch request.
      return (True, args.custom_features)
    else:
      # Custom features will not be sent as part of the patch request.
      return (False, [])
