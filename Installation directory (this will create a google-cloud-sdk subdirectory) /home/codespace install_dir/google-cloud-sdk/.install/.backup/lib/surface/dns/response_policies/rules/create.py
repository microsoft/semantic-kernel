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
"""gcloud dns response-policies rules create command."""

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
  """Adds the common arguments for all versions."""
  flags.GetLocalDataResourceRecordSets().AddToParser(parser)
  # TODO(b/215745011) use AddResponsePolicyRulesBehaviorFlag once switch to v2
  flags.GetResponsePolicyRulesBehavior().AddToParser(parser)
  flags.GetLocationArg().AddToParser(parser)

  parser.add_argument(
      '--dns-name',
      required=True,
      help='DNS name (wildcard or exact) to apply this rule to.')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.UpdateCommand):
  r"""Creates a new Cloud DNS response policy rule.

      ## EXAMPLES

      To create a new response policy rule with local data rrsets, run:

        $ {command} myresponsepolicyrule --response-policy="myresponsepolicy"
        --dns-name="www.zone.com."
        --local-data=name=www.zone.com.,type=CNAME,ttl=21600,rrdatas=zone.com.

      To create a new response policy rule with behavior, run:

        $ {command} myresponsepolicyrule --response-policy="myresponsepolicy"
        --dns-name="www.zone.com." --behavior=bypassResponsePolicy

      To create a new response policy rule with behavior in a zonal response
      policy in us-east1-a, run:

        $ {command} myresponsepolicyrule --response-policy="myresponsepolicy"
        --dns-name="www.zone.com." --behavior=bypassResponsePolicy
        --location=us-east1-a
  """

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    api_version = util.GetApiFromTrack(cls.ReleaseTrack())
    _AddArgsCommon(parser)
    resource_args.AddResponsePolicyRuleArg(
        parser, verb='to create', api_version=api_version)
    parser.display_info.AddFormat('json')

  def Run(self, args):
    api_version = util.GetApiFromTrackAndArgs(self.ReleaseTrack(), args)
    client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)

    # Get Response Policy Rule
    registry = util.GetRegistry(api_version)
    response_policy_rule_ref = registry.Parse(
        args.response_policy_rule,
        util.GetParamsForRegistry(api_version, args, parent='responsePolicies'),
        collection='dns.responsePolicyRules')
    response_policy_rule_name = response_policy_rule_ref.Name()

    response_policy_rule = messages.ResponsePolicyRule(
        ruleName=response_policy_rule_name)

    response_policy_rule.dnsName = args.dns_name

    if args.IsSpecified('behavior') and args.IsSpecified('local_data'):
      raise exceptions.ConflictingArgumentsException(
          'Only one of arguments [--behavior, --local-data] is allowed.')

    if args.IsSpecified('behavior'):
      response_policy_rule.behavior = command_util.ParseResponsePolicyRulesBehavior(
          args, api_version)
    elif args.IsSpecified('local_data'):
      rrsets = []
      for rrset in args.local_data:
        resource_record_set = messages.ResourceRecordSet(
            name=rrset.get('name'),
            type=rrset.get('type'),
            ttl=rrset.get('ttl'),
            rrdatas=rrset.get('rrdatas').split('|'))
        rrsets.append(resource_record_set)

      local_data = messages.ResponsePolicyRuleLocalData(
          localDatas=rrsets)
      response_policy_rule.localData = local_data

    create_request = messages.DnsResponsePolicyRulesCreateRequest(
        responsePolicy=args.response_policy,
        project=response_policy_rule_ref.project,
        responsePolicyRule=response_policy_rule)

    if api_version == 'v2':
      create_request.location = args.location

    result = client.responsePolicyRules.Create(create_request)

    log.CreatedResource(response_policy_rule_ref, kind='ResponsePolicyRule')

    return result
