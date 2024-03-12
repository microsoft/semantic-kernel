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
"""Add a Spark job to the workflow template."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import workflow_templates
from googlecloudsdk.command_lib.dataproc.jobs import spark

DETAILED_HELP = {
    'EXAMPLES':
        """\
      To add a Spark job with files 'file1' and 'file2' to a the workflow template
      'my-workflow-template' in region 'us-central1' with step-id 'my-step-id'
      , run:

        $ {command} --step-id=my-step_id --files="file1,file2" --workflow-template=my-workflow-template --region=us-central1
      """,
}


class Spark(spark.SparkBase, base.Command):
  """Add a Spark job to the workflow template."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    spark.SparkBase.Args(parser)
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    workflow_templates.AddWorkflowTemplatesArgs(parser, dataproc.api_version)
    driver_group = parser.add_argument_group()
    util.AddJvmDriverFlags(driver_group)

  def ConfigureJob(self, messages, job, files_by_type, args):
    spark.SparkBase.ConfigureJob(messages, job, files_by_type,
                                 self.BuildLoggingConfig(
                                     messages, args.driver_log_levels), args)
    workflow_templates.ConfigureOrderedJob(messages, job, args)

  def Run(self, args):
    self.PopulateFilesByType(args)
    dataproc = dp.Dataproc(self.ReleaseTrack())
    ordered_job = workflow_templates.CreateWorkflowTemplateOrderedJob(
        args, dataproc)
    self.ConfigureJob(dataproc.messages, ordered_job, self.files_by_type, args)
    return workflow_templates.AddJobToWorkflowTemplate(args, dataproc,
                                                       ordered_job)
