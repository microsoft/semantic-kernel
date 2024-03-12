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

"""Implementation of gcloud dataflow jobs describe command.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import job_utils


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Outputs the Job object resulting from the Get API.

  By default this will display the Summary view which includes:
    - Project ID
    - Regional Endpoint
    - Job ID
    - Job Name
    - Job Type (Batch vs. Streaming)
    - Job Create Time
    - Job Status (Running, Done, Cancelled, Failed)
    - Job Status Time

  Notable values that are only in the full view:
    - Environment (staging Jars, information about workers, etc.)
    - Steps from the workflow graph
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    job_utils.ArgsForJobRef(parser)

    parser.add_argument(
        '--full',
        action='store_const',
        const=apis.Jobs.GET_REQUEST.ViewValueValuesEnum.JOB_VIEW_ALL,
        default=apis.Jobs.GET_REQUEST.ViewValueValuesEnum.JOB_VIEW_SUMMARY,
        help='Retrieve the full Job rather than the summary view')

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      A Job message.
    """
    job_ref = job_utils.ExtractJobRef(args)
    return apis.Jobs.Get(
        job_ref.jobId,
        project_id=job_ref.projectId,
        region_id=job_ref.location,
        view=args.full)
