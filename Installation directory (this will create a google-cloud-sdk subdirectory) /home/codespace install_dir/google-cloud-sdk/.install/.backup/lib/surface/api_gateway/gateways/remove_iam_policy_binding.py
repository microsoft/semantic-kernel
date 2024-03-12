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
"""Command to add IAM policy binding for a model."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import gateways
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.api_gateway import common_flags
from googlecloudsdk.command_lib.api_gateway import resource_args
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class RemoveIamPolicyBinding(base.Command):
  """Remove IAM policy binding from a gateway."""

  detailed_help = {
      'EXAMPLES':
          """\
          To remove an IAM policy binding for the role of 'roles/editor' for the
          user 'test-user@gmail.com' on Gateway 'my-gateway' in us-central1, run:

            $ {command} my-gateway --location='us-central1'
                --member='user:test-user@gmail.com'
                --role='roles/editor'
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddGatewayResourceArg(parser,
                                        'IAM policy binding will be added to',
                                        positional=True)
    iam_util.AddArgsForRemoveIamPolicyBinding(
        parser,
        common_flags.GatewayIamRolesCompleter)

  def Run(self, args):
    gateway_ref = args.CONCEPTS.gateway.Parse()

    return gateways.GatewayClient().RemoveIamPolicyBinding(
        gateway_ref, args.member, args.role)
