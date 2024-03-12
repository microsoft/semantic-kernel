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

"""Set IAM cluster policy command."""

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
  """Set IAM policy for a cluster.

  Sets the IAM policy for a cluster, given a cluster name and the policy.

  ## EXAMPLES

  The following command sets the IAM policy for a cluster with the name
  `example-cluster-name-1` using policy.yaml:

    $ {command} example-cluster-name-1 policy.yaml
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddClusterResourceArg(parser, 'set the policy on',
                                dataproc.api_version)
    parser.add_argument(
        'policy_file',
        metavar='POLICY_FILE',
        help="""\
        Path to a local JSON or YAML formatted file containing a valid policy.
        """)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    messages = dataproc.messages

    policy = iam_util.ParsePolicyFile(args.policy_file, messages.Policy)
    set_iam_policy_request = messages.SetIamPolicyRequest(policy=policy)

    cluster_ref = args.CONCEPTS.cluster.Parse()
    request = messages.DataprocProjectsRegionsClustersSetIamPolicyRequest(
        resource=cluster_ref.RelativeName(),
        setIamPolicyRequest=set_iam_policy_request)

    return dataproc.client.projects_regions_clusters.SetIamPolicy(request)
