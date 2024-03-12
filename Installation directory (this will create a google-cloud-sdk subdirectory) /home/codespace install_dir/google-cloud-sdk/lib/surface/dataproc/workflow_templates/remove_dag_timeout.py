# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Remove DAG timeout from workflow template command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'EXAMPLES':
        """\
      To remove a DAG timeout from a workflow template named
      ``my-workflow-template'' in region ``us-central1'', run:

        $ {command} my-workflow-template --region=us-central1"
      """,
}


class RemoveDagTimeout(base.CreateCommand):
  """Remove DAG timeout from a workflow template."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddTemplateResourceArg(parser, 'remove the DAG timeout from',
                                 dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    template_ref = args.CONCEPTS.template.Parse()

    workflow_template = dataproc.GetRegionsWorkflowTemplate(
        template_ref, args.version)

    workflow_template.dagTimeout = None

    response = dataproc.client.projects_regions_workflowTemplates.Update(
        workflow_template)

    log.status.Print('Removed DAG timeout from {0}.'.format(
        template_ref.Name()))
    return response
