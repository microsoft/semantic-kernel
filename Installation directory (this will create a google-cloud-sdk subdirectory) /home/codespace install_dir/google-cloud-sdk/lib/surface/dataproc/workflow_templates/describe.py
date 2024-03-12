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
"""Describe workflow template command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags

DETAILED_HELP = {
    'EXAMPLES':
        """\
      To describe a workflow template 'my-template' in region 'us-central1', run:

        $ {command} workflow-template --region=us-central1
      """,
}


class Describe(base.DescribeCommand):
  """Describe a workflow template."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddTemplateResourceArg(parser, 'describe', dataproc.api_version)
    flags.AddVersionFlag(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    template_ref = args.CONCEPTS.template.Parse()

    workflow_template = dataproc.GetRegionsWorkflowTemplate(
        template_ref, args.version)

    return workflow_template
