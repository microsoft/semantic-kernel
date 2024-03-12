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
"""Create a new CA pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create a new CA Pool.

  ## EXAMPLES

  To create a CA pool in the dev ops tier:

      $ {command} my-pool --location=us-west1 \
          --tier=devops

  To create a CA pool and restrict what it can issue:

      $ {command} my-pool --location=us-west1 \
          --issuance-policy=policy.yaml

  To create a CA pool that doesn't publicly publish CA certificates and CRLs:

      $ {command} my-pool --location=us-west1 \
          --issuance-policy=policy.yaml \
          --no-publish-ca-cert \
          --no-publish-crl
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCaPoolPositionalResourceArg(parser, 'to create')
    flags.AddTierFlag(parser)
    flags.AddPublishingOptionsFlags(parser, use_update_help_text=False)
    flags.AddCaPoolIssuancePolicyFlag(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    client = privateca_base.GetClientInstance('v1')
    messages = privateca_base.GetMessagesModule('v1')

    ca_pool_ref = args.CONCEPTS.ca_pool.Parse()
    issuance_policy = flags.ParseIssuancePolicy(args)
    publishing_options = flags.ParsePublishingOptions(args)
    tier = flags.ParseTierFlag(args)
    labels = labels_util.ParseCreateArgs(args, messages.CaPool.LabelsValue)
    new_ca_pool = messages.CaPool(
        issuancePolicy=issuance_policy,
        publishingOptions=publishing_options,
        tier=tier,
        labels=labels)
    operation = client.projects_locations_caPools.Create(
        messages.PrivatecaProjectsLocationsCaPoolsCreateRequest(
            caPool=new_ca_pool,
            caPoolId=ca_pool_ref.Name(),
            parent=ca_pool_ref.Parent().RelativeName(),
            requestId=request_utils.GenerateRequestId()))

    ca_pool_response = operations.Await(
        operation, 'Creating CA Pool.', api_version='v1')
    ca_pool = operations.GetMessageFromResponse(ca_pool_response,
                                                messages.CaPool)

    log.status.Print('Created CA Pool [{}].'.format(ca_pool.name))
