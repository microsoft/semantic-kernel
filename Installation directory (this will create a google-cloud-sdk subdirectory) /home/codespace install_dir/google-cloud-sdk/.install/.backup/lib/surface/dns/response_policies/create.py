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
"""gcloud dns response-policies create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.command_lib.dns import resource_args
from googlecloudsdk.command_lib.dns import util as command_util
from googlecloudsdk.core import log


def _AddArgsCommon(parser):
  flags.GetResponsePolicyDescriptionArg(required=True).AddToParser(parser)
  flags.GetResponsePolicyNetworksArg().AddToParser(parser)
  flags.GetLocationArg().AddToParser(parser)
  flags.GetResponsePolicyGkeClustersArg().AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Create(base.UpdateCommand):
  r"""Creates a new Cloud DNS response policy.

      This command creates a new Cloud DNS response policy.

      ## EXAMPLES

      To create a new response policy with minimal arguments, run:

        $ {command} myresponsepolicy --description='My new response policy.'
        --networks=''

      To create a new response policy with all optional arguments, run:

        $ {command} myresponsepolicy --description='My new response policy.'
        --networks=network1,network2

      To create a new zonal response policy scoped to a GKE cluster in
        us-central1-a, run (alpha/beta):

        $ {command} beta myresponsepolicy --description='My new response
        policy.'
        --gkeclusters=cluster1 --location=us-central1-a
  """

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    resource_args.AddResponsePolicyResourceArg(
        parser,
        verb='to create',
        api_version=util.GetApiFromTrack(cls.ReleaseTrack()))
    _AddArgsCommon(parser)
    parser.display_info.AddFormat('json')

  def Run(self, args):
    api_version = util.GetApiFromTrackAndArgs(self.ReleaseTrack(), args)
    client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)

    # Get Response Policy
    registry = util.GetRegistry(api_version)
    response_policy_ref = registry.Parse(
        args.response_policies,
        util.GetParamsForRegistry(api_version, args),
        collection='dns.responsePolicies')
    response_policy_name = response_policy_ref.Name()

    response_policy = messages.ResponsePolicy(
        responsePolicyName=response_policy_name)

    if args.IsSpecified('networks') or args.IsSpecified('gkeclusters'):
      if args.networks == ['']:
        args.networks = []
      response_policy.networks = command_util.ParseResponsePolicyNetworks(
          args.networks, response_policy_ref.project, api_version)

      if args.IsSpecified('gkeclusters'):
        gkeclusters = args.gkeclusters
        response_policy.gkeClusters = [
            messages.ResponsePolicyGKECluster(gkeClusterName=name)
            for name in gkeclusters
        ]

    else:
      raise exceptions.RequiredArgumentException(
          '--networks,--gkeclusters',
          ("""A list of networks or GKE clusters must be provided.'
         NOTE: You can provide an empty value ("") for response policies that
          have NO network or GKE clusters binding.
          """))

    if args.IsSpecified('description'):
      response_policy.description = args.description

    create_request = messages.DnsResponsePoliciesCreateRequest(
        responsePolicy=response_policy, project=response_policy_ref.project)

    if api_version == 'v2':
      create_request.location = args.location

    result = client.responsePolicies.Create(create_request)

    log.CreatedResource(response_policy_ref, kind='ResponsePolicy')

    return result
