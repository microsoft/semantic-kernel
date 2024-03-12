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

"""Get IAM cluster policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class GetIamPolicy(base.ListCommand):
  """Get IAM policy for a cluster.

  Gets the IAM policy for a cluster, given a cluster name.

  ## EXAMPLES

  The following command prints the IAM policy for a cluster with the name
  `example-cluster-name-1`:

    $ {command} example-cluster-name-1
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddClusterResourceArg(parser, 'retrieve the policy for',
                                dataproc.api_version)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    messages = dataproc.messages

    cluster_ref = args.CONCEPTS.cluster.Parse()
    request = messages.DataprocProjectsRegionsClustersGetIamPolicyRequest(
        resource=cluster_ref.RelativeName())

    return dataproc.client.projects_regions_clusters.GetIamPolicy(request)
