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
"""Run a Workflow."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild.v2 import client_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import run_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Run a Workflow."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument('WORKFLOW_ID', help='The ID of the Workflow.')
    parser.add_argument(
        '--params',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(),
        help='Params to run Workflow with.')
    run_flags.AddsRegionResourceArg(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = client_util.GetClientInstance()
    messages = client_util.GetMessagesModule()

    region_ref = args.CONCEPTS.region.Parse()
    parent = region_ref.RelativeName()
    workflow_name = '%s/workflows/%s' % (parent, args.WORKFLOW_ID)
    run_workflow_req = messages.RunWorkflowRequest()

    # Add params ('key1=val1,key2=val2') to RunWorkflow request.
    if args.params:
      params = []
      for key, value in args.params.items():
        param = messages.Param(
            name=key,
            value=messages.ParamValue(
                type=messages.ParamValue.TypeValueValuesEnum('STRING'),
                stringVal=value,
            ))
        params.append(param)
      run_workflow_req.params = params

    # Call RunWorkflow. Initial not-Done LRO immediately returned.
    run_workflow_operation = client.projects_locations_workflows.Run(
        messages.CloudbuildProjectsLocationsWorkflowsRunRequest(
            name=workflow_name,
            runWorkflowRequest=run_workflow_req,
        ))
    run_workflow_operation_name = run_workflow_operation.name
    run_workflow_operation_ref = resources.REGISTRY.ParseRelativeName(
        run_workflow_operation_name,
        collection='cloudbuild.projects.locations.operations')

    # Wait for RunWorkflow LRO to be marked as Done.
    # Underlying, this also waits for the CreatePipelineRun LRO to be Done.
    waiter.WaitFor(
        waiter.CloudOperationPoller(client.projects_locations_workflows,
                                    client.projects_locations_operations),
        run_workflow_operation_ref, 'Running workflow {}'.format(workflow_name))

    # Re-fetch the RunWorkflow LRO now that it is done.
    run_workflow_operation_done = client.projects_locations_operations.Get(
        messages.CloudbuildProjectsLocationsOperationsGetRequest(
            name=run_workflow_operation_name))

    # Extract the PipelineRunId from the RunWorkflowCustomOperationMetadata.
    pipeline_run_id = ''
    for additional_property in run_workflow_operation_done.metadata.additionalProperties:
      if additional_property.key == 'pipelineRunId':
        pipeline_run_id = additional_property.value.string_value

    # Log ran/created resources and return Done RunWorkflow LRO.
    log.status.Print(
        'View run:'
        ' https://console.cloud.google.com/cloud-build/runs/{region}/{run}?project={project}'
        .format(
            region=region_ref.Name(),
            run=pipeline_run_id,
            project=properties.VALUES.core.project.Get(required=True),
        )
    )
    return run_workflow_operation_done
