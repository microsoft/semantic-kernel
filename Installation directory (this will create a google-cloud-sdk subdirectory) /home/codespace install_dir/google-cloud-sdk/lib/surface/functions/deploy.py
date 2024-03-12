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
"""Creates or updates a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions import secrets_config
from googlecloudsdk.command_lib.functions import util
from googlecloudsdk.command_lib.functions.v1.deploy import command as command_v1
from googlecloudsdk.command_lib.functions.v1.deploy import labels_util
from googlecloudsdk.command_lib.functions.v2.deploy import command as command_v2
from googlecloudsdk.command_lib.functions.v2.deploy import env_vars_util
from googlecloudsdk.command_lib.util.args import labels_util as args_labels_util
from googlecloudsdk.core import log

_HOW_TO_DISABLE_CHANGE = (
    'You can disable this behavior by explicitly specifying the --no-gen2 flag'
    " or by setting the functions/gen2 config property to 'off'."
)

_LEARN_ABOUT_GEN_DIFFS = (
    'To learn more about the differences between 1st gen and 2nd gen functions,'
    ' visit:'
    '\nhttps://cloud.google.com/functions/docs/concepts/version-comparison'
)

_RECENT_DEFAULT_CHANGE = (
    'This function will be deployed as a 2nd gen function. This is a'
    ' recent change in the default behavior for newly created functions.'
    f'\n{_HOW_TO_DISABLE_CHANGE}\n{_LEARN_ABOUT_GEN_DIFFS}'
)

_UPCOMING_CHANGE_WARNING = (
    'In a future Cloud SDK release, new functions will be deployed as 2nd gen '
    ' functions by default. This is equivalent to currently deploying new '
    ' with the --gen2 flag. Existing 1st gen functions will not be impacted'
    ' and will continue to deploy as 1st gen functions.\nYou can preview this'
    ' behavior in beta. Alternatively,'
    f' {_HOW_TO_DISABLE_CHANGE[0].lower() + _HOW_TO_DISABLE_CHANGE[1:]}\n'
    f'{_LEARN_ABOUT_GEN_DIFFS}'
)


def _CommonArgs(parser, track):
  """Register base flags for this command."""
  # Add a positional "resource argument" for the name of the function
  flags.AddFunctionResourceArg(parser, 'to deploy')

  # Add `args.memory` as str. Converted at runtime to int for v1.
  # Add `args.cpu` as flag that requires `args.memory`
  flags.AddFunctionMemoryAndCpuFlags(parser)

  # Add args for function properties
  flags.AddAllowUnauthenticatedFlag(parser)
  flags.AddFunctionRetryFlag(parser)
  flags.AddFunctionTimeoutFlag(parser)
  flags.AddMaxInstancesFlag(parser)
  flags.AddMinInstancesFlag(parser)
  flags.AddRuntimeFlag(parser)
  flags.AddServiceAccountFlag(parser)
  args_labels_util.AddUpdateLabelsFlags(
      parser,
      extra_update_message=labels_util.NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE,
      extra_remove_message=labels_util.NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE,
  )

  # Add args for specifying the function source code
  flags.AddSourceFlag(parser)
  flags.AddStageBucketFlag(parser)
  flags.AddEntryPointFlag(parser)

  # Add args for specifying the function trigger
  flags.AddTriggerFlagGroup(parser)

  # Add args for specifying environment variables
  env_vars_util.AddUpdateEnvVarsFlags(parser)

  # Add flags for specifying build environment variables
  env_vars_util.AddBuildEnvVarsFlags(parser)

  # Add args for specifying ignore files to upload source
  flags.AddIgnoreFileFlag(parser)

  # Add args for base image automatic update policy
  flags.AddRuntimeUpdatePolicy(parser, track)

  # Add flags for CMEK
  flags.AddKMSKeyFlags(parser)
  flags.AddDockerRepositoryFlags(parser)

  # Add flags for secrets
  secrets_config.ConfigureFlags(parser)

  # Add flags for network settings
  flags.AddVPCConnectorMutexGroup(parser)
  flags.AddEgressSettingsFlag(parser)
  flags.AddIngressSettingsFlag(parser)
  flags.AddSecurityLevelFlag(parser)
  flags.AddBuildWorkerPoolMutexGroup(parser)

  # Configure flags for Artifact Registry
  flags.AddDockerRegistryFlags(parser)

  # Add additional flags for GCFv2
  flags.AddRunServiceAccountFlag(parser)
  flags.AddTriggerLocationFlag(parser)
  flags.AddTriggerServiceAccountFlag(parser)
  flags.AddGen2Flag(parser)
  flags.AddServeAllTrafficLatestRevisionFlag(parser)
  flags.AddConcurrencyFlag(parser)

  # Add flag for user-provided Cloud Build Service Account
  flags.AddBuildServiceAccountFlag(parser, track)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Deploy(util.FunctionResourceCommand, base.Command):
  """Create or update a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, base.ReleaseTrack.GA)

  def _RunV1(self, args):
    if not flags.ShouldUseGen1():
      # For all gen 1 deploys (even updates, per PM input) that don't explicitly
      # set --no-gen2, warn about upcoming gen 1 default changes
      log.status.Print(_UPCOMING_CHANGE_WARNING)
    return command_v1.Run(args, track=self.ReleaseTrack())

  def _RunV2(self, args):
    if not self._v2_function and not flags.ShouldUseGen2():
      # Gen2 function creation without an explicit generation specification.
      log.status.Print(_RECENT_DEFAULT_CHANGE)
    return command_v2.Run(args, self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeployBeta(Deploy):
  """Create or update a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Register alpha (and implicitly beta) flags for this command."""
    _CommonArgs(parser, base.ReleaseTrack.BETA)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeployAlpha(DeployBeta):
  """Create or update a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Register alpha (and implicitly beta) flags for this command."""
    _CommonArgs(parser, base.ReleaseTrack.ALPHA)

    # Flags specific to the Alpha track
    flags.AddBuildpackStackFlag(parser)


DETAILED_HELP = {
    'EXAMPLES': """\
        To deploy a function that is triggered by write events on the document
        ``/messages/{pushId}'', run:

          $ {command} my_function --runtime=python37 --trigger-event=providers/cloud.firestore/eventTypes/document.write --trigger-resource=projects/project_id/databases/(default)/documents/messages/{pushId}

        See https://cloud.google.com/functions/docs/calling for more details
        of using other types of resource as triggers.
        """
}

Deploy.detailed_help = DETAILED_HELP
DeployBeta.detailed_help = DETAILED_HELP
DeployAlpha.detailed_help = DETAILED_HELP
