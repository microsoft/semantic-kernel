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
"""Create workflow template command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc import workflow_templates
from googlecloudsdk.command_lib.util.args import labels_util
import six

DETAILED_HELP = {
    'EXAMPLES':
        """\
      To create a workflow template named ``my-workflow-template'' in region
      ``us-central1'' with label params 'key1'='value1' and 'key2'='value2', run:

        $ {command} my-workflow-template --region=us-central1 --labels="key1=value1,key2=value2"
      """,
}


class Create(base.CreateCommand):
  """Create a workflow template."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    labels_util.AddCreateLabelsFlags(parser)
    workflow_templates.AddDagTimeoutFlag(parser, False)
    workflow_templates.AddKmsKeyFlag(parser, False)
    flags.AddTemplateResourceArg(parser, 'create', dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    messages = dataproc.messages

    template_ref = args.CONCEPTS.template.Parse()
    # TODO(b/109837200) make the dataproc discovery doc parameters consistent
    # Parent() fails for the collection because of projectId/projectsId and
    # regionId/regionsId inconsistencies.
    # parent = template_ref.Parent().RelativePath()
    parent = '/'.join(template_ref.RelativeName().split('/')[0:4])

    workflow_template = messages.WorkflowTemplate(
        id=template_ref.Name(),
        name=template_ref.RelativeName(),
        labels=labels_util.ParseCreateArgs(
            args, messages.WorkflowTemplate.LabelsValue))

    if args.dag_timeout:
      workflow_template.dagTimeout = six.text_type(args.dag_timeout) + 's'

    if args.kms_key:
      workflow_template.encryptionConfig = (
          workflow_templates.GenerateEncryptionConfig(args.kms_key, dataproc)
      )

    request = messages.DataprocProjectsRegionsWorkflowTemplatesCreateRequest(
        parent=parent, workflowTemplate=workflow_template)

    template = dataproc.client.projects_regions_workflowTemplates.Create(
        request)
    return template
