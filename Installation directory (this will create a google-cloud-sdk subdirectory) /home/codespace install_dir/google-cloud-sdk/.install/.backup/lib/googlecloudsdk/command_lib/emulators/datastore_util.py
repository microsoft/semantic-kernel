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

"""Utility functions for gcloud datastore emulator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import tempfile
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import platforms


class UnableToPrepareDataDir(exceptions.Error):

  def __init__(self):
    super(UnableToPrepareDataDir, self).__init__(
        'Unable to prepare the data directory for the emulator')


def ArgsForGCDEmulator(emulator_args):
  """Constructs an argument list for calling the GCD emulator.

  Args:
    emulator_args: args for the emulator.

  Returns:
    An argument list to execute the GCD emulator.
  """
  current_os = platforms.OperatingSystem.Current()
  if current_os is platforms.OperatingSystem.WINDOWS:
    cmd = 'cloud_datastore_emulator.cmd'
    gcd_executable = os.path.join(util.GetEmulatorRoot(CLOUD_DATASTORE), cmd)
    return execution_utils.ArgsForCMDTool(gcd_executable, *emulator_args)
  else:
    cmd = 'cloud_datastore_emulator'
    gcd_executable = os.path.join(util.GetEmulatorRoot(CLOUD_DATASTORE), cmd)
    return execution_utils.ArgsForExecutableTool(gcd_executable, *emulator_args)


DATASTORE = 'datastore'
CLOUD_DATASTORE = 'cloud-datastore'
DATASTORE_TITLE = 'Google Cloud Datastore emulator'


def PrepareGCDDataDir(args):
  """Prepares the given directory using gcd create.

  Raises:
    UnableToPrepareDataDir: If the gcd create execution fails.

  Args:
    args: The arguments passed to the command.
  """
  data_dir = args.data_dir
  if os.path.isdir(data_dir) and os.listdir(data_dir):
    log.warning('Reusing existing data in [{0}].'.format(data_dir))
    return

  gcd_create_args = ['create']
  project = properties.VALUES.core.project.Get(required=True)
  gcd_create_args.append('--project_id={0}'.format(project))
  gcd_create_args.append(data_dir)
  exec_args = ArgsForGCDEmulator(gcd_create_args)

  log.status.Print('Executing: {0}'.format(' '.join(exec_args)))
  with util.Exec(exec_args) as process:
    util.PrefixOutput(process, DATASTORE)
    failed = process.poll()
    if failed:
      raise UnableToPrepareDataDir()


def StartGCDEmulator(args, log_file=None):
  """Starts the datastore emulator with the given arguments.

  Args:
    args: Arguments passed to the start command.
    log_file: optional file argument to reroute process's output.

  Returns:
    process, The handle of the child process running the datastore emulator.
  """
  gcd_start_args = ['start']
  gcd_start_args.append('--host={0}'.format(args.host_port.host))
  gcd_start_args.append('--port={0}'.format(args.host_port.port))
  gcd_start_args.append('--store_on_disk={0}'.format(args.store_on_disk))
  gcd_start_args.append('--allow_remote_shutdown')
  if args.use_firestore_in_datastore_mode:
    gcd_start_args.append('--firestore_in_datastore_mode')
  else:
    gcd_start_args.append('--consistency={0}'.format(args.consistency))
  gcd_start_args.append(args.data_dir)
  exec_args = ArgsForGCDEmulator(gcd_start_args)

  log.status.Print('Executing: {0}'.format(' '.join(exec_args)))
  return util.Exec(exec_args, log_file=log_file)


def WriteGCDEnvYaml(args):
  """Writes the env.yaml file for the datastore emulator with provided args.

  Args:
    args: Arguments passed to the start command.
  """
  host_port = '{0}:{1}'.format(args.host_port.host, args.host_port.port)
  project_id = properties.VALUES.core.project.Get(required=True)
  env = {'DATASTORE_HOST': 'http://{0}'.format(host_port),
         'DATASTORE_EMULATOR_HOST': host_port,
         'DATASTORE_EMULATOR_HOST_PATH': '{0}/datastore'.format(host_port),
         'DATASTORE_DATASET': project_id,
         'DATASTORE_PROJECT_ID': project_id,
        }
  util.WriteEnvYaml(env, args.data_dir)


def GetDataDir():
  return util.GetDataDir(DATASTORE)


def GetHostPort():
  return util.GetHostPort(DATASTORE)


class DatastoreEmulator(util.Emulator):
  """Represents the ability to start and route datastore emulator."""

  def Start(self, port):
    args = util.AttrDict({
        'host_port': {
            'host': 'localhost',
            'port': port,
        },
        'store_on_disk': True,
        'consistency': 0.9,
        'data_dir': tempfile.mkdtemp(),
    })
    PrepareGCDDataDir(args)
    return StartGCDEmulator(args, self._GetLogNo())

  @property
  def prefixes(self):
    # Taken Jan 1, 2017 from:
    # https://cloud.google.com/datastore/docs/reference/rpc/google.datastore.v1
    # Note that this should probably be updated to just be based off of the
    # prefix, without enumerating all of the types.
    return [
        'google.datastore.v1.Datastore',
        'google.datastore.v1.AllocateIdsRequest',
        'google.datastore.v1.AllocateIdsResponse',
        'google.datastore.v1.ArrayValue',
        'google.datastore.v1.BeginTransactionRequest',
        'google.datastore.v1.BeginTransactionResponse',
        'google.datastore.v1.CommitRequest',
        'google.datastore.v1.CommitRequest.Mode',
        'google.datastore.v1.CommitResponse',
        'google.datastore.v1.CompositeFilter',
        'google.datastore.v1.CompositeFilter.Operator',
        'google.datastore.v1.Entity',
        'google.datastore.v1.EntityResult',
        'google.datastore.v1.EntityResult.ResultType',
        'google.datastore.v1.Filter',
        'google.datastore.v1.GqlQuery',
        'google.datastore.v1.GqlQueryParameter',
        'google.datastore.v1.Key',
        'google.datastore.v1.Key.PathElement',
        'google.datastore.v1.KindExpression',
        'google.datastore.v1.LookupRequest',
        'google.datastore.v1.LookupResponse',
        'google.datastore.v1.Mutation',
        'google.datastore.v1.MutationResult',
        'google.datastore.v1.PartitionId',
        'google.datastore.v1.Projection',
        'google.datastore.v1.PropertyFilter',
        'google.datastore.v1.PropertyFilter.Operator',
        'google.datastore.v1.PropertyOrder',
        'google.datastore.v1.PropertyOrder.Direction',
        'google.datastore.v1.PropertyReference',
        'google.datastore.v1.Query',
        'google.datastore.v1.QueryResultBatch',
        'google.datastore.v1.QueryResultBatch.MoreResultsType',
        'google.datastore.v1.ReadOptions',
        'google.datastore.v1.ReadOptions.ReadConsistency'
        'google.datastore.v1.RollbackRequest',
        'google.datastore.v1.RollbackResponse',
        'google.datastore.v1.RunQueryRequest',
        'google.datastore.v1.RunQueryResponse',
        'google.datastore.v1.Value',
    ]

  @property
  def service_name(self):
    return DATASTORE

  @property
  def emulator_title(self):
    return DATASTORE_TITLE

  @property
  def emulator_component(self):
    return 'cloud-datastore-emulator'
