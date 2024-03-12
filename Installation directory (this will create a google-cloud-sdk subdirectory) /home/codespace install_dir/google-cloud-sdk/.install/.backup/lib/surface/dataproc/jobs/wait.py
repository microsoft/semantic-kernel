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

"""Wait for a job to complete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log


class Wait(base.Command):
  r"""View the output of a job as it runs or after it completes.

  View the output of a job as it runs or after it completes.

  ## EXAMPLES

  To see a list of all jobs, run:

    $ gcloud dataproc jobs list

  To display these jobs with their respective IDs and underlying REST calls,
  run:

    $ gcloud dataproc jobs list --format "table(reference.jobId)" \
      --limit 1 --log-http

  To view the output of a job as it runs, run:

    $ {command} job_id
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddJobResourceArg(parser, 'wait for', dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    job_ref = args.CONCEPTS.job.Parse()

    job = dataproc.client.projects_regions_jobs.Get(
        dataproc.messages.DataprocProjectsRegionsJobsGetRequest(
            projectId=job_ref.projectId,
            region=job_ref.region,
            jobId=job_ref.jobId))

    # TODO(b/36050945) Check if Job is still running and fail or handle 401.

    job = util.WaitForJobTermination(
        dataproc,
        job,
        job_ref,
        message='Waiting for job completion',
        goal_state=dataproc.messages.JobStatus.StateValueValuesEnum.DONE,
        error_state=dataproc.messages.JobStatus.StateValueValuesEnum.ERROR,
        stream_driver_log=True)

    log.status.Print('Job [{0}] finished successfully.'.format(args.job))

    return job
