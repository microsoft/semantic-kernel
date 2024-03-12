# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""Command for getting IAM policies for gateways."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import gateways
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.api_gateway import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for a gateway."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To print the IAM policy for a given gateway, run:

            $ {command} my-gateway --location=us-central1
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddGatewayResourceArg(parser, 'for which to get IAM policy',
                                        positional=True)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    gateway_ref = args.CONCEPTS.gateway.Parse()

    return gateways.GatewayClient().GetIamPolicy(gateway_ref)
