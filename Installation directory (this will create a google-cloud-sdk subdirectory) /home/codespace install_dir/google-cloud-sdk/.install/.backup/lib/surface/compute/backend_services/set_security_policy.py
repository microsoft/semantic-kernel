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
"""Command for setting the security policy for a backend service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.backend_services import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.command_lib.compute.security_policies import (
    flags as security_policy_flags)


@base.Deprecate(
    is_removed=False,
    warning=('This command is deprecated and will not be promoted to beta. '
             'Please use "gcloud beta backend-services update" instead.'))
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetSecurityPolicy(base.SilentCommand):
  """Set the security policy for a backend service."""

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    cls.SECURITY_POLICY_ARG = (
        security_policy_flags.SecurityPolicyArgumentForTargetResource(
            resource='backend service', required=True))
    cls.SECURITY_POLICY_ARG.AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
        args, holder.resources)

    if not args.security_policy:
      security_policy_ref = None
    else:
      security_policy_ref = self.SECURITY_POLICY_ARG.ResolveAsResource(
          args, holder.resources).SelfLink()

    backend_service = client.BackendService(ref, compute_client=holder.client)

    return backend_service.SetSecurityPolicy(
        security_policy=security_policy_ref)


SetSecurityPolicy.detailed_help = {
    'brief':
        'Set the security policy for a backend service',
    'DESCRIPTION':
        """\

        *{command}* is used to set the security policy for a backend service.
        Setting an empty string will clear the existing security policy.  """,
}
