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

"""Set IAM workflow template policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.iam import iam_util


class SetIamPolicy(base.Command):
  """Set IAM policy for a workflow template.

  Sets the IAM policy for a workflow template, given a template ID and the
  policy.
  """

  detailed_help = iam_util.GetDetailedHelpForSetIamPolicy('template')

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddTemplateResourceArg(parser, 'set the policy on',
                                 dataproc.api_version)
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    msgs = dataproc.messages

    policy = iam_util.ParsePolicyFile(args.policy_file, msgs.Policy)
    set_iam_policy_request = msgs.SetIamPolicyRequest(policy=policy)

    template_ref = args.CONCEPTS.template.Parse()
    request = msgs.DataprocProjectsRegionsWorkflowTemplatesSetIamPolicyRequest(
        resource=template_ref.RelativeName(),
        setIamPolicyRequest=set_iam_policy_request)

    return dataproc.client.projects_regions_workflowTemplates.SetIamPolicy(
        request)
