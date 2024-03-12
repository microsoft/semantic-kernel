# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""`gcloud api-gateway gateways create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import gateways
from googlecloudsdk.api_lib.api_gateway import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.api_gateway import common_flags
from googlecloudsdk.command_lib.api_gateway import operations_util
from googlecloudsdk.command_lib.api_gateway import resource_args
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a new gateway."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To create a gateway in 'us-central1' run:

          $ {command} my-gateway --api=my-api --api-config=my-config --location=us-central1
        """,
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    common_flags.AddDisplayNameArg(parser)
    labels_util.AddCreateLabelsFlags(parser)
    resource_args.AddGatewayApiConfigResourceArgs(parser, 'created')

  def Run(self, args):
    gateway_ref = args.CONCEPTS.gateway.Parse()
    api_config_ref = args.CONCEPTS.api_config.Parse()

    gateways_client = gateways.GatewayClient()
    resp = gateways_client.Create(gateway_ref,
                                  api_config_ref,
                                  display_name=args.display_name,
                                  labels=args.labels)

    wait = 'Waiting for API Gateway [{}] to be created with [{}] config'.format(
        gateway_ref.Name(), api_config_ref.RelativeName())

    return operations_util.PrintOperationResult(
        resp.name,
        operations.OperationsClient(),
        service=gateways_client.service,
        wait_string=wait,
        is_async=args.async_)
