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

"""`gcloud api-gateway gateways update` command."""

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
class Update(base.UpdateCommand):
  """Update an API Gateway."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update the display name of a gateway, run:

            $ {command} my-gateway --location=us-central1 --display-name="New Display Name"
          """,
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    common_flags.AddDisplayNameArg(parser)
    labels_util.AddUpdateLabelsFlags(parser)
    resource_args.AddGatewayApiConfigResourceArgs(parser, 'updated',
                                                  api_config_required=False)

  def Run(self, args):
    gateway_ref = args.CONCEPTS.gateway.Parse()

    gateways_client = gateways.GatewayClient()
    gateway, mask = self.ProcessUpdates(gateways_client.Get(gateway_ref), args)

    resp = gateways_client.Update(gateway, update_mask=mask)

    wait = 'Waiting for API Gateway [{}] to be updated'.format(
        gateway_ref.Name())

    return operations_util.PrintOperationResult(
        resp.name,
        operations.OperationsClient(),
        service=gateways_client.service,
        wait_string=wait,
        is_async=args.async_)

  def ProcessUpdates(self, gateway, args):
    api_config_ref = args.CONCEPTS.api_config.Parse()
    update_mask = []

    labels_update = labels_util.ProcessUpdateArgsLazy(
        args,
        gateway.LabelsValue,
        lambda: gateway.labels)
    if labels_update.needs_update:
      gateway.labels = labels_update.labels
      update_mask.append('labels')

    if api_config_ref:
      gateway.apiConfig = api_config_ref.RelativeName()
      update_mask.append('apiConfig')

    if args.display_name:
      gateway.displayName = args.display_name
      update_mask.append('displayName')

    return gateway, ','.join(update_mask)
