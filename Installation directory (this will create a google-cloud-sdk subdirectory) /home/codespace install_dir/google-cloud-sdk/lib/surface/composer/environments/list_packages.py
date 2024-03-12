# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to list all PyPI modules installed in an Airflow worker."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import random
import time

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import image_versions_util as image_versions_command_util
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import log

import six

DETAILED_HELP = {
    'EXAMPLES':
        """\
          The following command:

          $ {command} myenv

          runs the "python -m pip list" command on a worker and returns the output.

          The following command:

          $ {command} myenv --tree

          runs the "python -m pipdeptree --warn" command on a worker and returns the
          output.
      """
}

WORKER_POD_SUBSTR = 'worker'
WORKER_CONTAINER = 'airflow-worker'

DEFAULT_POLL_TIME_SECONDS = 2
MAX_CONSECUTIVE_POLL_ERRORS = 10
MAX_POLL_TIME_SECONDS = 30
EXP_BACKOFF_MULTIPLIER = 1.75
POLL_JITTER_SECONDS = 0.5


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Run(base.Command):
  """List all PyPI modules installed in an Airflow worker."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    resource_args.AddEnvironmentResourceArg(parser,
                                            'in which to list PyPI modules')

    parser.add_argument(
        '--tree',
        default=None,
        action='store_true',
        help="""\
        List PyPI packages, their versions and a dependency tree, as displayed by the "python -m pipdeptree --warn" command.
        """)

  def ConvertKubectlError(self, error, env_obj):
    del env_obj  # Unused argument.
    return error

  def _RunKubectl(self, args, env_obj):
    cluster_id = env_obj.config.gkeCluster
    cluster_location_id = command_util.ExtractGkeClusterLocationId(env_obj)

    tty = 'no-tty' not in args

    with command_util.TemporaryKubeconfig(cluster_location_id, cluster_id):
      try:
        image_version = env_obj.config.softwareConfig.imageVersion

        kubectl_ns = command_util.FetchKubectlNamespace(image_version)
        pod = command_util.GetGkePod(
            pod_substr=WORKER_POD_SUBSTR, kubectl_namespace=kubectl_ns)

        log.status.Print(
            'Executing within the following Kubernetes cluster namespace: '
            '{}'.format(kubectl_ns))

        kubectl_args = ['exec', pod, '--stdin']
        if tty:
          kubectl_args.append('--tty')
        kubectl_args.extend(['--container', WORKER_CONTAINER, '--'])
        if args.tree:
          kubectl_args.extend(['python', '-m', 'pipdeptree', '--warn'])
        else:
          kubectl_args.extend(['python', '-m', 'pip', 'list'])

        command_util.RunKubectlCommand(
            command_util.AddKubectlNamespace(kubectl_ns, kubectl_args),
            out_func=log.out.Print)
      except command_util.KubectlError as e:
        raise self.ConvertKubectlError(e, env_obj)

  def _RunApi(self, args, env_ref):

    cmd_params = []
    if args.tree:
      subcommand = 'pipdeptree'
      cmd_params.append('--warn')
    else:
      subcommand = 'pip list'
    execute_result = environments_api_util.ExecuteAirflowCommand(
        command='list-packages',
        subcommand=subcommand,
        parameters=[],
        environment_ref=env_ref,
        release_track=self.ReleaseTrack(),
    )

    if not execute_result.executionId:
      raise command_util.Error(
          'Cannot execute subcommand for environment. Got empty execution Id.'
      )

    output_end = False
    next_line = 1
    wait_time_seconds = DEFAULT_POLL_TIME_SECONDS
    poll_result = None
    cur_consequetive_poll_errors = 0
    while not output_end:
      lines = None
      try:
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
      except:  # pylint:disable=bare-except
        cur_consequetive_poll_errors += 1

      if cur_consequetive_poll_errors == MAX_CONSECUTIVE_POLL_ERRORS:
        raise command_util.Error('Cannot fetch list-packages command status.')

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
      log.error('Command exit code: {}'.format(poll_result.exitInfo.error))
      exit(poll_result.exitInfo.exitCode)

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()
    env_obj = environments_api_util.Get(
        env_ref, release_track=self.ReleaseTrack())
    if image_versions_command_util.IsVersionAirflowCommandsApiCompatible(
        image_version=env_obj.config.softwareConfig.imageVersion
    ):
      self._RunApi(args, env_ref)
    else:
      self._RunKubectl(args, env_obj)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class RunBeta(Run):
  """List all PyPI modules installed in an Airflow worker.

  ## EXAMPLES

    The following command:

    {command} myenv

    runs the "python -m pip list" command on a worker and returns the output.

    The following command:

    {command} myenv --tree

    runs the "python -m pipdeptree --warn" command on a worker and returns the
    output.
  """

  def ConvertKubectlError(self, error, env_obj):
    is_private = (
        env_obj.config.privateEnvironmentConfig and
        env_obj.config.privateEnvironmentConfig.enablePrivateEnvironment)
    if is_private:
      return command_util.Error(
          six.text_type(error) +
          ' Make sure you have followed https://cloud.google.com/composer/docs/how-to/accessing/airflow-cli#running_commands_on_a_private_ip_environment '
          'to enable access to your private Cloud Composer environment from '
          'your machine.')
    return error
