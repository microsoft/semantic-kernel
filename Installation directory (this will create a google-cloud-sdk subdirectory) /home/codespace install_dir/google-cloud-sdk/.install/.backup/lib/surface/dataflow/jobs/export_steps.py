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

"""Implementation of gcloud dataflow jobs export-steps command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.api_lib.dataflow import step_graph
from googlecloudsdk.api_lib.dataflow import step_json
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import job_utils
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ExportSteps(base.Command):
  """Exports information about the steps for the given job.

  The only currently supported format is to a GraphViz dot file.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    job_utils.ArgsForJobRef(parser)

  def Run(self, args):
    """Runs the command.

    Args:
      args: All the arguments that were provided to this command invocation.

    Returns:
      An iterator over the steps in the given job.
    """
    job_ref = job_utils.ExtractJobRef(args)
    return step_json.ExtractSteps(
        apis.Jobs.Get(
            job_ref.jobId,
            project_id=job_ref.projectId,
            region_id=job_ref.location,
            view=apis.Jobs.GET_REQUEST.ViewValueValuesEnum.JOB_VIEW_ALL))

  def Display(self, args, steps):
    """This method is called to print the result of the Run() method.

    Args:
      args: all the arguments that were provided to this command invocation.
      steps: The step information returned from Run().
    """
    if steps:
      for line in step_graph.YieldGraphviz(steps, 'StepGraph'):
        log.out.write(line)
        log.out.write('\n')
