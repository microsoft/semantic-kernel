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
"""Set managed cluster for workflow template command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import compute_helpers
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.util.args import labels_util


class SetManagedCluster(base.UpdateCommand):
  """Set a managed cluster for the workflow template."""

  detailed_help = {
      'EXAMPLES': """
To update managed cluster in a workflow template, run:

  $ {command} my_template --region=us-central1 --no-address --num-workers=10 \
--worker-machine-type=custom-6-23040

"""
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    parser.add_argument(
        '--cluster-name',
        help="""\
          The name of the managed dataproc cluster.
          If unspecified, the workflow template ID will be used.""")
    clusters.ArgsForClusterRef(
        parser,
        dataproc,
        cls.Beta(),
        cls.Alpha(),
        include_deprecated=cls.Beta(),
        include_gke_platform_args=False)
    flags.AddTemplateResourceArg(parser, 'set managed cluster',
                                 dataproc.api_version)
    if cls.Beta():
      clusters.BetaArgsForClusterRef(parser)

  @classmethod
  def Beta(cls):
    return cls.ReleaseTrack() != base.ReleaseTrack.GA

  @classmethod
  def Alpha(cls):
    return cls.ReleaseTrack() == base.ReleaseTrack.ALPHA

  @classmethod
  def GetComputeReleaseTrack(cls):
    if cls.Beta():
      return base.ReleaseTrack.BETA
    return base.ReleaseTrack.GA

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    template_ref = args.CONCEPTS.template.Parse()

    workflow_template = dataproc.GetRegionsWorkflowTemplate(
        template_ref, args.version)

    if args.cluster_name:
      cluster_name = args.cluster_name
    else:
      cluster_name = template_ref.workflowTemplatesId

    compute_resources = compute_helpers.GetComputeResources(
        self.GetComputeReleaseTrack(), cluster_name, template_ref.regionsId)

    cluster_config = clusters.GetClusterConfig(
        args,
        dataproc,
        template_ref.projectsId,
        compute_resources,
        self.Beta(),
        self.Alpha(),
        include_deprecated=self.Beta())

    labels = labels_util.ParseCreateArgs(
        args, dataproc.messages.ManagedCluster.LabelsValue)

    managed_cluster = dataproc.messages.ManagedCluster(
        clusterName=cluster_name, config=cluster_config, labels=labels)

    workflow_template.placement = dataproc.messages.WorkflowTemplatePlacement(
        managedCluster=managed_cluster)

    response = dataproc.client.projects_regions_workflowTemplates.Update(
        workflow_template)
    return response
