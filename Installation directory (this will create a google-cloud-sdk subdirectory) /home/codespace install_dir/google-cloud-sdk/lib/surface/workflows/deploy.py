# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Creates or updates a workflow."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.workflows import validate
from googlecloudsdk.api_lib.workflows import workflows
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.workflows import flags
from googlecloudsdk.command_lib.workflows import hooks
from googlecloudsdk.core import log


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Deploy(base.CacheCommand):
  """Create or update a workflow."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To deploy a workflow with source code myWorkflow.yaml on Workflows:

            $ {command} my-workflow --source=myWorkflow.yaml

          You may also skip waiting for the operation to finish:

            $ {command} my-workflow --source=myWorkflow.yaml --async

          To specify a service account as the workflow identity:

            $ {command} my-workflow --source=myWorkflow.yaml --service-account=my-account@my-project.iam.gserviceaccount.com
          """,
  }

  @classmethod
  def Args(cls, parser):
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddWorkflowResourceArg(parser, verb='to deploy')
    flags.AddSourceArg(parser)
    flags.AddDescriptionArg(parser)
    flags.AddServiceAccountArg(parser)
    if cls.ReleaseTrack() is base.ReleaseTrack.GA:
      flags.AddKmsKeyFlags(parser)
      flags.AddWorkflowLoggingArg(parser)
      flags.AddUserEnvVarsFlags(parser)

  def Run(self, args):
    """Deploy a workflow."""
    hooks.print_default_location_warning(None, args, None)
    api_version = workflows.ReleaseTrackToApiVersion(self.ReleaseTrack())
    client = workflows.WorkflowsClient(api_version)
    workflow_ref = flags.ParseWorkflow(args)
    validate.WorkflowNameConforms(workflow_ref.Name())
    old_workflow = client.Get(workflow_ref)
    first_deployment = old_workflow is None
    workflow, updated_fields = client.BuildWorkflowFromArgs(
        args, old_workflow, self.ReleaseTrack(),
    )
    validate.ValidateWorkflow(workflow, first_deployment=first_deployment)
    if first_deployment:
      operation = client.Create(workflow_ref, workflow)
    else:
      if not updated_fields:
        log.status.Print('No updates provided, quitting as a no-op.')
        return None
      operation = client.Patch(workflow_ref, workflow, updated_fields)
    if args.async_:
      return operation
    else:
      return client.WaitForOperation(operation, workflow_ref)
