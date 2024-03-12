# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Export workflow template command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files

DETAILED_HELP = {
    'EXAMPLES':
        """\
      To export version 1.0 of workflow template for 'my-workflow-template' in region
      'us-central1' to template.yaml, run:

        $ {command} my-workflow-template --region=us-central1 --destination=path/to/template.yaml --version=1.0
      """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Export a workflow template.

  Exports a workflow template's configuration to a file.
  This configuration can be imported at a later time.
  """

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddTemplateResourceArg(parser, 'export', dataproc.api_version)
    export_util.AddExportFlags(parser)
    flags.AddVersionFlag(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    template_ref = args.CONCEPTS.template.Parse()

    # Get specified version, or most recent version if no version arg provided.
    workflow_template = dataproc.GetRegionsWorkflowTemplate(
        template_ref, args.version)

    # Filter out OUTPUT_ONLY fields and resource identifying fields. Note this
    # needs to be kept in sync with v1 workflow_templates.proto.
    workflow_template.id = None
    workflow_template.name = None
    workflow_template.version = None
    workflow_template.createTime = None
    workflow_template.updateTime = None
    # We do not need to clear any fields from workflow_template.placement.
    # 1) Managed cluster:
    #    a) cluster_name is really a name prefix, so it's okay that multiple
    #       templates have the same value.
    #    b) The server does not resolve OUTPUT_ONLY fields when storing a
    #       workflow template, so cluster_config is fine as is.
    # 2) Cluster selector: there are no OUTPUT_ONLY or directly resource
    # identifying fields here.

    if args.destination:
      with files.FileWriter(args.destination) as stream:
        export_util.Export(message=workflow_template, stream=stream)
    else:
      export_util.Export(message=workflow_template, stream=sys.stdout)
