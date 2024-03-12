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
"""Implementation of gcloud dataflow jobs cancel command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import job_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Cancel(base.Command):
  """Cancels all jobs that match the command line arguments."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    job_utils.ArgsForJobRefs(parser, nargs='+')
    parser.add_argument(
        '--force',
        action='store_true',
        help='Forcibly cancels a Dataflow job, leaking any VMs the Dataflow job created. Regular cancel must have been attempted at least 30 minutes ago for a job to be force cancelled.',
    )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: all the arguments that were provided to this command invocation.
    """
    for job_ref in job_utils.ExtractJobRefs(args):
      try:
        if args.force:
          console_io.PromptContinue(
              message='Force cancellation will leak VMs the cancelled Dataflow job created that must be manually cleaned up.',
              cancel_on_no=True,
          )
        apis.Jobs.Cancel(
            job_ref.jobId,
            args.force,
            project_id=job_ref.projectId,
            region_id=job_ref.location)
        log.status.Print('Cancelled job [{0}]'.format(job_ref.jobId))
      except exceptions.HttpException as error:
        log.status.Print(
            'Failed to cancel job [{0}]: {1} Please ensure you have permission '
            "to access the job and the `--region` flag, {2}, matches the job\'s"
            ' region.'.format(job_ref.jobId, error.payload.status_message,
                              job_ref.location))
