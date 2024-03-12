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
"""gcloud dns policy create command."""

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
  flags.GetPolicyDescriptionArg(required=True).AddToParser(parser)
  flags.GetPolicyNetworksArg(required=True).AddToParser(parser)
  flags.GetPolicyInboundForwardingArg().AddToParser(parser)
  flags.GetPolicyAltNameServersArg().AddToParser(parser)
  flags.GetPolicyLoggingArg().AddToParser(parser)
  flags.GetPolicyPrivateAltNameServersArg().AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.UpdateCommand):
  r"""Creates a new Cloud DNS policy.

      This command creates a new Cloud DNS policy.

      ## EXAMPLES

      To create a new policy with minimal arguments, run:

        $ {command} mypolicy \
        --description='My new policy test policy 5' \
        --networks=''

      To create a new policy with all optional arguments, run:

        $ {command} mypolicy \
        --description='My new policy test policy 5' \
        --networks=network1,network2 \
        --alternative-name-servers=192.168.1.1,192.168.1.2 \
        --enable-inbound-forwarding \
        --enable-logging
  """

  @staticmethod
  def Args(parser):
    resource_args.AddPolicyResourceArg(
        parser, verb='to create', api_version='v1')
    _AddArgsCommon(parser)
    parser.display_info.AddFormat('json')

  def Run(self, args):
    api_version = util.GetApiFromTrack(self.ReleaseTrack())
    client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)

    # Get Policy
    policy_ref = args.CONCEPTS.policy.Parse()
    policy_name = policy_ref.Name()

    policy = messages.Policy(
        name=policy_name, enableLogging=False, enableInboundForwarding=False)

    if args.IsSpecified('networks'):
      if args.networks == ['']:
        args.networks = []
      policy.networks = command_util.ParsePolicyNetworks(
          args.networks, policy_ref.project, api_version)
    else:
      raise exceptions.RequiredArgumentException('--networks', ("""
           A list of networks must be
           provided.'
         NOTE: You can provide an empty value ("") for policies that
          have NO network binding.
          """))

    if args.IsSpecified('alternative_name_servers') or args.IsSpecified(
        'private_alternative_name_servers'):
      if args.alternative_name_servers == ['']:
        args.alternative_name_servers = []
      if args.private_alternative_name_servers == ['']:
        args.private_alternative_name_servers = []
      policy.alternativeNameServerConfig = command_util.ParseAltNameServers(
          version=api_version,
          server_list=args.alternative_name_servers,
          private_server_list=args.private_alternative_name_servers)

    if args.IsSpecified('enable_inbound_forwarding'):
      policy.enableInboundForwarding = args.enable_inbound_forwarding

    if args.IsSpecified('enable_logging'):
      policy.enableLogging = args.enable_logging

    if args.IsSpecified('description'):
      policy.description = args.description

    create_request = messages.DnsPoliciesCreateRequest(
        policy=policy, project=policy_ref.project)

    result = client.policies.Create(create_request)

    log.CreatedResource(policy_ref, kind='Policy')

    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(CreateGA):
  r"""Creates a new Cloud DNS policy.

      This command creates a new Cloud DNS policy.

      ## EXAMPLES

      To create a new policy with minimal arguments, run:

        $ {command} mypolicy \
        --description='My new policy test policy 5' \
        --networks=''

      To create a new policy with all optional arguments, run:

        $ {command} mypolicy \
        --description='My new policy test policy 5' \
        --networks=network1,network2 \
        --alternative-name-servers=192.168.1.1,192.168.1.2 \
        --private-alternative-name-servers=100.64.0.1 \
        --enable-inbound-forwarding \
        --enable-logging
  """

  @staticmethod
  def Args(parser):
    resource_args.AddPolicyResourceArg(
        parser, verb='to create', api_version='v1beta2')
    _AddArgsCommon(parser)
    parser.display_info.AddFormat('json')

  def Run(self, args):
    api_version = util.GetApiFromTrack(self.ReleaseTrack())
    client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)

    # Get Policy
    policy_ref = args.CONCEPTS.policy.Parse()
    policy_name = policy_ref.Name()

    policy = messages.Policy(
        name=policy_name, enableLogging=False, enableInboundForwarding=False)

    if args.IsSpecified('networks'):
      if args.networks == ['']:
        args.networks = []
      policy.networks = command_util.ParsePolicyNetworks(
          args.networks, policy_ref.project, api_version)
    else:
      raise exceptions.RequiredArgumentException('--networks', ("""
           A list of networks must be
           provided.'
         NOTE: You can provide an empty value ("") for policies that
          have NO network binding.
          """))

    if args.IsSpecified('alternative_name_servers') or args.IsSpecified(
        'private_alternative_name_servers'):
      if args.alternative_name_servers == ['']:
        args.alternative_name_servers = []
      if args.private_alternative_name_servers == ['']:
        args.private_alternative_name_servers = []
      policy.alternativeNameServerConfig = command_util.BetaParseAltNameServers(
          version=api_version,
          server_list=args.alternative_name_servers,
          private_server_list=args.private_alternative_name_servers)

    if args.IsSpecified('enable_inbound_forwarding'):
      policy.enableInboundForwarding = args.enable_inbound_forwarding

    if args.IsSpecified('enable_logging'):
      policy.enableLogging = args.enable_logging

    if args.IsSpecified('description'):
      policy.description = args.description

    create_request = messages.DnsPoliciesCreateRequest(
        policy=policy, project=policy_ref.project)

    result = client.policies.Create(create_request)

    log.CreatedResource(policy_ref, kind='Policy')

    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  r"""Creates a new Cloud DNS policy.

      This command creates a new Cloud DNS policy.

      ## EXAMPLES

      To create a new policy with minimal arguments, run:

        $ {command} mypolicy \
        --description='My new policy test policy 5' \
        --networks=''

      To create a new policy with all optional arguments, run:

        $ {command} mypolicy \
        --description='My new policy test policy 5' \
        --networks=network1,network2 \
        --alternative-name-servers=192.168.1.1,192.168.1.2 \
        --private-alternative-name-servers=100.64.0.1 \
        --enable-inbound-forwarding \
        --enable-logging
  """

  @staticmethod
  def Args(parser):
    resource_args.AddPolicyResourceArg(
        parser, verb='to create', api_version='v1alpha2')
    _AddArgsCommon(parser)
    parser.display_info.AddFormat('json')
