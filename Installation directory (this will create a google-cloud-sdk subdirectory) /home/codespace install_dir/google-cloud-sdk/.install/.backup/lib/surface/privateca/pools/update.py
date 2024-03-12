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
"""Update a CA pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.privateca import update_utils
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update an existing  CA Pool.

  ## EXAMPLES
    To update labels on a CA pool:

      $ {command} my-pool \
        --location=us-west1 \
        --update-labels=foo=bar

    To disable publishing CRLs on a CA pool:

      $ {command} my-pool \
        --location=us-west1 \
        --no-publish-crl
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCaPoolPositionalResourceArg(
        parser, 'to update')
    flags.AddPublishingOptionsFlags(parser, use_update_help_text=True)
    flags.AddCaPoolIssuancePolicyFlag(parser)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    client = privateca_base.GetClientInstance('v1')
    messages = privateca_base.GetMessagesModule('v1')

    ca_pool_ref = args.CONCEPTS.ca_pool.Parse()

    current_ca_pool = client.projects_locations_caPools.Get(
        messages.PrivatecaProjectsLocationsCaPoolsGetRequest(
            name=ca_pool_ref.RelativeName()))

    pool_to_update, update_mask = update_utils.UpdateCaPoolFromArgs(
        args, current_ca_pool.labels)

    operation = client.projects_locations_caPools.Patch(
        messages.PrivatecaProjectsLocationsCaPoolsPatchRequest(
            name=ca_pool_ref.RelativeName(),
            caPool=pool_to_update,
            updateMask=','.join(update_mask),
            requestId=request_utils.GenerateRequestId()))

    return operations.Await(operation, 'Updating CA pool.', api_version='v1')
