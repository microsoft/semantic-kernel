# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Evaluate policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import platform_policy
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags
from googlecloudsdk.command_lib.container.binauthz import parsing
from googlecloudsdk.command_lib.container.binauthz import util
from googlecloudsdk.core.exceptions import Error


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Evaluate(base.Command):
  """Evaluate a Binary Authorization platform policy.

  ## EXAMPLES

  To evaluate a policy using its resource name:

    $ {command} projects/my-proj/platforms/gke/policies/my-policy
    --resource=$KUBERNETES_RESOURCE

  To evaluate the same policy using flags against an image:

    $ {command} my-policy --platform=gke --project=my-proj --image=$IMAGE
  """

  @staticmethod
  def Args(parser):
    flags.AddPlatformPolicyResourceArg(parser, 'to evaluate')
    flags.AddEvaluationUnitArg(parser)

  def Run(self, args):
    policy_ref = args.CONCEPTS.policy_resource_name.Parse().RelativeName()
    platform_id = policy_ref.split('/')[3]
    if platform_id != 'gke':
      raise Error(
          "Found unsupported platform '{}'. Currently only 'gke' platform "
          "policies are supported.".format(platform_id)
      )

    if args.resource:
      resource_obj = parsing.LoadResourceFile(args.resource)
      response = platform_policy.Client('v1').Evaluate(
          policy_ref, resource_obj, False
      )
    else:
      pod_spec = util.GeneratePodSpecFromImages(args.image)
      response = platform_policy.Client('v1').Evaluate(
          policy_ref, pod_spec, False
      )

    # Set non-zero exit code for non-conformant verdicts to improve the
    # command's scriptability.
    if (
        response.verdict
        != apis.GetMessagesModule(
            'v1'
        ).EvaluateGkePolicyResponse.VerdictValueValuesEnum.CONFORMANT
    ):
      self.exit_code = 2

    return response
