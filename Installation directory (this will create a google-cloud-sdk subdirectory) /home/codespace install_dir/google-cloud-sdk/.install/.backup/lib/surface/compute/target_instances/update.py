# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command for updating target instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.security_policies import (
    flags as security_policy_flags,
)
from googlecloudsdk.command_lib.compute.target_instances import flags


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Update(base.UpdateCommand):
  r"""Update a Compute Engine target instance.

  *{command}* updates a Compute Engine target instance.

  ## EXAMPLES

  To update the security policy run this:

    $ {command} TARGET_INSTANCE --security-policy='my-policy'
  """

  TARGET_INSTANCE_ARG = None
  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.TARGET_INSTANCE_ARG = flags.TargetInstanceArgument()
    cls.TARGET_INSTANCE_ARG.AddArgument(parser, operation_type='update')
    cls.SECURITY_POLICY_ARG = (
        security_policy_flags.SecurityPolicyRegionalArgumentForTargetResource(
            resource='target instance'
        )
    )
    cls.SECURITY_POLICY_ARG.AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    target_instance_ref = self.TARGET_INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    # Empty string is a valid value.
    if getattr(args, 'security_policy', None) is not None:
      if getattr(args, 'security_policy', None):
        security_policy_ref = self.SECURITY_POLICY_ARG.ResolveAsResource(
            args, holder.resources).SelfLink()
      # If security policy is an empty string we should clear the current policy
      else:
        security_policy_ref = None
      request = client.messages.ComputeTargetInstancesSetSecurityPolicyRequest(
          project=target_instance_ref.project,
          targetInstance=target_instance_ref.Name(),
          zone=target_instance_ref.zone,
          securityPolicyReference=client.messages.SecurityPolicyReference(
              securityPolicy=security_policy_ref
          )
      )
      return client.MakeRequests([(client.apitools_client.targetInstances,
                                   'SetSecurityPolicy', request)])

    parameter_names = ['--security-policy']
    raise exceptions.MinimumArgumentException(
        parameter_names, 'Please specify at least one property to update'
    )
