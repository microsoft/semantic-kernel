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
"""Describe a node group command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.Command):
  """Describe the node group."""
  detailed_help = {
      'EXAMPLES':
          """\
          To describe a node group, run:

            $ {command} my-node-group-id --region=us-central1 --cluster=my-cluster-name
          """
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())

    flags.AddNodeGroupResourceArg(parser, 'describe', dataproc.api_version)

  def Run(self, args):
    node_group_ref = args.CONCEPTS.node_group.Parse()
    dataproc = dp.Dataproc(self.ReleaseTrack())
    messages = dataproc.messages
    request = messages.DataprocProjectsRegionsClustersNodeGroupsGetRequest(
        name=node_group_ref.RelativeName())
    node_group = dataproc.client.projects_regions_clusters_nodeGroups.Get(
        request)

    return node_group
