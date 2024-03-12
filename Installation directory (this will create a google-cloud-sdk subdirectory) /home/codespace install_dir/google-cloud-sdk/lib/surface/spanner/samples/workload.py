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
"""Command for spanner samples workload."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import samples
from googlecloudsdk.core import execution_utils


def _get_popen_jar(appname):
  if appname not in samples.APPS:
    raise ValueError("Unknown sample app '{}'".format(appname))
  return os.path.join(
      samples.get_local_bin_path(appname), samples.APPS[appname].workload_bin)


def run_workload(appname, port=None, capture_logs=False):
  """Run the workload generator executable for the given sample app.

  Args:
    appname: str, Name of the sample app.
    port: int, Port to run the service on.
    capture_logs: bool, Whether to save logs to disk or print to stdout.

  Returns:
    subprocess.Popen or execution_utils.SubprocessTimeoutWrapper, The running
      subprocess.
  """
  proc_args = ['java', '-jar', _get_popen_jar(appname)]
  if port is not None:
    proc_args.append('--port={}'.format(port))
  capture_logs_fn = (
      os.path.join(samples.SAMPLES_LOG_PATH, '{}-workload.log'.format(appname))
      if capture_logs else None)
  return samples.run_proc(proc_args, capture_logs_fn)


class Workload(base.Command):
  """Generate gRPC traffic for a given sample app's backend service.

  Before sending traffic to the backend service, create the database and
  start the service with:

      $ {parent_command} init APPNAME --instance-id=INSTANCE_ID
      $ {parent_command} backend APPNAME --instance-id=INSTANCE_ID

  To run all three steps together, use:

      $ {parent_command} run APPNAME --instance-id=INSTANCE_ID
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To generate traffic for the 'finance' sample app, run:

          $ {command} finance
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument('appname', help='The sample app name, e.g. "finance".')

    parser.add_argument(
        '--duration',
        default='1h',
        type=arg_parsers.Duration(),
        help=('Duration of time allowed to run before stopping the workload.'))
    parser.add_argument(
        '--port', type=int, help=('Port of the running backend service.'))
    parser.add_argument(
        '--target-qps', type=int, help=('Target requests per second.'))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    proc = run_workload(args.appname, args.port)
    try:
      with execution_utils.RaisesKeyboardInterrupt():
        return proc.wait(args.duration)
    except KeyboardInterrupt:
      proc.terminate()
      return 'Workload generator killed'
    except execution_utils.TIMEOUT_EXPIRED_ERR:
      proc.terminate()
      return 'Workload generator killed after {duration}s'.format(
          duration=args.duration)
    return
