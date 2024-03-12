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
"""Command for running jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import messages_util
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core.console import progress_tracker


class Execute(base.Command):
  """Execute a job."""

  detailed_help = {
      'DESCRIPTION': """
          {description}
          """,
      'EXAMPLES': """
          To execute a job:

              $ {command} my-job
          """,
  }

  @staticmethod
  def Args(parser):
    job_presentation = presentation_specs.ResourcePresentationSpec(
        'JOB',
        resource_args.GetJobResourceSpec(prompt=True),
        'Job to execute.',
        required=True,
        prefixes=False,
    )
    concept_parsers.ConceptParser([job_presentation]).AddToParser(parser)
    polling_group = parser.add_mutually_exclusive_group()
    flags.AddAsyncFlag(polling_group)
    flags.AddWaitForCompletionFlag(polling_group)
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')
    flags.AddTaskTimeoutFlags(parser, for_execution_overrides=True)
    flags.AddTasksFlag(parser, for_execution_overrides=True)
    flags.AddArgsFlag(parser, for_execution_overrides=True)
    flags.AddOverrideEnvVarsFlag(parser)

  def Run(self, args):
    """Execute a Job on Cloud Run."""
    job_ref = args.CONCEPTS.job.Parse()
    flags.ValidateResource(job_ref)
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    with serverless_operations.Connect(conn_context) as operations:
      with progress_tracker.StagedProgressTracker(
          'Creating execution...',
          stages.ExecutionStages(include_completion=args.wait),
          failure_message='Executing job failed',
          suppress_output=args.async_,
      ) as tracker:
        overrides = None
        if flags.HasExecutionOverrides(args):
          config_overrides = flags.GetRunJobConfigurationOverrides(args)
          operations.ValidateConfigOverrides(job_ref, config_overrides)
          container_overrides = []
          if flags.HasContainerOverrides(args):
            # If args list has been explicitly provided as an empty list,
            # this is to clear out the existing args list.
            clear_args = (
                flags.FlagIsExplicitlySet(args, 'args') and not args.args
            )
            container_overrides = operations.GetContainerOverrides(
                args.update_env_vars, args.args, clear_args
            )
          overrides = operations.GetExecutionOverrides(
              args.tasks, args.task_timeout, container_overrides
          )
        e = operations.RunJob(
            job_ref,
            tracker,
            args.wait,
            args.async_,
            self.ReleaseTrack(),
            overrides
        )

      if args.async_:
        pretty_print.Success(
            'Execution [{{bold}}{execution}{{reset}}] is being'
            ' started asynchronously.'.format(execution=e.name)
        )
      else:
        operation = 'completed' if args.wait else 'started running'

        pretty_print.Success(
            'Execution [{{bold}}{execution}{{reset}}] has '
            'successfully {operation}.'.format(
                execution=e.name, operation=operation
            )
        )

      log.status.Print(
          messages_util.GetExecutionCreatedMessage(self.ReleaseTrack(), e)
      )
      return e
