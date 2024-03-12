# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Shows the logs for an in-progress or completed PipelineRun/TaskRun/Build."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util as v1_client_util
from googlecloudsdk.api_lib.cloudbuild import logs as v1_logs
from googlecloudsdk.api_lib.cloudbuild.v2 import client_util as v2_client_util
from googlecloudsdk.api_lib.cloudbuild.v2 import logs as v2_logs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import run_flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Log(base.Command):
  """Show the logs for a PipelineRun/TaskRun/Build."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        '--stream',
        help=('If a run is ongoing, stream the logs to stdout until '
              'the run completes.'),
        default=False,
        action='store_true')
    parser = run_flags.AddsRunFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    project = properties.VALUES.core.project.Get(required=True)
    run_id = args.RUN_ID
    if args.type == 'build':
      client = v1_client_util.GetClientInstance()
      messages = v1_client_util.GetMessagesModule()
      build_ref = resources.REGISTRY.Parse(
          run_id,
          params={
              'projectsId': project,
              'locationsId': region,
              'buildsId': run_id,
          },
          collection='cloudbuild.projects.locations.builds')
      logger = v1_logs.CloudBuildClient(client, messages, True)
      if args.stream:
        logger.Stream(build_ref)
        return
      logger.PrintLog(build_ref)
      return
    else:
      client = v2_client_util.GetClientInstance()
      messages = v2_client_util.GetMessagesModule()
      if args.type == 'pipelinerun':
        pipeline_run_resource = resources.REGISTRY.Parse(
            run_id,
            collection='cloudbuild.projects.locations.pipelineRuns',
            api_version='v2',
            params={
                'projectsId': project,
                'locationsId': region,
                'pipelineRunsId': run_id,
            })
        run_id = pipeline_run_resource.Name()
      else:
        task_run_resource = resources.REGISTRY.Parse(
            run_id,
            collection='cloudbuild.projects.locations.taskRuns',
            api_version='v2',
            params={
                'projectsId': project,
                'locationsId': region,
                'taskRunsId': run_id,
            })
        run_id = task_run_resource.Name()
      logger = v2_logs.CloudBuildLogClient()
      if args.stream:
        logger.Stream(project, region, run_id, args.type)
        return
      logger.PrintLog(project, region, run_id, args.type)
      return
