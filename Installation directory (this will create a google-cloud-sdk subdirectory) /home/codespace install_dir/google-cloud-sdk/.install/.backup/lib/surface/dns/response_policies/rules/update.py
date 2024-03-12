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
"""gcloud dns response-policies rules update command."""

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
from googlecloudsdk.core import properties


def _AddArgsCommon(parser):
  """Adds the common arguments for all versions."""
  flags.GetLocalDataResourceRecordSets().AddToParser(parser)
  # TODO(b/215745011) use AddResponsePolicyRulesBehaviorFlag once switch to v2
  flags.GetResponsePolicyRulesBehavior().AddToParser(parser)
  flags.GetLocationArg().AddToParser(parser)

  parser.add_argument(
      '--dns-name',
      required=False,
      help='DNS name (wildcard or exact) to apply this rule to.')


def _FetchResponsePolicyRule(response_policy, response_policy_rule, api_version,
                             args):
  """Get response policy rule to be Updated."""
  client = util.GetApiClient(api_version)
  m = apis.GetMessagesModule('dns', api_version)
  get_request = m.DnsResponsePolicyRulesGetRequest(
      responsePolicy=response_policy,
      project=properties.VALUES.core.project.Get(),
      responsePolicyRule=response_policy_rule)
  if api_version == 'v2':
    get_request.location = args.location
  return client.responsePolicyRules.Get(get_request)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Updates a new Cloud DNS response policy rule.

      This command updates a new Cloud DNS response policy rule.

      ## EXAMPLES

      To update a new response policy rule with DNS name, run:

        $ {command} myresponsepolicyrule --response-policy="myresponsepolicy"
        --dns-name="www.newzone.com." # pylint: disable=line-too-long

      To update a new response policy rule with local data rrsets, run:

        $ {command} myresponsepolicyrule --response-policy="myresponsepolicy"
        --local-data=name=www.zone.com.,type=A,ttl=21600,rrdatas=1.2.3.4

      To update a new response policy rule with behavior, run:

        $ {command} myresponsepolicyrule --response-policy="myresponsepolicy"
        --behavior=bypassResponsePolicy
  """

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    _AddArgsCommon(parser)
    resource_args.AddResponsePolicyRuleArg(
        parser, verb='to update', api_version='v1')
    parser.display_info.AddFormat('json')

  def Run(self, args):
    api_version = util.GetApiFromTrackAndArgs(self.ReleaseTrack(), args)
    client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)

    # Get Response Policy Rule
    response_policy_rule_ref = args.CONCEPTS.response_policy_rule.Parse()
    response_policy_rule_name = response_policy_rule_ref.Name()

    response_policy_rule = messages.ResponsePolicyRule(
        ruleName=response_policy_rule_name)

    response_policy = messages.ResponsePolicy(
        responsePolicyName=args.response_policy)

    to_update = _FetchResponsePolicyRule(response_policy.responsePolicyName,
                                         response_policy_rule.ruleName,
                                         api_version, args)

    if not args.IsSpecified('dns_name') and not args.IsSpecified(
        'local_data') and not args.IsSpecified('behavior'):
      log.status.Print('Nothing to update.')
      return to_update

    if args.IsSpecified('dns_name'):
      to_update.dnsName = args.dns_name

    if args.IsSpecified('local_data'):
      to_update.behavior = None
      rrsets = []
      for rrset in args.local_data:
        resource_record_set = messages.ResourceRecordSet(
            name=rrset.get('name'),
            type=rrset.get('type'),
            ttl=rrset.get('ttl'),
            rrdatas=rrset.get('rrdatas').split('|'))
        rrsets.append(resource_record_set)
      to_update.localData = messages.ResponsePolicyRuleLocalData(
          localDatas=rrsets)

    if args.IsSpecified('behavior'):
      to_update.localData = None
      to_update.behavior = command_util.ParseResponsePolicyRulesBehavior(
          args, api_version)

    update_req = messages.DnsResponsePolicyRulesUpdateRequest(
        responsePolicy=response_policy.responsePolicyName,
        responsePolicyRule=response_policy_rule.ruleName,
        responsePolicyRuleResource=to_update,
        project=properties.VALUES.core.project.Get())

    if api_version == 'v2':
      update_req.location = args.location

    updated_response_policy_rule = client.responsePolicyRules.Update(update_req)

    log.UpdatedResource(updated_response_policy_rule.responsePolicyRule,
                        kind='ResponsePolicyRule')

    return updated_response_policy_rule
