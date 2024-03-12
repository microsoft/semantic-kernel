# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""gcloud dns response-policies delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.command_lib.dns import resource_args
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  r"""Deletes a Cloud DNS response policy.

      This command deletes a new Cloud DNS response policy.

      ## EXAMPLES

      To delete a global response policy (default), run:

        $ {command} myresponsepolicy
  """

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    api_version = util.GetApiFromTrack(cls.ReleaseTrack())
    resource_args.AddResponsePolicyResourceArg(
        parser, verb='to describe', api_version=api_version)
    flags.GetLocationArg().AddToParser(parser)
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

    request = messages.DnsResponsePoliciesDeleteRequest(
        responsePolicy=response_policy_name,
        project=response_policy_ref.project)

    if api_version == 'v2':
      request.location = args.location

    result = client.responsePolicies.Delete(request)

    log.DeletedResource(response_policy_ref, kind='ResponsePolicy')

    return result
