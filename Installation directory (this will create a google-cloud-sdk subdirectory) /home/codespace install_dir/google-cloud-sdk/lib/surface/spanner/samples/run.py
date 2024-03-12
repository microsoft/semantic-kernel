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
"""Command for spanner samples run."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
import time

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.spanner import samples
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from surface.spanner.samples import backend as samples_backend
from surface.spanner.samples import init as samples_init
from surface.spanner.samples import workload as samples_workload


class Run(base.Command):
  """Run the given Cloud Spanner sample app.

  Each Cloud Spanner sample application includes a backend gRPC service
  backed by a Cloud Spanner database and a workload script that generates
  service traffic. This command creates and initializes the Cloud Spanner
  database and runs both the backend service and workload script.

  These sample apps are open source and available at
  https://github.com/GoogleCloudPlatform/cloud-spanner-samples.

  To see a list of available sample apps, run:

      $ {parent_command} list
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To run the 'finance' sample app using instance 'my-instance', run:

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
        help='ID of the new Cloud Spanner database to create for the sample '
        'app.')
    parser.add_argument(
        '--duration',
        default='1h',
        type=arg_parsers.Duration(),
        help=('Duration of time allowed to run the sample app before stopping '
              'the service.'))
    parser.add_argument(
        '--cleanup',
        action='store_true',
        default=True,
        help=('Delete the instance after running the sample app.'))
    parser.add_argument(
        '--skip-init',
        action='store_true',
        default=False,
        help=('Use an existing database instead of creating a new one.'))

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
    instance_id = args.instance_id
    project = properties.VALUES.core.project.GetOrFail()
    instance_ref = resources.REGISTRY.Parse(
        instance_id,
        params={
            'projectsId': project,
        },
        collection='spanner.projects.instances')
    if args.database_id is not None:
      database_id = args.database_id
    else:
      database_id = samples.get_db_id_for_app(appname)
    duration = args.duration
    skip_init = args.skip_init

    try:
      samples_init.check_instance(instance_id)
    except ValueError as ex:
      raise calliope_exceptions.BadArgumentException('--instance-id', ex)
    log.status.Print(
        "Initializing database '{database_id}' for sample app '{appname}'"
        .format(database_id=database_id, appname=appname))
    if skip_init:
      database_ref = resources.REGISTRY.Parse(
          database_id,
          params={
              'instancesId': instance_id,
              'projectsId': project
          },
          collection='spanner.projects.instances.databases')
      try:
        databases.Get(database_ref)
      # --skip-init assumes the database exists already, raise if it doesn't.
      except apitools_exceptions.HttpNotFoundError:
        bad_flag = ('--instance-id'
                    if args.database_id is None else '--database-id')
        raise calliope_exceptions.BadArgumentException(
            bad_flag, "Database '{database_id}' does not exist in instance "
            "'{instance_id}'. Re-run this command without `--skip-init` to "
            'create it.'.format(
                database_id=database_id, instance_id=instance_id))
    else:
      try:
        # Download any missing sample files and create the DB.
        if self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
          samples_init.download_sample_files(args.appname)
        samples_init.check_create_db(args.appname, instance_ref, database_id)
      except ValueError as ex:
        raise calliope_exceptions.BadArgumentException('--database-id', ex)

    be_proc = samples_backend.run_backend(project, appname, instance_id,
                                          database_id)
    try:
      be_proc.wait(2)
      return (
          'The {} sample app backend gRPC service failed to start, is another '
          'instance already running?'.format(appname))
    except execution_utils.TIMEOUT_EXPIRED_ERR:
      pass

    now = int(time.time())
    later = now + duration
    wl_proc = samples_workload.run_workload(appname, capture_logs=True)
    # Wait a second to let the workload print startup logs
    time.sleep(1)
    log.status.Print(
        '\nGenerating workload for database, start timestamp: {now}, end '
        'timestamp: {later}. Press ^C to stop.'.format(now=now, later=later))

    try:
      with execution_utils.RaisesKeyboardInterrupt():
        wl_proc.wait(duration)
    except KeyboardInterrupt:
      wl_proc.terminate()
      be_proc.terminate()
      log.status.Print('Backend gRPC service and workload generator killed')
    except execution_utils.TIMEOUT_EXPIRED_ERR:
      wl_proc.terminate()
      be_proc.terminate()
      log.status.Print(
          'Backend gRPC service and workload generator killed after {duration}s'
          .format(duration=duration))

    if args.cleanup:
      log.status.Print("Deleting database '{}'".format(database_id))
      database_ref = resources.REGISTRY.Parse(
          database_id,
          params={
              'projectsId': properties.VALUES.core.project.GetOrFail,
              'instancesId': instance_ref.instancesId
          },
          collection='spanner.projects.instances.databases')
      databases.Delete(database_ref)

    log.status.Print('Done')
    return
