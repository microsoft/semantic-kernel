# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Commands for updating network edge security services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.network_edge_security_services import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.network_edge_security_services import flags
from googlecloudsdk.command_lib.compute.security_policies import (
    flags as security_policy_flags)
from googlecloudsdk.core import resources as resources_exceptions


class Update(base.UpdateCommand):
  r"""Update a network edge security service.

  *{command}* is used to update network edge security services.

  ## EXAMPLES

  To attach a new security policy 'my-policy' to a network edge security service
  with the name 'my-service' in region 'us-central1', run:

    $ {command} my-service \
      --security-policy=my-policy \
      --region=us-central1

  To remove the security policy attached to a network edge security service
  with the name 'my-service' in region 'us-central1', run:

    $ {command} my-service \
      --security-policy="" \
      --region=us-central1
  """

  NETWORK_EDGE_SECURITY_SERVICE_ARG = None
  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command."""
    cls.NETWORK_EDGE_SECURITY_SERVICE_ARG = (
        flags.NetworkEdgeSecurityServiceArgument())
    cls.NETWORK_EDGE_SECURITY_SERVICE_ARG.AddArgument(
        parser, operation_type='update')
    parser.add_argument(
        '--description',
        help=('An optional, textual description for the '
              'network edge security service.'))

    cls.SECURITY_POLICY_ARG = (
        security_policy_flags.SecurityPolicyRegionalArgumentForTargetResource(
            resource='network edge security service'))
    cls.SECURITY_POLICY_ARG.AddArgument(parser)

  def _ValidateArgs(self, args):
    """Validates that at least one field to update is specified.

    Args:
      args: The arguments given to the update command.
    """
    if not (args.IsSpecified('description') or
            args.IsSpecified('security_policy')):
      parameter_names = ['--description', '--security_policy']
      raise exceptions.MinimumArgumentException(
          parameter_names, 'Please specify at least one property to update')

  def Run(self, args):
    self._ValidateArgs(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.NETWORK_EDGE_SECURITY_SERVICE_ARG.ResolveAsResource(
        args, holder.resources)
    network_edge_security_service = client.NetworkEdgeSecurityService(
        ref=ref, compute_client=holder.client)
    existing_network_edge_security_service = (
        network_edge_security_service.Describe()[0])
    description = existing_network_edge_security_service.description
    security_policy = existing_network_edge_security_service.securityPolicy
    update_mask = []
    if args.IsSpecified('description'):
      description = args.description
      update_mask.append('description')
    # Empty string is a valid value.
    if getattr(args, 'security_policy', None) is not None:
      update_mask.append('securityPolicy')
      try:
        security_policy = self.SECURITY_POLICY_ARG.ResolveAsResource(
            args, holder.resources).SelfLink()
      # If security policy is an empty string we should clear the current policy
      except resources_exceptions.InvalidResourceException:
        security_policy = None

    updated_network_edge_security_service = (
        holder.client.messages.NetworkEdgeSecurityService(
            description=description,
            securityPolicy=security_policy,
            fingerprint=existing_network_edge_security_service.fingerprint))

    return network_edge_security_service.Patch(
        network_edge_security_service=updated_network_edge_security_service,
        update_mask=update_mask)
