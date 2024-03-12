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
"""Cancel a PipelineRun/TaskRun."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild.v2 import client_util as v2_client_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import run_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Cancel(base.Command):
  """Cancel a PipelineRun/TaskRun."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser = run_flags.AddsRunFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    project = region_ref.AsDict()['projectsId']
    run_id = args.RUN_ID

    if args.type == 'pipelinerun':
      client = v2_client_util.GetClientInstance()
      messages = v2_client_util.GetMessagesModule()
      pipeline_run_resource = resources.REGISTRY.Parse(
          run_id,
          collection='cloudbuild.projects.locations.pipelineRuns',
          api_version='v2',
          params={
              'projectsId': project,
              'locationsId': region,
              'pipelineRunsId': run_id,
          })
      pipeline_run = messages.PipelineRun(
          pipelineRunStatus=messages.PipelineRun
          .PipelineRunStatusValueValuesEnum.PIPELINE_RUN_CANCELLED,)
      update_mask = 'pipelineRunStatus'
      operation = client.projects_locations_pipelineRuns.Patch(
          messages.CloudbuildProjectsLocationsPipelineRunsPatchRequest(
              name=pipeline_run_resource.RelativeName(),
              pipelineRun=pipeline_run,
              updateMask=update_mask,
          ))
      operation_ref = resources.REGISTRY.ParseRelativeName(
          operation.name, collection='cloudbuild.projects.locations.operations')
      updated_pipeline_run = waiter.WaitFor(
          waiter.CloudOperationPoller(client.projects_locations_pipelineRuns,
                                      client.projects_locations_operations),
          operation_ref, 'Cancelling PipelineRun')
      log.status.Print('Cancelled PipelineRun {0}'.format(run_id))
      return updated_pipeline_run
    elif args.type == 'taskrun':
      client = v2_client_util.GetClientInstance()
      messages = v2_client_util.GetMessagesModule()
      task_run_resource = resources.REGISTRY.Parse(
          run_id,
          collection='cloudbuild.projects.locations.taskRuns',
          api_version='v2',
          params={
              'projectsId': project,
              'locationsId': region,
              'taskRunsId': run_id,
          })
      task_run = messages.TaskRun(
          taskRunStatus=messages.TaskRun.TaskRunStatusValueValuesEnum
          .TASK_RUN_CANCELLED,)
      update_mask = 'taskRunStatus'
      operation = client.projects_locations_taskRuns.Patch(
          messages.CloudbuildProjectsLocationsTaskRunsPatchRequest(
              name=task_run_resource.RelativeName(),
              taskRun=task_run,
              updateMask=update_mask,
          ))
      operation_ref = resources.REGISTRY.ParseRelativeName(
          operation.name, collection='cloudbuild.projects.locations.operations')
      updated_task_run = waiter.WaitFor(
          waiter.CloudOperationPoller(client.projects_locations_taskRuns,
                                      client.projects_locations_operations),
          operation_ref, 'Cancelling TaskRun')
      log.status.Print('Cancelled TaskRun {0}'.format(run_id))
      return updated_task_run
