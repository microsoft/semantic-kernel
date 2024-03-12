# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command to run an Airflow CLI sub-command in an environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import random
import re
import time

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import image_versions_util as image_versions_command_util
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

WORKER_POD_SUBSTR = 'airflow-worker'
WORKER_CONTAINER = 'airflow-worker'
DEPRECATION_WARNING = ('Because Cloud Composer manages the Airflow metadata '
                       'database for your environment, support for the Airflow '
                       '`{}` subcommand is being deprecated. '
                       'To avoid issues related to Airflow metadata, we '
                       'recommend that you do not use this subcommand unless '
                       'you understand the outcome.')
DEFAULT_POLL_TIME_SECONDS = 2
MAX_CONSECUTIVE_POLL_ERRORS = 10
MAX_POLL_TIME_SECONDS = 30
EXP_BACKOFF_MULTIPLIER = 1.75
POLL_JITTER_SECONDS = 0.5


class Run(base.Command):
  """Run an Airflow sub-command remotely in a Cloud Composer environment.

  Executes an Airflow CLI sub-command remotely in an environment. If the
  sub-command takes flags, separate the environment name from the sub-command
  and its flags with ``--''. This command waits for the sub-command to
  complete; its exit code will match the sub-command's exit code.

  Note: Airflow CLI sub-command syntax differs between Airflow 1 and Airflow 2.
  Refer to the Airflow CLI reference documentation for more details.

  ## EXAMPLES

    The following command in environments with Airflow 2:

    {command} myenv dags trigger -- some_dag --run_id=foo

  is equivalent to running the following command from a shell inside the
  *my-environment* environment:

    airflow dags trigger --run_id=foo some_dag

  The same command, but for environments with Airflow 1.10.14+:

    {command} myenv trigger_dag -- some_dag --run_id=foo

  is equivalent to running the following command from a shell inside the
  *my-environment* environment:

    airflow trigger_dag some_dag --run_id=foo

  The following command (for environments with Airflow 1.10.14+):

    {command} myenv dags list

  is equivalent to running the following command from a shell inside the
  *my-environment* environment:

    airflow dags list
  """

  SUBCOMMAND_ALLOWLIST = command_util.SUBCOMMAND_ALLOWLIST

  @classmethod
  def Args(cls, parser):
    resource_args.AddEnvironmentResourceArg(
        parser, 'in which to run an Airflow command')

    doc_url = 'https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html'
    parser.add_argument(
        'subcommand',
        metavar='SUBCOMMAND',
        choices=list(cls.SUBCOMMAND_ALLOWLIST.keys()),
        help=('The Airflow CLI subcommand to run. Available subcommands '
              'include (listed with Airflow versions that support): {} '
              '(see {} for more info).').format(
                  ', '.join(
                      sorted([
                          '{} [{}, {})'.format(cmd, r.from_version or '**',
                                               r.to_version or '**')
                          for cmd, r in cls.SUBCOMMAND_ALLOWLIST.items()
                      ])), doc_url))
    # Add information about restricted nested subcommands.
    # Some subcommands only allow certain nested subcommands.
    # Written with for loops to reduce complexity. [g-complex-comprehension]
    allowed_nested_subcommands_help = []
    for sub_cmd, r in cls.SUBCOMMAND_ALLOWLIST.items():
      # Skip sub-commands which don't have a list of allowed_nested_subcommands
      # Meaning, all nested subcommands are allowed for this subcommand
      if not r.allowed_nested_subcommands:
        continue
      allowed_nested_subcommands_help.append(
          '- {}: {}'.format(
              sub_cmd,
              ', '.join(sorted(r.allowed_nested_subcommands.keys()))
          ))
    # Add an additional element stating that all other subcommands are allowed
    allowed_nested_subcommands_help.append(
        '- all other subcommands: all nested subcommands are allowed'
    )
    parser.add_argument(
        'subcommand_nested',
        metavar='SUBCOMMAND_NESTED',
        nargs=argparse.OPTIONAL,
        help=(
            'Additional subcommand in case it is nested. '
            'The following is a list of allowed nested subcommands:\n'
            '{}'
        ).format('\n'.join(allowed_nested_subcommands_help)),
    )
    parser.add_argument(
        'cmd_args',
        metavar='CMD_ARGS',
        nargs=argparse.REMAINDER,
        help='Command line arguments to the subcommand.',
        example='{command} myenv trigger_dag -- some_dag --run_id=foo')

  def BypassConfirmationPrompt(self, args, airflow_version):
    """Bypasses confirmations with "yes" responses.

    Prevents certain Airflow CLI subcommands from presenting a confirmation
    prompting (which can make the gcloud CLI stop responding). When necessary,
    bypass confirmations with a "yes" response.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
      airflow_version: String, an Airflow semantic version.
    """
    # Value is the lowest Airflow version for which this command needs to bypass
    # the confirmation prompt.
    prompting_subcommands = {
        'backfill': '1.10.6',
        'delete_dag': None,
        ('dags', 'backfill'): None,
        ('dags', 'delete'): None,
        ('tasks', 'clear'): None,
        ('db', 'clean'): None,
    }

    # Handle nested commands like "dags list". There are two ways to execute
    # nested Airflow subcommands via gcloud:
    # 1. {command} myenv dags delete -- dag_id
    # 2. {command} myenv dags -- delete dag_id
    subcommand_two_level = self._GetSubcommandTwoLevel(args)

    def _IsPromptingSubcommand(s):
      if s in prompting_subcommands:
        pass
      elif s[0] in prompting_subcommands:
        s = s[0]
      else:
        return False

      return (prompting_subcommands[s] is None or
              image_versions_command_util.CompareVersions(
                  airflow_version, prompting_subcommands[s]) >= 0)

    if (_IsPromptingSubcommand(subcommand_two_level) and
        set(args.cmd_args or []).isdisjoint({'-y', '--yes'})):
      args.cmd_args = args.cmd_args or []
      args.cmd_args.append('--yes')

  def CheckForRequiredCmdArgs(self, args):
    """Prevents running Airflow CLI commands without required arguments.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
    """
    # Dict values are lists of tuples, each tuple represents set of arguments,
    # where at least one argument from tuple will be required.
    # E.g. for "users create" subcommand, one of the "-p", "--password" or
    # "--use-random-password" will be required.
    required_cmd_args = {
        ('users', 'create'): [['-p', '--password', '--use-random-password']],
    }

    def _StringifyRequiredCmdArgs(cmd_args):
      quoted_args = ['"{}"'.format(a) for a in cmd_args]
      return '[{}]'.format(', '.join(quoted_args))

    subcommand_two_level = self._GetSubcommandTwoLevel(args)

    # For now `required_cmd_args` contains only two-level Airflow commands,
    # but potentially in the future it could be extended for one-level
    # commands as well, and this code will have to be updated appropriately.
    for subcommand_required_cmd_args in required_cmd_args.get(
        subcommand_two_level, []):
      if set(subcommand_required_cmd_args).isdisjoint(set(args.cmd_args or [])):
        raise command_util.Error(
            'The subcommand "{}" requires one of the following command line '
            'arguments: {}.'.format(
                ' '.join(subcommand_two_level),
                _StringifyRequiredCmdArgs(subcommand_required_cmd_args)))

  def DeprecationWarningPrompt(self, args):
    response = True
    if args.subcommand in command_util.SUBCOMMAND_DEPRECATION:
      response = console_io.PromptContinue(
          message=DEPRECATION_WARNING.format(args.subcommand),
          default=False,
          cancel_on_no=True)
    return response

  def _GetSubcommandTwoLevel(self, args):
    """Extract and return two level nested Airflow subcommand in unified shape.

    There are two ways to execute nested Airflow subcommands via gcloud, e.g.:
    1. {command} myenv users create -- -u User
    2. {command} myenv users -- create -u User
    The method returns here (users, create) in both cases.

    It is possible that first element of args.cmd_args will not be a nested
    subcommand, but that is ok as it will not break entire logic.
    So, essentially there can be subcommand_two_level = ['info', '--anonymize'].

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      subcommand_two_level: two level subcommand in unified format
    """

    subcommand_two_level = (args.subcommand, None)

    if args.subcommand_nested:
      subcommand_two_level = (args.subcommand, args.subcommand_nested)
    elif args.cmd_args:
      subcommand_two_level = (args.subcommand, args.cmd_args[0])

    return subcommand_two_level

  def CheckSubcommandAirflowSupport(self, args, airflow_version):

    def _CheckIsSupportedSubcommand(command, airflow_version, from_version,
                                    to_version):
      if not image_versions_command_util.IsVersionInRange(
          airflow_version, from_version, to_version):
        _RaiseLackOfSupportError(command, airflow_version)

    def _RaiseLackOfSupportError(command, airflow_version):
      raise command_util.Error(
          'The subcommand "{}" is not supported for Composer environments'
          ' with Airflow version {}.'.format(command, airflow_version),)

    subcommand, subcommand_nested = self._GetSubcommandTwoLevel(args)
    _CheckIsSupportedSubcommand(
        subcommand, airflow_version,
        self.SUBCOMMAND_ALLOWLIST[args.subcommand].from_version,
        self.SUBCOMMAND_ALLOWLIST[args.subcommand].to_version)

    if not self.SUBCOMMAND_ALLOWLIST[
        args.subcommand].allowed_nested_subcommands:
      return

    two_level_subcommand_string = '{} {}'.format(subcommand, subcommand_nested)

    if subcommand_nested in self.SUBCOMMAND_ALLOWLIST[
        args.subcommand].allowed_nested_subcommands:
      _CheckIsSupportedSubcommand(
          two_level_subcommand_string, airflow_version,
          self.SUBCOMMAND_ALLOWLIST[args.subcommand]
          .allowed_nested_subcommands[subcommand_nested].from_version,
          self.SUBCOMMAND_ALLOWLIST[args.subcommand]
          .allowed_nested_subcommands[subcommand_nested].to_version)
    else:
      _RaiseLackOfSupportError(two_level_subcommand_string, airflow_version)

  def CheckSubcommandNestedAirflowSupport(self, args, airflow_version):
    if (args.subcommand_nested and
        not image_versions_command_util.IsVersionInRange(
            airflow_version, '1.10.14', None)):
      raise command_util.Error(
          'Nested subcommands are supported only for Composer environments '
          'with Airflow version 1.10.14 or higher.')

  def ConvertKubectlError(self, error, env_obj):
    is_private = (
        env_obj.config.privateEnvironmentConfig and
        env_obj.config.privateEnvironmentConfig.enablePrivateEnvironment)
    if is_private:
      return command_util.Error(
          str(error)
          + ' Make sure you have followed'
          ' https://cloud.google.com/composer/docs/how-to/accessing/airflow-cli#private-ip'
          ' to enable access to your private Cloud Composer environment from'
          ' your machine.'
      )
    return error

  def _ExtractAirflowVersion(self, image_version):
    return re.findall(r'-airflow-([\d\.]+)', image_version)[0]

  def _RunKubectl(self, args, env_obj):
    """Runs Airflow command using kubectl on the GKE Cluster.

    This mode the command is executed by connecting to the cluster and
    running `kubectl pod exec` command.
    It requires access to GKE Control plane.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
      env_obj: Cloud Composer Environment object.
    """
    cluster_id = env_obj.config.gkeCluster
    cluster_location_id = command_util.ExtractGkeClusterLocationId(env_obj)

    tty = 'no-tty' not in args

    with command_util.TemporaryKubeconfig(cluster_location_id, cluster_id):
      try:
        image_version = env_obj.config.softwareConfig.imageVersion
        airflow_version = self._ExtractAirflowVersion(image_version)

        self.CheckSubcommandAirflowSupport(args, airflow_version)
        self.CheckSubcommandNestedAirflowSupport(args, airflow_version)

        kubectl_ns = command_util.FetchKubectlNamespace(image_version)
        pod = command_util.GetGkePod(
            pod_substr=WORKER_POD_SUBSTR, kubectl_namespace=kubectl_ns)

        log.status.Print(
            'Executing within the following Kubernetes cluster namespace: '
            '{}'.format(kubectl_ns))
        self.BypassConfirmationPrompt(args, airflow_version)
        kubectl_args = ['exec', pod, '--stdin']
        if tty:
          kubectl_args.append('--tty')
        kubectl_args.extend(
            ['--container', WORKER_CONTAINER, '--', 'airflow', args.subcommand])
        if args.subcommand_nested:
          kubectl_args.append(args.subcommand_nested)
        if args.cmd_args:
          kubectl_args.extend(args.cmd_args)

        command_util.RunKubectlCommand(
            command_util.AddKubectlNamespace(kubectl_ns, kubectl_args),
            out_func=log.out.Print)
      except command_util.KubectlError as e:
        raise self.ConvertKubectlError(e, env_obj)

  def _RunApi(self, args, env_obj):
    image_version = env_obj.config.softwareConfig.imageVersion
    airflow_version = self._ExtractAirflowVersion(image_version)
    env_ref = args.CONCEPTS.environment.Parse()

    self.CheckSubcommandAirflowSupport(args, airflow_version)
    self.CheckSubcommandNestedAirflowSupport(args, airflow_version)
    self.BypassConfirmationPrompt(args, airflow_version)

    cmd = [args.subcommand]
    if args.subcommand_nested:
      cmd.append(args.subcommand_nested)
    if args.cmd_args:
      cmd.extend(args.cmd_args)
    log.status.Print(
        'Executing the command: [ airflow {} ]...'.format(' '.join(cmd))
    )
    execute_result = environments_api_util.ExecuteAirflowCommand(
        command=args.subcommand,
        subcommand=args.subcommand_nested or '',
        parameters=args.cmd_args or [],
        environment_ref=env_ref,
        release_track=self.ReleaseTrack(),
    )
    if execute_result and execute_result.executionId:
      log.status.Print(
          'Command has been started. execution_id={}'.format(
              execute_result.executionId
          )
      )

    if not execute_result.executionId:
      raise command_util.Error(
          'Cannot execute subcommand for environment. Got empty execution Id.'
      )
    log.status.Print('Use ctrl-c to interrupt the command')
    output_end = False
    next_line = 1
    cur_consequetive_poll_errors = 0
    wait_time_seconds = DEFAULT_POLL_TIME_SECONDS
    poll_result = None
    interrupted = False
    force_stop = False
    while not output_end and not force_stop:
      lines = None
      try:
        with execution_utils.RaisesKeyboardInterrupt():
          time.sleep(
              wait_time_seconds
              + random.uniform(-POLL_JITTER_SECONDS, POLL_JITTER_SECONDS)
          )
          poll_result = environments_api_util.PollAirflowCommand(
              execution_id=execute_result.executionId,
              pod_name=execute_result.pod,
              pod_namespace=execute_result.podNamespace,
              next_line_number=next_line,
              environment_ref=env_ref,
              release_track=self.ReleaseTrack(),
          )
          cur_consequetive_poll_errors = 0
          output_end = poll_result.outputEnd
          lines = poll_result.output
          lines.sort(key=lambda line: line.lineNumber)
      except KeyboardInterrupt:
        log.status.Print('Interrupting the command...')
        try:
          log.debug('Stopping the airflow command...')
          stop_result = environments_api_util.StopAirflowCommand(
              execution_id=execute_result.executionId,
              pod_name=execute_result.pod,
              force=interrupted,
              pod_namespace=execute_result.podNamespace,
              environment_ref=env_ref,
              release_track=self.ReleaseTrack(),
          )
          log.debug('Stop airflow command result...'+str(stop_result))
          if stop_result and stop_result.output:
            for line in stop_result.output:
              log.Print(line)
          if interrupted:
            force_stop = True
          interrupted = True
        except:  # pylint:disable=bare-except
          log.debug('Error during stopping airflow command. Retrying polling')
          cur_consequetive_poll_errors += 1
      except:  # pylint:disable=bare-except
        cur_consequetive_poll_errors += 1

      if cur_consequetive_poll_errors == MAX_CONSECUTIVE_POLL_ERRORS:
        raise command_util.Error('Cannot fetch airflow command status.')

      if not lines:
        wait_time_seconds = min(
            wait_time_seconds * EXP_BACKOFF_MULTIPLIER, MAX_POLL_TIME_SECONDS
        )
      else:
        wait_time_seconds = DEFAULT_POLL_TIME_SECONDS
        for line in lines:
          log.Print(line.content if line.content else '')
        next_line = lines[-1].lineNumber + 1

    if poll_result and poll_result.exitInfo and poll_result.exitInfo.exitCode:
      if poll_result.exitInfo.error:
        log.error('Error message: {}'.format(poll_result.exitInfo.error))
      log.error('Command exit code: {}'.format(poll_result.exitInfo.exitCode))
      exit(poll_result.exitInfo.exitCode)

  def Run(self, args):
    self.DeprecationWarningPrompt(args)
    self.CheckForRequiredCmdArgs(args)

    running_state = api_util.GetMessagesModule(
        release_track=self.ReleaseTrack()
    ).Environment.StateValueValuesEnum.RUNNING

    env_ref = args.CONCEPTS.environment.Parse()
    env_obj = environments_api_util.Get(
        env_ref, release_track=self.ReleaseTrack()
    )

    if env_obj.state != running_state:
      raise command_util.Error(
          'Cannot execute subcommand for environment in state {}. '
          'Must be RUNNING.'.format(env_obj.state)
      )
    if image_versions_command_util.IsVersionAirflowCommandsApiCompatible(
        image_version=env_obj.config.softwareConfig.imageVersion
    ):
      self._RunApi(args, env_obj)
    else:
      self._RunKubectl(args, env_obj)
