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

"""`gcloud api-gateway apis create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import apis
from googlecloudsdk.api_lib.api_gateway import operations as ops
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.api_gateway import common_flags
from googlecloudsdk.command_lib.api_gateway import operations_util
from googlecloudsdk.command_lib.api_gateway import resource_args
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a new API."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To create an API, run:

          $ {command} my-api
        """,
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    common_flags.AddDisplayNameArg(parser)
    common_flags.AddManagedServiceFlag(parser)
    labels_util.AddCreateLabelsFlags(parser)
    resource_args.AddApiResourceArg(parser, 'created', positional=True)

  def Run(self, args):
    api_ref = args.CONCEPTS.api.Parse()
    api_client = apis.ApiClient()

    resp = api_client.Create(api_ref,
                             managed_service=args.managed_service,
                             labels=args.labels,
                             display_name=args.display_name)

    return operations_util.PrintOperationResult(
        resp.name,
        ops.OperationsClient(),
        service=api_client.service,
        wait_string='Waiting for API [{}] to be created'.format(api_ref.Name()),
        is_async=args.async_)
