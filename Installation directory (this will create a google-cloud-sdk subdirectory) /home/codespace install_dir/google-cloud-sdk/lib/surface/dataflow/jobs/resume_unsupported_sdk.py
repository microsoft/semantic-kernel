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

"""Implementation of gcloud dataflow jobs resume-unsupported-sdk command.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import job_utils
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Resume(base.Command):
  """Resumes job running with the specified job id.

     Resumes a pipeline job which is running on an unsupported SDK version.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    job_utils.ArgsForJobRef(parser)

    parser.add_argument(
        "--token",
        help=("The resume token unique to the job."),
        required=True)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: all the arguments that were provided to this command invocation.
    """
    job_ref = job_utils.ExtractJobRef(args)
    try:
      apis.Jobs.ResumeUnsupportedSDK(
          job_ref.jobId,
          "unsupported_sdk_temporary_override_token=" + args.token,
          project_id=job_ref.projectId,
          region_id=job_ref.location)
      log.status.Print("Resuming job running on unsupported SDK version [{0}]. "
                       "This job may be cancelled in the future. For more "
                       "details, see https://cloud.google.com/dataflow/docs/"
                       "support/sdk-version-support-status.".format(
                           job_ref.jobId))
    except exceptions.HttpException as error:
      log.status.Print(
          ("Failed to resume job [{0}]: {1} Please ensure you have permission "
           "to access the job, the `--region` flag, {2}, is correct for the "
           "job and the `--token` flag, {3}, corresponds to the job.").format(
               job_ref.jobId, error.payload.status_message, job_ref.location,
               args.token))
