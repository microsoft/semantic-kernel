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
"""Get IAM autoscaling policy policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags


class GetIamPolicy(base.Command):
  """Get IAM policy for an autoscaling policy.

  Gets the IAM policy for an autoscaling policy, given an autoscaling policy ID.

  ## EXAMPLES

  The following command prints the IAM policy for an autoscaling policy with the
  ID `example-autoscaling-policy`:

    $ {command} example-autoscaling-policy
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddAutoscalingPolicyResourceArg(
        parser, 'retrieve the IAM policy for', api_version=dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    messages = dataproc.messages

    policy_ref = args.CONCEPTS.autoscaling_policy.Parse()
    # pylint: disable=line-too-long
    request = messages.DataprocProjectsRegionsAutoscalingPoliciesGetIamPolicyRequest(
        resource=policy_ref.RelativeName())
    # pylint: enable=line-too-long

    return dataproc.client.projects_regions_autoscalingPolicies.GetIamPolicy(
        request)
