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
"""Set IAM autoscaling policy policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.iam import iam_util


class SetIamPolicy(base.Command):
  r"""Set IAM policy for an autoscaling policy.

  Sets the IAM policy for an autoscaling policy, given an autoscaling policy ID
  and the IAM policy.

  ## EXAMPLES
    The following command will read an IAM policy defined in a JSON file
    'policy.json' and set it for an autoscaling-policy with identifier
    'example-autoscaling-policy'

        $ {command} autoscaling-policies set-iam-policy \
            example-autoscaling-policy policy.json

    See https://cloud.google.com/iam/docs/managing-policies for details of the
    policy file format and contents.
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddAutoscalingPolicyResourceArg(parser, 'retrieve the IAM policy for',
                                          dataproc.api_version)
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    messages = dataproc.messages

    policy = iam_util.ParsePolicyFile(args.policy_file, messages.Policy)
    set_iam_policy_request = messages.SetIamPolicyRequest(policy=policy)

    policy_ref = args.CONCEPTS.autoscaling_policy.Parse()
    # pylint: disable=line-too-long
    request = messages.DataprocProjectsRegionsAutoscalingPoliciesSetIamPolicyRequest(
        resource=policy_ref.RelativeName(),
        setIamPolicyRequest=set_iam_policy_request)
    # pylint: enable=line-too-long

    return dataproc.client.projects_regions_autoscalingPolicies.SetIamPolicy(
        request)
