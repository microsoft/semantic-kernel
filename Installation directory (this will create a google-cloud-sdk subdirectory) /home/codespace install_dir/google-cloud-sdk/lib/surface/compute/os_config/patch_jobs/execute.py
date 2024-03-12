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
"""Implements command to execute an OS patch on the specified VM instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.resource import resource_projector
import six


def _AddCommonInstanceFilterFlags(mutually_exclusive_group):
  """Adds instance filter flags to a mutually exclusive argument group."""
  mutually_exclusive_group.add_argument(
      '--instance-filter-all',
      action='store_true',
      help="""A filter that targets all instances in the project.""",
  )
  individual_filters_group = mutually_exclusive_group.add_group(help="""\
    Individual filters. The targeted instances must meet all criteria specified.
    """)
  individual_filters_group.add_argument(
      '--instance-filter-group-labels',
      action='append',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help="""\
      A filter that represents a label set. Targeted instances must have all
      specified labels in this set. For example, "env=prod and app=web".

      This flag can be repeated. Targeted instances must have at least one of
      these label sets. This allows targeting of disparate groups, for example,
      "(env=prod and app=web) or (env=staging and app=web)".""",
  )
  individual_filters_group.add_argument(
      '--instance-filter-zones',
      metavar='INSTANCE_FILTER_ZONES',
      type=arg_parsers.ArgList(),
      help="""\
      A filter that targets instances in any of the specified zones. Leave empty
      to target instances in any zone.""",
  )
  individual_filters_group.add_argument(
      '--instance-filter-names',
      metavar='INSTANCE_FILTER_NAMES',
      type=arg_parsers.ArgList(),
      help="""\
      A filter that targets instances of any of the specified names. Instances
      are specified by the URI in the form
      "zones/<ZONE>/instances/<INSTANCE_NAME>",
      "projects/<PROJECT_ID>/zones/<ZONE>/instances/<INSTANCE_NAME>", or
      "https://www.googleapis.com/compute/v1/projects/<PROJECT_ID>/zones/<ZONE>/instances/<INSTANCE_NAME>".
      """,
  )
  individual_filters_group.add_argument(
      '--instance-filter-name-prefixes',
      metavar='INSTANCE_FILTER_NAME_PREFIXES',
      type=arg_parsers.ArgList(),
      help="""\
      A filter that targets instances whose name starts with one of these
      prefixes. For example, "prod-".""",
  )


def _AddTopLevelArguments(parser):
  """Adds top-level argument flags for the Beta and GA tracks."""
  instance_filter_group = parser.add_mutually_exclusive_group(
      required=True,
      help='Filters for selecting which instances to patch:',
  )
  _AddCommonInstanceFilterFlags(instance_filter_group)


def _AddTopLevelArgumentsAlpha(parser):
  """Adds top-level argument flags for the Alpha track."""
  instance_filter_group = parser.add_mutually_exclusive_group(
      required=True,
      help='Filters for selecting which instances to patch:',
  )
  # TODO(b/145214199): Remove this flag
  instance_filter_group.add_argument(
      '--instance-filter',
      type=str,
      help="""\
      Filter expression for selecting the instances to patch. Patching supports
      the same filter mechanisms as `gcloud compute instances list`, allowing
      one to patch specific instances by name, zone, label, or other criteria.
      """,
      action=actions.DeprecationAction(
          '--instance-filter',
          warn="""\
          {flag_name} is deprecated; use individual filter flags instead. See
          the command help text for more details.""",
          removed=False,
          action='store'))
  _AddCommonInstanceFilterFlags(instance_filter_group)
  parser.add_argument(
      '--retry',
      action='store_true',
      help="""\
      Specifies whether to attempt to retry, within the duration window, if
      patching initially fails. If omitted, the agent uses its default retry
      strategy.""",
  )


def _AddPatchRolloutArguments(parser):
  """Adds top-level patch rollout arguments."""
  rollout_group = base.ArgumentGroup(
      mutex=False, help='Rollout configurations for this patch job:')
  rollout_group.AddArgument(
      base.ChoiceArgument(
          '--rollout-mode',
          help_str='Mode of the rollout.',
          choices={
              'zone-by-zone':
                  """\
              Patches are applied one zone at a time. The patch job begins in
              the region with the lowest number of targeted VMs. Within the
              region, patching begins in the zone with the lowest number of
              targeted VMs. If multiple regions (or zones within a region) have
              the same number of targeted VMs, a tie-breaker is achieved by
              sorting the regions or zones in alphabetical order.""",
              'concurrent-zones':
                  'Patches are applied to VMs in all zones at the same time.',
          },
      ))
  disruption_budget_group = base.ArgumentGroup(
      mutex=True,
      help="""\
      Disruption budget for this rollout. A running VM with an active agent is
      considered disrupted if its patching operation fails anytime between the
      time the agent is notified until the patch process completes.""")
  disruption_budget_group.AddArgument(
      base.Argument(
          '--rollout-disruption-budget',
          help='Number of VMs per zone to disrupt at any given moment.',
      ))
  disruption_budget_group.AddArgument(
      base.Argument(
          '--rollout-disruption-budget-percent',
          help="""\
          Percentage of VMs per zone to disrupt at any given moment. The number
          of VMs calculated from multiplying the percentage by the total number
          of VMs in a zone is rounded up.""",
      ))
  rollout_group.AddArgument(disruption_budget_group)
  rollout_group.AddToParser(parser)


def _AddCommonTopLevelArguments(parser):
  """Adds top-level argument flags for all tracks."""
  base.ASYNC_FLAG.AddToParser(parser)
  parser.add_argument(
      '--description', type=str, help='Textual description of the patch job.')
  parser.add_argument(
      '--display-name',
      type=str,
      help='Display name for this patch job. This does not have to be unique.',
  )
  parser.add_argument(
      '--dry-run',
      action='store_true',
      help="""\
      Whether to execute this patch job as a dry run. If this patch job is a dry
      run, instances are contacted, but the patch is not run.""",
  )
  parser.add_argument(
      '--duration',
      type=arg_parsers.Duration(),
      help="""\
      Total duration in which the patch job must complete. If the patch does not
      complete in this time, the process times out. While some instances might
      still be running the patch, they will not continue to work after
      completing the current step. See $ gcloud topic datetimes for information
      on specifying absolute time durations.

      If unspecified, the job stays active until all instances complete the
      patch.""",
  )
  base.ChoiceArgument(
      '--reboot-config',
      help_str='Post-patch reboot settings.',
      choices={
          'default':
              """\
          The agent decides if a reboot is necessary by checking signals such as
          registry keys or '/var/run/reboot-required'.""",
          'always':
              """Always reboot the machine after the update completes.""",
          'never':
              """Never reboot the machine after the update completes.""",
      },
  ).AddToParser(parser)


def _AddAptGroupArguments(parser):
  """Adds Apt setting flags."""
  apt_group = parser.add_group(help='Settings for machines running Apt:')
  apt_group.add_argument(
      '--apt-dist',
      action='store_true',
      help="""\
      If specified, machines running Apt use the `apt-get dist-upgrade` command;
      otherwise the `apt-get upgrade` command is used.""",
  )
  mutually_exclusive_group = apt_group.add_mutually_exclusive_group()
  mutually_exclusive_group.add_argument(
      '--apt-excludes',
      metavar='APT_EXCLUDES',
      type=arg_parsers.ArgList(),
      help="""List of packages to exclude from update.""",
  )
  mutually_exclusive_group.add_argument(
      '--apt-exclusive-packages',
      metavar='APT_EXCLUSIVE_PACKAGES',
      type=arg_parsers.ArgList(),
      help="""\
      An exclusive list of packages to be updated. These are the only packages
      that will be updated. If these packages are not installed, they will be
      ignored.""",
  )


def _AddWinGroupArguments(parser):
  """Adds Windows setting flags."""
  win_group = parser.add_mutually_exclusive_group(
      help='Settings for machines running Windows:')
  non_exclusive_group = win_group.add_group(help='Windows patch options')
  non_exclusive_group.add_argument(
      '--windows-classifications',
      metavar='WINDOWS_CLASSIFICATIONS',
      type=arg_parsers.ArgList(choices=[
          'critical', 'security', 'definition', 'driver', 'feature-pack',
          'service-pack', 'tool', 'update-rollup', 'update'
      ]),
      help="""\
      List of classifications to use to restrict the Windows update. Only
      patches of the given classifications are applied. If omitted, a default
      Windows update is performed. For more information on classifications,
      see: https://support.microsoft.com/en-us/help/824684""",
  )
  non_exclusive_group.add_argument(
      '--windows-excludes',
      metavar='WINDOWS_EXCLUDES',
      type=arg_parsers.ArgList(),
      help="""Optional list of Knowledge Base (KB) IDs to exclude from the
      update operation.""",
  )
  win_group.add_argument(
      '--windows-exclusive-patches',
      metavar='WINDOWS_EXCLUSIVE_PATCHES',
      type=arg_parsers.ArgList(),
      help="""\
      An exclusive list of Knowledge Base (KB) IDs to be updated. These are the
      only patches that will be updated.""",
  )


def _AddYumGroupArguments(parser):
  """Adds Yum setting flags."""
  yum_group = parser.add_mutually_exclusive_group(
      help='Settings for machines running Yum:')
  non_exclusive_group = yum_group.add_group(help='Yum patch options')
  non_exclusive_group.add_argument(
      '--yum-security',
      action='store_true',
      help="""\
      If specified, machines running Yum append the `--security` flag to the
      patch command.""",
  )
  non_exclusive_group.add_argument(
      '--yum-minimal',
      action='store_true',
      help="""\
      If specified, machines running Yum use the command `yum update-minimal`;
      otherwise the patch uses `yum-update`.""",
  )
  non_exclusive_group.add_argument(
      '--yum-excludes',
      metavar='YUM_EXCLUDES',
      type=arg_parsers.ArgList(),
      help="""\
      Optional list of packages to exclude from updating. If this argument is
      specified, machines running Yum exclude the given list of packages using
      the Yum `--exclude` flag.""",
  )
  yum_group.add_argument(
      '--yum-exclusive-packages',
      metavar='YUM_EXCLUSIVE_PACKAGES',
      type=arg_parsers.ArgList(),
      help="""\
      An exclusive list of packages to be updated. These are the only packages
      that will be updated. If these packages are not installed, they will be
      ignored.""",
  )


def _AddZypperGroupArguments(parser):
  """Adds Zypper setting flags."""
  zypper_group = parser.add_mutually_exclusive_group(
      help='Settings for machines running Zypper:')
  non_exclusive_group = zypper_group.add_group('Zypper patch options')
  non_exclusive_group.add_argument(
      '--zypper-categories',
      metavar='ZYPPER_CATEGORIES',
      type=arg_parsers.ArgList(),
      help="""\
      If specified, machines running Zypper install only patches with the
      specified categories. Categories include security, recommended, and
      feature.""",
  )
  non_exclusive_group.add_argument(
      '--zypper-severities',
      metavar='ZYPPER_SEVERITIES',
      type=arg_parsers.ArgList(),
      help="""\
      If specified, machines running Zypper install only patch with the
      specified severities. Severities include critical, important, moderate,
      and low.""",
  )
  non_exclusive_group.add_argument(
      '--zypper-with-optional',
      action='store_true',
      help="""\
      If specified, machines running Zypper add the `--with-optional` flag to
      `zypper patch`.""",
  )
  non_exclusive_group.add_argument(
      '--zypper-with-update',
      action='store_true',
      help="""\
      If specified, machines running Zypper add the `--with-update` flag to
      `zypper patch`.""",
  )
  non_exclusive_group.add_argument(
      '--zypper-excludes',
      metavar='ZYPPER_EXCLUDES',
      type=arg_parsers.ArgList(),
      help="""\
      List of Zypper patches to exclude from the patch job.
      """,
  )
  zypper_group.add_argument(
      '--zypper-exclusive-patches',
      metavar='ZYPPER_EXCLUSIVE_PATCHES',
      type=arg_parsers.ArgList(),
      help="""\
      An exclusive list of patches to be updated. These are the only patches
      that will be installed using the 'zypper patch patch:<patch_name>'
      command.""",
  )


def _AddPrePostStepArguments(parser):
  """Adds pre-/post-patch setting flags."""
  pre_patch_linux_group = parser.add_group(
      help='Pre-patch step settings for Linux machines:')
  pre_patch_linux_group.add_argument(
      '--pre-patch-linux-executable',
      help="""\
      A set of commands to run on a Linux machine before an OS patch begins.
      Commands must be supplied in a file. If the file contains a shell script,
      include the shebang line.

      The path to the file must be supplied in one of the following formats:

      An absolute path of the file on the local filesystem.

      A URI for a Google Cloud Storage object with a generation number.
      """,
  )
  pre_patch_linux_group.add_argument(
      '--pre-patch-linux-success-codes',
      type=arg_parsers.ArgList(element_type=int),
      metavar='PRE_PATCH_LINUX_SUCCESS_CODES',
      help="""\
      Additional exit codes that the executable can return to indicate a
      successful run. The default exit code for success is 0.""",
  )
  post_patch_linux_group = parser.add_group(
      help='Post-patch step settings for Linux machines:')
  post_patch_linux_group.add_argument(
      '--post-patch-linux-executable',
      help="""\
      A set of commands to run on a Linux machine after an OS patch completes.
      Commands must be supplied in a file. If the file contains a shell script,
      include the shebang line.

      The path to the file must be supplied in one of the following formats:

      An absolute path of the file on the local filesystem.

      A URI for a Google Cloud Storage object with a generation number.
      """,
  )
  post_patch_linux_group.add_argument(
      '--post-patch-linux-success-codes',
      type=arg_parsers.ArgList(element_type=int),
      metavar='POST_PATCH_LINUX_SUCCESS_CODES',
      help="""\
      Additional exit codes that the executable can return to indicate a
      successful run. The default exit code for success is 0.""",
  )

  pre_patch_windows_group = parser.add_group(
      help='Pre-patch step settings for Windows machines:')
  pre_patch_windows_group.add_argument(
      '--pre-patch-windows-executable',
      help="""\
      A set of commands to run on a Windows machine before an OS patch begins.
      Commands must be supplied in a file. If the file contains a PowerShell
      script, include the .ps1 file extension. The PowerShell script executes
      with flags `-NonInteractive`, `-NoProfile`, and `-ExecutionPolicy Bypass`.

      The path to the file must be supplied in one of the following formats:

      An absolute path of the file on the local filesystem.

      A URI for a Google Cloud Storage object with a generation number.
      """,
  )
  pre_patch_windows_group.add_argument(
      '--pre-patch-windows-success-codes',
      type=arg_parsers.ArgList(element_type=int),
      metavar='PRE_PATCH_WINDOWS_SUCCESS_CODES',
      help="""\
      Additional exit codes that the executable can return to indicate a
      successful run. The default exit code for success is 0.""",
  )

  post_patch_windows_group = parser.add_group(
      help='Post-patch step settings for Windows machines:')
  post_patch_windows_group.add_argument(
      '--post-patch-windows-executable',
      help="""\
      A set of commands to run on a Windows machine after an OS patch completes.
      Commands must be supplied in a file. If the file contains a PowerShell
      script, include the .ps1 file extension. The PowerShell script executes
      with flags `-NonInteractive`, `-NoProfile`, and `-ExecutionPolicy Bypass`.

      The path to the file must be supplied in one of the following formats:

      An absolute path of the file on the local filesystem.

      A URI for a Google Cloud Storage object with a generation number.
      """,
  )
  post_patch_windows_group.add_argument(
      '--post-patch-windows-success-codes',
      type=arg_parsers.ArgList(element_type=int),
      metavar='POST_PATCH_WINDOWS_SUCCESS_CODES',
      help="""\
      Additional exit codes that the executable can return to indicate a
      successful run. The default exit code for success is 0.""",
  )


def _AddPatchConfigArguments(parser):
  """Adds all patch config argument flags."""
  _AddAptGroupArguments(parser)
  _AddYumGroupArguments(parser)
  _AddWinGroupArguments(parser)
  _AddZypperGroupArguments(parser)
  _AddPrePostStepArguments(parser)
  parser.add_argument(
      '--mig-instances-allowed',
      action='store_true',
      help="""\
        If set, patching of VMs that are part of a managed instance group (MIG) is allowed.""",
  )


def _CreateAptSettings(args, messages):
  """Creates an AptSettings message from input arguments."""
  if not any([args.apt_dist, args.apt_excludes, args.apt_exclusive_packages]):
    return None

  return messages.AptSettings(
      type=messages.AptSettings.TypeValueValuesEnum.DIST if args.apt_dist else
      messages.AptSettings.TypeValueValuesEnum.TYPE_UNSPECIFIED,
      excludes=args.apt_excludes if args.apt_excludes else [],
      exclusivePackages=args.apt_exclusive_packages
      if args.apt_exclusive_packages else [])


def _CreateWindowsUpdateSettings(args, messages):
  """Creates a WindowsUpdateSettings message from input arguments."""
  if not any([
      args.windows_classifications, args.windows_excludes,
      args.windows_exclusive_patches
  ]):
    return None

  enums = messages.WindowsUpdateSettings.ClassificationsValueListEntryValuesEnum
  classifications = [
      arg_utils.ChoiceToEnum(c, enums) for c in args.windows_classifications
  ] if args.windows_classifications else []
  return messages.WindowsUpdateSettings(
      classifications=classifications,
      excludes=args.windows_excludes if args.windows_excludes else [],
      exclusivePatches=args.windows_exclusive_patches
      if args.windows_exclusive_patches else [],
  )


def _CreateYumSettings(args, messages):
  """Creates a YumSettings message from input arguments."""
  if not any([
      args.yum_excludes, args.yum_minimal, args.yum_security,
      args.yum_exclusive_packages
  ]):
    return None

  return messages.YumSettings(
      excludes=args.yum_excludes if args.yum_excludes else [],
      minimal=args.yum_minimal,
      security=args.yum_security,
      exclusivePackages=args.yum_exclusive_packages
      if args.yum_exclusive_packages else [],
  )


def _CreateZypperSettings(args, messages):
  """Creates a ZypperSettings message from input arguments."""
  if not any([
      args.zypper_categories, args.zypper_severities, args.zypper_with_optional,
      args.zypper_with_update, args.zypper_excludes,
      args.zypper_exclusive_patches
  ]):
    return None

  return messages.ZypperSettings(
      categories=args.zypper_categories if args.zypper_categories else [],
      severities=args.zypper_severities if args.zypper_severities else [],
      withOptional=args.zypper_with_optional,
      withUpdate=args.zypper_with_update,
      excludes=args.zypper_excludes if args.zypper_excludes else [],
      exclusivePatches=args.zypper_exclusive_patches
      if args.zypper_exclusive_patches else [],
  )


def _GetWindowsExecStepConfigInterpreter(messages, path):
  """Returns the ExecStepConfig interpreter based on file path."""
  if path.endswith('.ps1'):
    return messages.ExecStepConfig.InterpreterValueValuesEnum.POWERSHELL
  else:
    return messages.ExecStepConfig.InterpreterValueValuesEnum.SHELL


def _CreateExecStepConfig(messages, arg_name, path, allowed_success_codes,
                          is_windows):
  """Creates an ExecStepConfig message from input arguments."""
  interpreter = messages.ExecStepConfig.InterpreterValueValuesEnum.INTERPRETER_UNSPECIFIED
  gcs_params = osconfig_command_utils.GetGcsParams(arg_name, path)
  if gcs_params:
    if is_windows:
      interpreter = _GetWindowsExecStepConfigInterpreter(
          messages, gcs_params['object'])
    return messages.ExecStepConfig(
        gcsObject=messages.GcsObject(
            bucket=gcs_params['bucket'],
            object=gcs_params['object'],
            generationNumber=gcs_params['generationNumber'],
        ),
        allowedSuccessCodes=allowed_success_codes
        if allowed_success_codes else [],
        interpreter=interpreter,
    )
  else:
    if is_windows:
      interpreter = _GetWindowsExecStepConfigInterpreter(messages, path)
    return messages.ExecStepConfig(
        localPath=path,
        allowedSuccessCodes=allowed_success_codes
        if allowed_success_codes else [],
        interpreter=interpreter,
    )


def _ValidatePrePostPatchStepArgs(executable_arg_name, executable_arg,
                                  success_codes_arg_name, success_codes_arg):
  """Validates the relation between pre-/post-patch setting flags."""
  if success_codes_arg and not executable_arg:
    raise exceptions.InvalidArgumentException(
        success_codes_arg_name,
        '[{}] must also be specified.'.format(executable_arg_name))


def _CreatePrePostPatchStepSettings(args, messages, is_pre_patch_step):
  """Creates an ExecStep message from input arguments."""
  if is_pre_patch_step:
    if not any([
        args.pre_patch_linux_executable, args.pre_patch_linux_success_codes,
        args.pre_patch_windows_executable, args.pre_patch_windows_success_codes
    ]):
      return None

    _ValidatePrePostPatchStepArgs('pre-patch-linux-executable',
                                  args.pre_patch_linux_executable,
                                  'pre-patch-linux-success-codes',
                                  args.pre_patch_linux_success_codes)
    _ValidatePrePostPatchStepArgs('pre-patch-windows-executable',
                                  args.pre_patch_windows_executable,
                                  'pre-patch-windows-success-codes',
                                  args.pre_patch_windows_success_codes)

    pre_patch_linux_step_config = pre_patch_windows_step_config = None
    if args.pre_patch_linux_executable:
      pre_patch_linux_step_config = _CreateExecStepConfig(
          messages,
          'pre-patch-linux-executable',
          args.pre_patch_linux_executable,
          args.pre_patch_linux_success_codes,
          is_windows=False)
    if args.pre_patch_windows_executable:
      pre_patch_windows_step_config = _CreateExecStepConfig(
          messages,
          'pre-patch-windows-executable',
          args.pre_patch_windows_executable,
          args.pre_patch_windows_success_codes,
          is_windows=True)
    return messages.ExecStep(
        linuxExecStepConfig=pre_patch_linux_step_config,
        windowsExecStepConfig=pre_patch_windows_step_config,
    )
  else:
    if not any([
        args.post_patch_linux_executable, args.post_patch_linux_success_codes,
        args.post_patch_windows_executable,
        args.post_patch_windows_success_codes
    ]):
      return None

    _ValidatePrePostPatchStepArgs('post-patch-linux-executable',
                                  args.post_patch_linux_executable,
                                  'post-patch-linux-success-codes',
                                  args.post_patch_linux_success_codes)
    _ValidatePrePostPatchStepArgs('post-patch-windows-executable',
                                  args.post_patch_windows_executable,
                                  'post-patch-windows-success-codes',
                                  args.post_patch_windows_success_codes)

    post_patch_linux_step_config = post_patch_windows_step_config = None
    if args.post_patch_linux_executable:
      post_patch_linux_step_config = _CreateExecStepConfig(
          messages,
          'post-patch-linux-executable',
          args.post_patch_linux_executable,
          args.post_patch_linux_success_codes,
          is_windows=False)
    if args.post_patch_windows_executable:
      post_patch_windows_step_config = _CreateExecStepConfig(
          messages,
          'post-patch-windows-executable',
          args.post_patch_windows_executable,
          args.post_patch_windows_success_codes,
          is_windows=True)
    return messages.ExecStep(
        linuxExecStepConfig=post_patch_linux_step_config,
        windowsExecStepConfig=post_patch_windows_step_config,
    )


def _CreateProgressTracker(patch_job_name):
  """Creates a progress tracker to display patch status synchronously."""
  stages = [
      progress_tracker.Stage(
          'Generating instance details...', key='pre-summary'),
      progress_tracker.Stage(
          'Reporting instance details...', key='with-summary')
  ]
  return progress_tracker.StagedProgressTracker(
      message='Executing patch job [{0}]'.format(patch_job_name), stages=stages)


def _CreateExecutionUpdateMessage(percent_complete, instance_details_json):
  """Constructs a message to be displayed during synchronous execute."""
  instance_states = {
      state: 0 for state in osconfig_command_utils.InstanceDetailsStates
  }

  for key, state in osconfig_command_utils.INSTANCE_DETAILS_KEY_MAP.items():
    num_instances = int(
        instance_details_json[key]) if key in instance_details_json else 0
    instance_states[state] = instance_states[state] + num_instances

  instance_details_str = ', '.join([
      '{} {}'.format(num, state.name.lower())
      for state, num in instance_states.items()
  ])
  return '{:.1f}% complete with {}'.format(percent_complete,
                                           instance_details_str)


def _UpdateProgressTracker(tracker, patch_job, unused_status):
  """Updates the progress tracker on screen based on patch job details.

  Args:
    tracker: Progress tracker to be updated.
    patch_job: Patch job being executed.
  """
  details_json = resource_projector.MakeSerializable(
      patch_job.instanceDetailsSummary)
  if not details_json or details_json == '{}':
    if not tracker.IsRunning('pre-summary'):
      tracker.StartStage('pre-summary')
    else:
      tracker.UpdateStage('pre-summary', 'Please wait...')
  else:
    details_str = _CreateExecutionUpdateMessage(patch_job.percentComplete,
                                                details_json)
    if tracker.IsRunning('pre-summary'):
      tracker.CompleteStage('pre-summary', 'Done!')
      tracker.StartStage('with-summary')
      tracker.UpdateStage('with-summary', details_str)
    else:
      tracker.UpdateStage('with-summary', details_str)


def _GetDuration(args):
  """Returns a formatted duration string."""
  return six.text_type(args.duration) + 's' if args.duration else None


def _CreatePatchConfig(args, messages):
  """Creates a PatchConfig message from input arguments."""
  reboot_config = getattr(
      messages.PatchConfig.RebootConfigValueValuesEnum,
      args.reboot_config.upper()) if args.reboot_config else None

  return messages.PatchConfig(
      rebootConfig=reboot_config,
      apt=_CreateAptSettings(args, messages),
      windowsUpdate=_CreateWindowsUpdateSettings(args, messages),
      yum=_CreateYumSettings(args, messages),
      zypper=_CreateZypperSettings(args, messages),
      preStep=_CreatePrePostPatchStepSettings(
          args, messages, is_pre_patch_step=True),
      postStep=_CreatePrePostPatchStepSettings(
          args, messages, is_pre_patch_step=False),
      migInstancesAllowed=args.mig_instances_allowed,
  )


def _CreatePatchInstanceFilter(messages, filter_all, filter_group_labels,
                               filter_zones, filter_names,
                               filter_name_prefixes):
  """Creates a PatchInstanceFilter message from its components."""
  group_labels = []
  for group_label in filter_group_labels:
    pairs = []
    for key, value in group_label.items():
      pairs.append(
          messages.PatchInstanceFilterGroupLabel.LabelsValue.AdditionalProperty(
              key=key, value=value))
    group_labels.append(
        messages.PatchInstanceFilterGroupLabel(
            labels=messages.PatchInstanceFilterGroupLabel.LabelsValue(
                additionalProperties=pairs)))

  return messages.PatchInstanceFilter(
      all=filter_all,
      groupLabels=group_labels,
      zones=filter_zones,
      instances=filter_names,
      instanceNamePrefixes=filter_name_prefixes,
  )


def _CreatePatchRollout(args, messages):
  """Creates a PatchRollout message from input arguments."""
  if not any([
      args.rollout_mode, args.rollout_disruption_budget,
      args.rollout_disruption_budget_percent
  ]):
    return None

  if args.rollout_mode and not (args.rollout_disruption_budget or
                                args.rollout_disruption_budget_percent):
    raise exceptions.InvalidArgumentException(
        'rollout-mode',
        '[rollout-disruption-budget] or [rollout-disruption-budget-percent] '
        'must also be specified.')

  if args.rollout_disruption_budget and not args.rollout_mode:
    raise exceptions.InvalidArgumentException(
        'rollout-disruption-budget', '[rollout-mode] must also be specified.')

  if args.rollout_disruption_budget_percent and not args.rollout_mode:
    raise exceptions.InvalidArgumentException(
        'rollout-disruption-budget-percent',
        '[rollout-mode] must also be specified.')

  rollout_modes = messages.PatchRollout.ModeValueValuesEnum
  return messages.PatchRollout(
      mode=arg_utils.ChoiceToEnum(args.rollout_mode, rollout_modes),
      disruptionBudget=messages.FixedOrPercent(
          fixed=int(args.rollout_disruption_budget)
          if args.rollout_disruption_budget else None,
          percent=int(args.rollout_disruption_budget_percent)
          if args.rollout_disruption_budget_percent else None))


def _CreateExecuteRequest(messages, project, description, dry_run, duration,
                          patch_config, patch_rollout, display_name, filter_all,
                          filter_group_labels, filter_zones, filter_names,
                          filter_name_prefixes):
  """Creates an ExecuteRequest message for the Beta track."""
  patch_instance_filter = _CreatePatchInstanceFilter(
      messages,
      filter_all,
      filter_group_labels,
      filter_zones,
      filter_names,
      filter_name_prefixes,
  )

  if patch_rollout:
    return messages.OsconfigProjectsPatchJobsExecuteRequest(
        executePatchJobRequest=messages.ExecutePatchJobRequest(
            description=description,
            displayName=display_name,
            dryRun=dry_run,
            duration=duration,
            instanceFilter=patch_instance_filter,
            patchConfig=patch_config,
            rollout=patch_rollout,
        ),
        parent=osconfig_command_utils.GetProjectUriPath(project))
  else:
    return messages.OsconfigProjectsPatchJobsExecuteRequest(
        executePatchJobRequest=messages.ExecutePatchJobRequest(
            description=description,
            displayName=display_name,
            dryRun=dry_run,
            duration=duration,
            instanceFilter=patch_instance_filter,
            patchConfig=patch_config,
        ),
        parent=osconfig_command_utils.GetProjectUriPath(project))


def _CreateExecuteRequestAlpha(messages, project, description, dry_run,
                               duration, patch_config, patch_rollout,
                               display_name, filter_all, filter_group_labels,
                               filter_zones, filter_names, filter_name_prefixes,
                               filter_expression):
  """Creates an ExecuteRequest message for the Alpha track."""
  if filter_expression:
    return messages.OsconfigProjectsPatchJobsExecuteRequest(
        executePatchJobRequest=messages.ExecutePatchJobRequest(
            description=description,
            displayName=display_name,
            dryRun=dry_run,
            duration=duration,
            filter=filter_expression,
            patchConfig=patch_config,
            rollout=patch_rollout,
        ),
        parent=osconfig_command_utils.GetProjectUriPath(project))
  elif not any([
      filter_all, filter_group_labels, filter_zones, filter_names,
      filter_name_prefixes
  ]):
    return messages.OsconfigProjectsPatchJobsExecuteRequest(
        executePatchJobRequest=messages.ExecutePatchJobRequest(
            description=description,
            displayName=display_name,
            dryRun=dry_run,
            duration=duration,
            instanceFilter=messages.PatchInstanceFilter(all=True),
            patchConfig=patch_config,
            rollout=patch_rollout,
        ),
        parent=osconfig_command_utils.GetProjectUriPath(project))
  else:
    return _CreateExecuteRequest(messages, project, description, dry_run,
                                 duration, patch_config, patch_rollout,
                                 display_name, filter_all, filter_group_labels,
                                 filter_zones, filter_names,
                                 filter_name_prefixes)


def _CreateExecuteResponse(client, messages, request, is_async, command_prefix):
  """Creates an ExecutePatchJobResponse message."""
  async_response = client.projects_patchJobs.Execute(request)

  patch_job_name = osconfig_command_utils.GetResourceName(async_response.name)

  if is_async:
    log.status.Print(
        'Execution in progress for patch job [{}]'.format(patch_job_name))
    log.status.Print(
        'Run the [{} describe] command to check the status of this execution.'
        .format(command_prefix))
    return async_response

  # Execute the patch job synchronously.
  patch_job_poller = osconfig_api_utils.Poller(client, messages)
  get_request = messages.OsconfigProjectsPatchJobsGetRequest(
      name=async_response.name)
  sync_response = waiter.WaitFor(
      patch_job_poller,
      get_request,
      custom_tracker=_CreateProgressTracker(patch_job_name),
      tracker_update_func=_UpdateProgressTracker,
      pre_start_sleep_ms=5000,
      exponential_sleep_multiplier=1,  # Constant poll rate of 5s.
      sleep_ms=5000,
  )
  log.status.Print(
      'Execution for patch job [{}] has completed with status [{}].'.format(
          patch_job_name, sync_response.state))
  log.status.Print('Run the [{} list-instance-details] command to view any '
                   'instance failure reasons.'.format(command_prefix))
  return sync_response


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Execute(base.Command):
  """Execute an OS patch on the specified VM instances."""

  detailed_help = {
      'EXAMPLES':
          """\
      To start a patch job named `my patch job` that patches all instances in the
      current project, run:

            $ {command} --display-name="my patch job" --instance-filter-all

      To patch an instance named `instance-1` in the `us-east1-b` zone, run:

            $ {command} --instance-filter-names="zones/us-east1-b/instances/instance-1"

      To patch all instances in the `us-central1-b` and `europe-west1-d` zones, run:

            $ {command} --instance-filter-zones="us-central1-b,europe-west1-d"

      To patch all instances where the `env` label is `test` and `app` label is
      `web`, run:

            $ {command} --instance-filter-group-labels="env=test,app=web"

      To patch all instances where the `env` label is `test` and `app` label is
      `web` or where the `env` label is `staging` and `app` label is `web`, run:

            $ {command} --instance-filter-group-labels="env=test,app=web" --instance-filter-group-labels="env=staging,app=web"

      To apply security and critical patches to Windows instances with the prefix
      `windows-` in the instance name, run:

            $ {command} --instance-filter-name-prefixes="windows-" --windows-classifications=SECURITY,CRITICAL

      To update only `KB4339284` on Windows instances with the prefix `windows-` in
      the instance name, run:

            $ {command} --instance-filter-name-prefixes="windows-" --windows-exclusive-patches=4339284

      To patch all instances in the current project and specify scripts to run
      pre-patch and post-patch, run:

            $ {command} --instance-filter-all --pre-patch-linux-executable="/bin/script" --pre-patch-linux-success-codes=0,200 --pre-patch-windows-executable="C:\\Users\\user\\script.ps1" --post-patch-linux-executable="gs://my-bucket/linux-script#123" --post-patch-windows-executable="gs://my-bucket/windows-script#678"

      To patch all instances zone-by-zone with no more than 50 percent of the
      instances in the same zone disrupted at a given time, run:

            $ {command} --instance-filter-all --rollout-mode=zone-by-zone --rollout-disruption-budget-percent=50
      """
  }

  _command_prefix = 'gcloud compute os-config patch-jobs'

  @staticmethod
  def Args(parser):
    _AddTopLevelArguments(parser)
    _AddCommonTopLevelArguments(parser)
    _AddPatchConfigArguments(parser)
    _AddPatchRolloutArguments(parser)

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()

    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    duration = _GetDuration(args)
    patch_config = _CreatePatchConfig(args, messages)
    patch_rollout = _CreatePatchRollout(args, messages)

    request = _CreateExecuteRequest(
        messages,
        project,
        args.description,
        args.dry_run,
        duration,
        patch_config,
        patch_rollout,
        args.display_name,
        args.instance_filter_all,
        args.instance_filter_group_labels
        if args.instance_filter_group_labels else [],
        args.instance_filter_zones if args.instance_filter_zones else [],
        args.instance_filter_names if args.instance_filter_names else [],
        args.instance_filter_name_prefixes
        if args.instance_filter_name_prefixes else [],
    )
    return _CreateExecuteResponse(client, messages, request, args.async_,
                                  self._command_prefix)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ExecuteBeta(Execute):
  """Execute an OS patch on the specified VM instances."""

  _command_prefix = 'gcloud beta compute os-config patch-jobs'
