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

"""Implementation of gcloud dataflow jobs show command.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.api_lib.dataflow import job_display
from googlecloudsdk.api_lib.dataflow import step_json
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import job_utils


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Show(base.Command):
  """Shows a short description of the given job.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    job_utils.ArgsForJobRef(parser)

    parser.add_argument(
        '--environment', action='store_true',
        help='If present, the environment will be listed.')
    parser.add_argument(
        '--steps', action='store_true',
        help='If present, the steps will be listed.')

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      A Job message.
    """
    job_ref = job_utils.ExtractJobRef(args)
    job = apis.Jobs.Get(
        job_id=job_ref.jobId,
        project_id=job_ref.projectId,
        region_id=job_ref.location,
        view=apis.Jobs.GET_REQUEST.ViewValueValuesEnum.JOB_VIEW_ALL)

    # Extract the basic display information for the job
    shown_job = job_display.DisplayInfo(job)

    if args.environment:
      shown_job.environment = job.environment

    if args.steps:
      shown_job.steps = [
          self._PrettyStep(step) for step in step_json.ExtractSteps(job)]

    return shown_job

  def _PrettyStep(self, step):
    """Prettify a given step, by only extracting certain pieces of info.

    Args:
      step: The step to prettify.
    Returns:
      A dictionary describing the step.
    """
    return {
        'id': step['name'],
        'user_name': step['properties']['user_name']
    }
