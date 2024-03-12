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
"""Command for creating network edge security services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.network_edge_security_services import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_edge_security_services import flags
from googlecloudsdk.command_lib.compute.security_policies import (
    flags as security_policy_flags)


class Create(base.CreateCommand):
  r"""Create a Compute Engine network edge security service.

  *{command}* is used to create network edge security services.

  ## EXAMPLES

  To create a network edge security service with the name 'my-service' in region
  'us-central1', run:

    $ {command} my-service \
      --region=us-central1

  To create a network edge security service with the name 'my-service' with
  security policy 'my-policy' attached in region 'us-central1', run:

    $ {command} my-service \
      --security-policy=my-policy \
      --region=us-central1
  """

  NETWORK_EDGE_SECURITY_SERVICE_ARG = None
  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_EDGE_SECURITY_SERVICE_ARG = (
        flags.NetworkEdgeSecurityServiceArgument())
    cls.NETWORK_EDGE_SECURITY_SERVICE_ARG.AddArgument(
        parser, operation_type='create')
    cls.SECURITY_POLICY_ARG = (
        security_policy_flags.SecurityPolicyRegionalArgumentForTargetResource(
            resource='network edge security service'))
    cls.SECURITY_POLICY_ARG.AddArgument(parser)

    parser.add_argument(
        '--description',
        help=('An optional, textual description for the network edge security '
              'service.'))

    parser.display_info.AddCacheUpdater(
        flags.NetworkEdgeSecurityServicesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.NETWORK_EDGE_SECURITY_SERVICE_ARG.ResolveAsResource(
        args, holder.resources)
    network_edge_security_service = client.NetworkEdgeSecurityService(
        ref, compute_client=holder.client)

    resource = holder.client.messages.NetworkEdgeSecurityService(
        name=ref.Name(), description=args.description)
    if args.IsSpecified('security_policy'):
      security_policy_ref = self.SECURITY_POLICY_ARG.ResolveAsResource(
          args, holder.resources).SelfLink()
      resource.securityPolicy = security_policy_ref

    return network_edge_security_service.Create(resource)

