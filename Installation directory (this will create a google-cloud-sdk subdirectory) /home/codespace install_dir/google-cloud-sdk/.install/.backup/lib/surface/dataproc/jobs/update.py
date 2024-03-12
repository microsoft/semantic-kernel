# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Update job command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


class Update(base.UpdateCommand):
  """Update the labels for a job.

  Update the labels for a job.

  ## EXAMPLES

  To add the label 'customer=acme' to a job , run:

    $ {command} job_id --update-labels=customer=acme

  To update the label 'customer=ackme' to 'customer=acme', run:

    $ {command} job_id --update-labels=customer=acme

  To remove the label whose key is 'customer', run:

    $ {command} job_id --remove-labels=customer
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddJobResourceArg(parser, 'update', dataproc.api_version)
    changes = parser.add_argument_group(required=True)
    # Allow the user to specify new labels as well as update/remove existing
    labels_util.AddUpdateLabelsFlags(changes)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    job_ref = args.CONCEPTS.job.Parse()

    changed_fields = []

    orig_job = dataproc.client.projects_regions_jobs.Get(
        dataproc.messages.DataprocProjectsRegionsJobsGetRequest(
            projectId=job_ref.projectId,
            region=job_ref.region,
            jobId=job_ref.jobId))

    # Update labels if the user requested it
    labels_update_result = labels_util.Diff.FromUpdateArgs(args).Apply(
        dataproc.messages.Job.LabelsValue, orig_job.labels)
    if labels_update_result.needs_update:
      changed_fields.append('labels')

    updated_job = orig_job
    updated_job.labels = labels_update_result.GetOrNone()
    request = dataproc.messages.DataprocProjectsRegionsJobsPatchRequest(
        projectId=job_ref.projectId,
        region=job_ref.region,
        jobId=job_ref.jobId,
        job=updated_job,
        updateMask=','.join(changed_fields))

    returned_job = dataproc.client.projects_regions_jobs.Patch(request)

    log.UpdatedResource(returned_job)
    return returned_job
