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
"""gcloud dns response-policies update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.command_lib.dns import resource_args
from googlecloudsdk.command_lib.dns import util as command_util
from googlecloudsdk.core import log


def _AddArgsCommon(parser):
  flags.GetResponsePolicyDescriptionArg().AddToParser(parser)
  flags.GetResponsePolicyNetworksArg().AddToParser(parser)
  flags.GetResponsePolicyGkeClustersArg().AddToParser(parser)
  flags.GetLocationArg().AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  r"""Updates a Cloud DNS response policy.

      This command updates a Cloud DNS response policy.

      ## EXAMPLES

      To update a response policy with minimal arguments, run:

        $ {command} myresponsepolicy --description='My updated response policy.'
        --networks=''

      To update a response policy with all optional arguments, run:

        $ {command} myresponsepolicy --description='My updated response policy.'
        --networks=network1,network2

      To update a new zonal response policy scoped to a GKE cluster in
      us-central1-a, run:

        $ {command} myresponsepolicy --description='My new response policy.'
        --gkeclusters=cluster1 --location=us-central1-a
  """

  def _FetchResponsePolicy(self, response_policy_ref, api_version):
    """Get response policy to be Updated."""
    client = util.GetApiClient(api_version)
    message_module = apis.GetMessagesModule('dns', api_version)
    get_request = message_module.DnsResponsePoliciesGetRequest(
        responsePolicy=response_policy_ref.Name(),
        project=response_policy_ref.project)
    return client.responsePolicies.Get(get_request)

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    resource_args.AddResponsePolicyResourceArg(
        parser,
        verb='to update',
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
    to_update = self._FetchResponsePolicy(response_policy_ref, api_version)

    if not (
        args.IsSpecified('networks')
        or args.IsSpecified('description')
        or args.IsSpecified('gkeclusters')
    ):
      log.status.Print('Nothing to update.')
      return to_update

    if args.IsSpecified('networks'):
      if args.networks == ['']:
        args.networks = []
      to_update.networks = command_util.ParseResponsePolicyNetworks(
          args.networks, response_policy_ref.project, api_version)

    if args.IsSpecified('gkeclusters'):
      gkeclusters = args.gkeclusters
      to_update.gkeClusters = [
          messages.ResponsePolicyGKECluster(gkeClusterName=name)
          for name in gkeclusters
      ]

    if args.IsSpecified('description'):
      to_update.description = args.description

    update_req = messages.DnsResponsePoliciesUpdateRequest(
        responsePolicy=response_policy_ref.Name(),
        responsePolicyResource=to_update,
        project=response_policy_ref.project)

    if api_version == 'v2':
      update_req.location = args.location

    updated_response_policy = client.responsePolicies.Update(update_req)

    log.UpdatedResource(updated_response_policy.responsePolicy,
                        kind='ResponsePolicy')

    return updated_response_policy
