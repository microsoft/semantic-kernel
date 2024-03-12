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

"""Transcoder API jobs delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transcoder import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transcoder import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete transcoder jobs."""

  detailed_help = {
      'EXAMPLES': """
          To delete a transcoder job:

              $ {command} JOB_NAME --location=us-central1
              """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddJobResourceArg(parser)

  def Run(self, args):
    """Delete a job."""
    client = jobs.JobsClient(self.ReleaseTrack())

    job_ref = args.CONCEPTS.job_name.Parse()

    console_io.PromptContinue(
        'You are about to delete job [{}]'.format(job_ref.jobsId),
        throw_if_unattended=True, cancel_on_no=True)

    result = client.Delete(job_ref)
    log.DeletedResource(job_ref.RelativeName(), kind='job')
    return result
