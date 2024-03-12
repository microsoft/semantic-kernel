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

"""Kill job command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Kill(base.Command):
  """Kill an active job.

  Kill an active job.

  ## EXAMPLES

  To cancel a job, run:

    $ {command} job_id
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddJobResourceArg(parser, 'kill', dataproc.api_version)
    flags.AddAsync(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    job_ref = args.CONCEPTS.job.Parse()
    request = dataproc.messages.DataprocProjectsRegionsJobsCancelRequest(
        projectId=job_ref.projectId,
        region=job_ref.region,
        jobId=job_ref.jobId,
        cancelJobRequest=dataproc.messages.CancelJobRequest())

    console_io.PromptContinue(
        message="The job '{0}' will be killed.".format(args.job),
        cancel_on_no=True,
        cancel_string='Cancellation aborted by user.')

    job = dataproc.client.projects_regions_jobs.Cancel(request)
    log.status.Print(
        'Job cancellation initiated for [{0}].'.format(job_ref.jobId))

    if args.async_:
      output_job = job
    else:
      output_job = util.WaitForJobTermination(
          dataproc,
          job,
          job_ref,
          message='Waiting for job cancellation',
          goal_state=dataproc.messages.JobStatus.StateValueValuesEnum.CANCELLED)
      log.status.Print('Killed [{0}].'.format(job_ref))

    return output_job
