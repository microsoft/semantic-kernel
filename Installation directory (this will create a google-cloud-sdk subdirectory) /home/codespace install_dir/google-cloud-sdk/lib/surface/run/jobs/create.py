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
"""Deploy a container to Cloud Run that will run to completion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.calliope import parser_errors as c_parser_errors
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import container_parser
from googlecloudsdk.command_lib.run import exceptions
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


EXAMPLE_JOB_IMAGE = 'us-docker.pkg.dev/cloudrun/container/job:latest'


def ContainerArgGroup():
  """Returns an argument group with all per-container deploy args."""

  help_text = """
Container Flags

  If the --container is specified the following arguments may only be specified after a --container flag.
"""
  group = base.ArgumentGroup(help=help_text)
  # Verify image flag is specified in Run function for better error message.
  group.AddArgument(flags.ImageArg(image=EXAMPLE_JOB_IMAGE, required=False))
  group.AddArgument(flags.MutexEnvVarsFlags())
  group.AddArgument(flags.MemoryFlag())
  group.AddArgument(flags.CpuFlag())
  group.AddArgument(flags.ArgsFlag())
  group.AddArgument(flags.SecretsFlags())
  group.AddArgument(flags.CommandFlag())
  group.AddArgument(flags.DependsOnFlag())

  return group


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  """Create a Cloud Run job."""

  detailed_help = {
      'DESCRIPTION': """\
          Creates a new Cloud Run job.
          """,
      'EXAMPLES': """\
          To deploy a new job `my-data-transformation` on Cloud Run:

              $ {command} my-data-transformation --image=us-docker.pkg.dev/project/image

          You may also omit the job name. Then a prompt will be displayed
          with a suggested default value:

              $ {command} --image=us-docker.pkg.dev/project/image
          """,
  }

  @staticmethod
  def CommonArgs(parser, add_container_args=True):
    # Flags not specific to any platform
    job_presentation = presentation_specs.ResourcePresentationSpec(
        'JOB',
        resource_args.GetJobResourceSpec(prompt=True),
        'Job to create.',
        required=True,
        prefixes=False,
    )
    if add_container_args:
      flags.AddImageArg(parser, image=EXAMPLE_JOB_IMAGE)
      flags.AddArgsFlag(parser)
      flags.AddCommandFlag(parser)
      flags.AddCpuFlag(parser, managed_only=True)
      flags.AddMemoryFlag(parser)
      flags.AddMutexEnvVarsFlagsForCreate(parser)
      flags.AddSetSecretsFlag(parser)
    flags.AddLabelsFlag(parser)
    flags.AddParallelismFlag(parser)
    flags.AddTasksFlag(parser)
    flags.AddMaxRetriesFlag(parser)
    flags.AddTaskTimeoutFlags(parser)
    flags.AddServiceAccountFlag(parser, managed_only=True)
    flags.AddSetCloudSQLFlag(parser)
    flags.AddVpcConnectorArg(parser)
    flags.AddEgressSettingsFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    flags.AddBinAuthzPolicyFlags(parser, with_clear=False)
    flags.AddBinAuthzBreakglassFlag(parser)
    flags.AddCmekKeyFlag(parser, with_clear=False)
    flags.AddSandboxArg(parser, hidden=True)
    flags.AddGeneralAnnotationFlags(parser)

    polling_group = parser.add_mutually_exclusive_group()
    flags.AddAsyncFlag(polling_group)

    execute_group = polling_group.add_argument_group(
        help='--async cannot be used if executing the job after the update.'
    )
    flags.AddWaitForCompletionFlag(execute_group, implies_execute_now=True)

    flags.AddExecuteNowFlag(execute_group)

    concept_parsers.ConceptParser([job_presentation]).AddToParser(parser)
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  @staticmethod
  def Args(parser):
    Create.CommonArgs(parser)

  def Run(self, args):
    """Deploy a Job to Cloud Run."""
    if flags.FlagIsExplicitlySet(args, 'containers'):
      containers = args.containers
      if len(containers) > 10:
        raise c_exceptions.InvalidArgumentException(
            '--container', 'Jobs may include at most 10 containers'
        )
      needs_image = {
          name: container
          for name, container in containers.items()
          if not container.IsSpecified('image')
      }
      if needs_image:
        raise exceptions.RequiredImageArgumentException(needs_image)
    elif not flags.FlagIsExplicitlySet(args, 'image'):
      raise c_parser_errors.RequiredError(argument='--image')

    job_ref = args.CONCEPTS.job.Parse()
    flags.ValidateResource(job_ref)

    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    changes = flags.GetJobConfigurationChanges(
        args,
        release_track=self.ReleaseTrack())
    changes.append(
        config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack())
    )

    execute_now = args.execute_now or args.wait
    execution = None

    with serverless_operations.Connect(conn_context) as operations:
      pretty_print.Info(
          messages_util.GetStartDeployMessage(
              conn_context, job_ref, 'Creating', 'job'
          )
      )
      if execute_now:
        header_msg = 'Creating and running job...'
      else:
        header_msg = 'Creating job...'
      with progress_tracker.StagedProgressTracker(
          header_msg,
          stages.JobStages(
              execute_now=execute_now, include_completion=args.wait
          ),
          failure_message='Job failed to deploy',
          suppress_output=args.async_,
      ) as tracker:
        job = operations.CreateJob(
            job_ref, changes, tracker, asyn=(args.async_ and not execute_now)
        )
        if execute_now:
          execution = operations.RunJob(
              job_ref, tracker, args.wait, args.async_, self.ReleaseTrack()
          )

      if args.async_ and not execute_now:
        pretty_print.Success(
            'Job [{{bold}}{job}{{reset}}] is being created '
            'asynchronously.'.format(job=job.name)
        )
      else:
        operation = 'been created'
        if args.wait:
          operation += ' and completed execution [{}]'.format(execution.name)
        elif execute_now:
          operation += ' and started running execution [{}]'.format(
              execution.name
          )

        pretty_print.Success(
            'Job [{{bold}}{job}{{reset}}] has successfully {operation}.'.format(
                job=job.name, operation=operation
            )
        )

      msg = ''
      if execute_now:
        msg += messages_util.GetExecutionCreatedMessage(
            self.ReleaseTrack(), execution
        )
        msg += '\n'
      msg += messages_util.GetRunJobMessage(
          self.ReleaseTrack(), job.name, repeat=execute_now
      )
      log.status.Print(msg)
      return job


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaCreate(Create):
  """Create a Cloud Run job."""

  @staticmethod
  def Args(parser):
    Create.CommonArgs(parser)
    flags.AddVpcNetworkGroupFlagsForCreate(parser, resource_kind='job')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaCreate(BetaCreate):
  """Create a Cloud Run job."""

  @staticmethod
  def Args(parser):
    Create.CommonArgs(parser, add_container_args=False)
    flags.AddVpcNetworkGroupFlagsForCreate(parser, resource_kind='job')
    flags.AddRuntimeFlag(parser)
    container_args = ContainerArgGroup()
    container_parser.AddContainerFlags(parser, container_args)
