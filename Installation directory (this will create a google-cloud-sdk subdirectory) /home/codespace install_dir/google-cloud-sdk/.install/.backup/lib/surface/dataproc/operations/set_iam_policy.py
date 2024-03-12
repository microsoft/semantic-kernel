# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Set IAM operation policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class SetIamPolicy(base.Command):
  """Set IAM policy for an operation.

  Sets the IAM policy for an operation, given an operation ID and the policy.
  """

  detailed_help = iam_util.GetDetailedHelpForSetIamPolicy('operation',
                                                          use_an=True)

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddOperationResourceArg(parser, 'set the policy on',
                                  dataproc.api_version)
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    msgs = dataproc.messages

    policy = iam_util.ParsePolicyFile(args.policy_file, msgs.Policy)
    set_iam_policy_request = msgs.SetIamPolicyRequest(policy=policy)

    operation_ref = args.CONCEPTS.operation.Parse()
    request = msgs.DataprocProjectsRegionsOperationsSetIamPolicyRequest(
        resource=operation_ref.RelativeName(),
        setIamPolicyRequest=set_iam_policy_request)

    return dataproc.client.projects_regions_operations.SetIamPolicy(request)
