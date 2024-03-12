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
"""Remove Job from workflow template command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'EXAMPLES':
        """\
      To remove a job with step ID 'step-id' from a workflow template
      'workflow-template' in region 'us-central1', run:

        $ {command} workflow-template --region=us-central1 --step-id=step-id
      """,
}


class RemoveJob(base.UpdateCommand):
  """Remove a job from workflow template."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    parser.add_argument(
        '--step-id',
        metavar='STEP_ID',
        type=str,
        help='The step ID of the job in the workflow template to remove.')
    flags.AddTemplateResourceArg(
        parser, 'remove job', api_version=dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    template_ref = args.CONCEPTS.template.Parse()

    workflow_template = dataproc.GetRegionsWorkflowTemplate(
        template_ref, args.version)

    jobs = workflow_template.jobs

    job_removed = False
    new_jobs = []
    for ordered_job in jobs:
      if ordered_job.stepId != args.step_id:
        new_jobs.append(ordered_job)
      else:
        console_io.PromptContinue(
            message=('The job [{0}] will be removed from workflow template '
                     '[{1}].').format(args.step_id, workflow_template.id),
            cancel_on_no=True)
        job_removed = True

    if not job_removed:
      log.error('Step id [{0}] is not found in workflow template [{1}].'.format(
          args.step_id, workflow_template.id))
      return  # do not update workflow template if job is not removed.

    workflow_template.jobs = new_jobs
    response = dataproc.client.projects_regions_workflowTemplates.Update(
        workflow_template)
    return response
