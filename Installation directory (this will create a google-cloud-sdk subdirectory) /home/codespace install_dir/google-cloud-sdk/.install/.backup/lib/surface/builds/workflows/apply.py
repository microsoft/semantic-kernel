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
"""Create a Workflow."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild.v2 import client_util
from googlecloudsdk.api_lib.cloudbuild.v2 import input_util
from googlecloudsdk.api_lib.cloudbuild.v2 import workflow_input_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import run_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Workflow."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        '--file',
        required=True,
        help='The YAML file to use as the Workflow configuration file.')
    run_flags.AddsRegionResourceArg(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = client_util.GetClientInstance()
    messages = client_util.GetMessagesModule()

    yaml_data = input_util.LoadYamlFromPath(args.file)
    workflow = workflow_input_util.CloudBuildYamlDataToWorkflow(yaml_data)

    region_ref = args.CONCEPTS.region.Parse()
    parent = region_ref.RelativeName()
    workflow_id = yaml_data['name']
    name = '%s/workflows/%s' % (parent, workflow_id)

    # Update workflow (or create if missing).
    workflow.name = name
    update_operation = client.projects_locations_workflows.Patch(
        messages.CloudbuildProjectsLocationsWorkflowsPatchRequest(
            name=name, workflow=workflow, allowMissing=True))

    update_operation_ref = resources.REGISTRY.ParseRelativeName(
        update_operation.name,
        collection='cloudbuild.projects.locations.operations')

    updated_workflow = waiter.WaitFor(
        waiter.CloudOperationPoller(client.projects_locations_workflows,
                                    client.projects_locations_operations),
        update_operation_ref,
        'Applying {file} as workflow {name}'.format(file=args.file, name=name))

    log.status.Print('Applied workflow {}.'.format(updated_workflow.name))
    return updated_workflow
