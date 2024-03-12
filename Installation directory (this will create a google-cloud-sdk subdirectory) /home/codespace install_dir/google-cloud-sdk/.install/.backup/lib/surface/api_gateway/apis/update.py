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

"""`gcloud api-gateway apis update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import apis
from googlecloudsdk.api_lib.api_gateway import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.api_gateway import common_flags
from googlecloudsdk.command_lib.api_gateway import operations_util
from googlecloudsdk.command_lib.api_gateway import resource_args
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update an API Gateway API."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}

          NOTE: Only the display name and labels attributes are mutable on an API.
          """,
      'EXAMPLES':
          """\
          To update the display name of an API, run:

            $ {command} my-api --display-name="New Display Name"

          NOTE: Only the display name and labels attributes are mutable on an API.
          """,
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    common_flags.AddDisplayNameArg(parser)
    labels_util.AddUpdateLabelsFlags(parser)
    resource_args.AddApiResourceArg(parser, 'updated', positional=True)

  def Run(self, args):
    api_ref = args.CONCEPTS.api.Parse()

    api_client = apis.ApiClient()
    api, mask = self.ProcessUpdates(api_client.Get(api_ref), args)

    resp = api_client.Update(api, update_mask=mask)

    return operations_util.PrintOperationResult(
        resp.name,
        operations.OperationsClient(),
        service=api_client.service,
        wait_string='Waiting for API [{}] to be updated'.format(api_ref.Name()),
        is_async=args.async_)

  def ProcessUpdates(self, api, args):
    update_mask = []

    labels_update = labels_util.ProcessUpdateArgsLazy(
        args,
        api.LabelsValue,
        lambda: api.labels)
    if labels_update.needs_update:
      api.labels = labels_update.labels
      update_mask.append('labels')

    if args.display_name:
      api.displayName = args.display_name
      update_mask.append('displayName')

    return api, ','.join(update_mask)
