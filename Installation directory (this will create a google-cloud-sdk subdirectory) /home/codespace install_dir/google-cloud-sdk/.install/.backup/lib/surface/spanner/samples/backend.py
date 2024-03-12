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
"""Command for spanner samples backend."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.spanner import samples
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from surface.spanner.samples import init as samples_init


def _get_logfile_name(appname):
  return '{}-backend.log'.format(appname)


def _get_popen_jar(appname):
  if appname not in samples.APPS:
    raise ValueError("Unknown sample app '{}'".format(appname))
  return os.path.join(
      samples.get_local_bin_path(appname), samples.APPS[appname].backend_bin)


# Note: Currently all apps supported use the same flag definitions.
# If there is a need for different flags by app in the future this logic can
# move to: third_party/py/googlecloudsdk/command_lib/spanner/samples.py
def _get_popen_args(project, appname, instance_id, database_id=None, port=None):
  """Get formatted args for server command."""
  if database_id is None:
    database_id = samples.get_db_id_for_app(appname)
  flags = [
      '--spanner_project_id={}'.format(project),
      '--spanner_instance_id={}'.format(instance_id),
      '--spanner_database_id={}'.format(database_id)
  ]
  if port is not None:
    flags.append('--port={}'.format(port))
  if samples.get_database_dialect(
      appname) == databases.DATABASE_DIALECT_POSTGRESQL:
    flags.append('--spanner_use_pg')
  return flags


def run_backend(project,
                appname,
                instance_id,
                database_id=None,
                port=None,
                capture_logs=False):
  """Run the backend service executable for the given sample app.

  Args:
    project: str, Name of the GCP project.
    appname: str, Name of the sample app.
    instance_id: str, Cloud Spanner instance ID.
    database_id: str, Cloud Spanner database ID.
    port: int, Port to run the service on.
    capture_logs: bool, Whether to save logs to disk or print to stdout.

  Returns:
    subprocess.Popen or execution_utils.SubprocessTimeoutWrapper, The running
      subprocess.
  """
  proc_args = ['java', '-jar']
  proc_args.append(_get_popen_jar(appname))
  proc_args.extend(
      _get_popen_args(project, appname, instance_id, database_id, port))
  capture_logs_fn = (
      os.path.join(samples.SAMPLES_LOG_PATH, '{}-backend.log'.format(appname))
      if capture_logs else None)
  return samples.run_proc(proc_args, capture_logs_fn)


class Backend(base.Command):
  """Run the backend gRPC service for the given Cloud Spanner sample app.

  This command starts the backend gRPC service for the given sample
  application. Before starting the service, create the database and load any
  initial data with:

      $ {parent_command} init APPNAME --instance-id=INSTANCE_ID

  After starting the service, generate traffic with:

      $ {parent_command} workload APPNAME

  To run all three steps together, use:

      $ {parent_command} run APPNAME --instance-id=INSTANCE_ID
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To run the backend gRPC service for the 'finance' sample app using
          instance 'my-instance', run:

          $ {command} finance --instance-id=my-instance
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
        '--instance-id',
        required=True,
        type=str,
        help='The Cloud Spanner instance ID for the sample app.')
    parser.add_argument(
        '--database-id',
        type=str,
        help='The Cloud Spanner database ID for the sample app.')
    parser.add_argument(
        '--duration',
        default='1h',
        type=arg_parsers.Duration(),
        help=('Duration of time allowed to run before stopping the service.'))
    parser.add_argument(
        '--port', type=int, help=('Port on which to receive gRPC requests.'))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    appname = args.appname
    try:
      samples.check_appname(appname)
    except ValueError as ex:
      raise calliope_exceptions.BadArgumentException('APPNAME', ex)

    project = properties.VALUES.core.project.GetOrFail()

    instance_id = args.instance_id
    try:
      samples_init.check_instance(instance_id)
    except ValueError as ex:
      raise calliope_exceptions.BadArgumentException('--instance-id', ex)

    if args.database_id is not None:
      database_id = args.database_id
    else:
      database_id = samples.get_db_id_for_app(appname)
    database_ref = resources.REGISTRY.Parse(
        database_id,
        params={
            'projectsId': project,
            'instancesId': instance_id
        },
        collection='spanner.projects.instances.databases')
    try:
      databases.Get(database_ref)
    except apitools_exceptions.HttpNotFoundError as ex:
      if args.database_id is not None:
        raise calliope_exceptions.BadArgumentException('--database-id', ex)
      else:
        raise samples.SpannerSamplesError(
            "Database {} doesn't exist. Did you run `gcloud spanner samples "
            'init` first?'.format(database_id))

    proc = run_backend(project, appname, instance_id, args.database_id,
                       args.port)
    try:
      with execution_utils.RaisesKeyboardInterrupt():
        proc.wait(args.duration)
    except KeyboardInterrupt:
      proc.terminate()
      return 'Backend gRPC service killed'
    except execution_utils.TIMEOUT_EXPIRED_ERR:
      proc.terminate()
      return 'Backend gRPC service timed out after {duration}s'.format(
          duration=args.duration)
    return
