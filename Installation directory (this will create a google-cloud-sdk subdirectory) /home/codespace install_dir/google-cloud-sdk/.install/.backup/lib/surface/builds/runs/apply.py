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
"""Create a PipelineRun/TaskRun."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_exceptions
from googlecloudsdk.api_lib.cloudbuild.v2 import client_util
from googlecloudsdk.api_lib.cloudbuild.v2 import input_util
from googlecloudsdk.api_lib.cloudbuild.v2 import pipeline_input_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import run_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a PipelineRun/TaskRun."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser = run_flags.AddsCreateFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = client_util.GetClientInstance()
    messages = client_util.GetMessagesModule()

    yaml_data = input_util.LoadYamlFromPath(args.file)
    run_type = yaml_data['kind']
    run_id = yaml_data['metadata']['name']

    parent = args.CONCEPTS.region.Parse().RelativeName()

    if run_type == 'PipelineRun':
      pipeline_run = pipeline_input_util.TektonYamlDataToPipelineRun(
          yaml_data)
      operation = client.projects_locations_pipelineRuns.Create(
          messages.CloudbuildProjectsLocationsPipelineRunsCreateRequest(
              parent=parent,
              pipelineRun=pipeline_run,
              pipelineRunId=run_id,
          ))
      operation_ref = resources.REGISTRY.ParseRelativeName(
          operation.name, collection='cloudbuild.projects.locations.operations')
      created_pipeline_run = waiter.WaitFor(
          waiter.CloudOperationPoller(client.projects_locations_pipelineRuns,
                                      client.projects_locations_operations),
          operation_ref, 'Creating PipelineRun')

      pipeline_run_ref = resources.REGISTRY.Parse(
          created_pipeline_run.name,
          collection='cloudbuild.projects.locations.pipelineRuns',
          api_version=client_util.RELEASE_TRACK_TO_API_VERSION[
              self.ReleaseTrack()],
      )

      log.CreatedResource(pipeline_run_ref)
      return created_pipeline_run
    elif run_type == 'TaskRun':
      task_run = pipeline_input_util.TektonYamlDataToTaskRun(
          yaml_data)
      operation = client.projects_locations_taskRuns.Create(
          messages.CloudbuildProjectsLocationsTaskRunsCreateRequest(
              parent=parent,
              taskRun=task_run,
              taskRunId=run_id,
          ))
      operation_ref = resources.REGISTRY.ParseRelativeName(
          operation.name, collection='cloudbuild.projects.locations.operations')
      created_task_run = waiter.WaitFor(
          waiter.CloudOperationPoller(client.projects_locations_taskRuns,
                                      client.projects_locations_operations),
          operation_ref, 'Creating TaskRun')

      task_run_ref = resources.REGISTRY.Parse(
          created_task_run.name,
          collection='cloudbuild.projects.locations.taskRuns',
          api_version=client_util.RELEASE_TRACK_TO_API_VERSION[
              self.ReleaseTrack()],
      )

      log.CreatedResource(task_run_ref)
      return created_task_run
    else:
      raise cloudbuild_exceptions.InvalidYamlError(
          'Requested resource type {r} not supported'.format(r=run_type))

