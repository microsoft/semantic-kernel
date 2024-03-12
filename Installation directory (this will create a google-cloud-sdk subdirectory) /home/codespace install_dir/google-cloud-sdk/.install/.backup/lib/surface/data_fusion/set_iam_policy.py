# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Command to set an IAM policy on a Data Fusion instance or a namespace."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_fusion import datafusion as df
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_fusion import data_fusion_iam_util
from googlecloudsdk.command_lib.data_fusion import resource_args
from googlecloudsdk.command_lib.iam import iam_util


def SetIamPolicyFromFile(instance_ref,
                         namespace,
                         policy_file,
                         messages,
                         client):
  """Reads an instance's IAM policy from a file, and sets it."""
  new_iam_policy = data_fusion_iam_util.ParsePolicyFile(
      policy_file,
      messages.Policy)

  return data_fusion_iam_util.DoSetIamPolicy(
      instance_ref, namespace, new_iam_policy, messages, client)


class SetIamPolicy(base.Command):
  r"""Sets the IAM policy for a Cloud Data Fusion instance.

  ## EXAMPLES

  To set the policy for instance 'my-instance' in project 'my-project', location
  in 'my-location', and zone in 'my-zone' run:

  $ {command} my-instance policy-file.yaml --project=my-project \
    --location=my-location

  To do the same in a particular namespace, run:
  $ {command} my-instance policy-file.yaml --project=my-project \
    --location=my-location [--namespace=NAMESPACE]
  """

  @staticmethod
  def Args(parser):
    resource_args.AddInstanceResourceArg(parser, 'Instance to set.')
    base.URI_FLAG.RemoveFromParser(parser)
    iam_util.AddArgForPolicyFile(parser)
    parser.add_argument(
        '--namespace',
        help='CDAP Namespace whose IAM policy we wish to set. '
        'For example: `--namespace=my-namespace`.')

  def Run(self, args):
    datafusion = df.Datafusion()
    instance_ref = args.CONCEPTS.instance.Parse()

    results = SetIamPolicyFromFile(instance_ref, args.namespace,
                                   args.policy_file, datafusion.messages,
                                   datafusion.client)
    return results
