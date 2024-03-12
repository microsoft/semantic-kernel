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
"""Command that loads environment snapshots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.composer import operations_util as operations_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import flags
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import log

import six

DETAILED_HELP = {
    'EXAMPLES':
        """\
          To load a snapshot into the environment named env-1, run:

          $ {command} env-1 \
          --snapshot-path=gs://my-bucket/path-to-the-specific-snapshot
        """
}


class LoadSnapshot(base.Command):
  """Load a snapshot into the environment."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(parser, 'where to load a snapshot')
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        '--snapshot-path',
        type=str,
        help='The Cloud Storage path to load the snapshot from. It must '
        'start with prefix gs:// and one needs to specify a single snapshot '
        'that should be loaded.',
        required=True)
    flags.SKIP_PYPI_PACKAGES_INSTALLATION.AddToParser(parser)
    flags.SKIP_ENVIRONMENT_VARIABLES_SETTING.AddToParser(parser)
    flags.SKIP_AIRFLOW_OVERRIDES_SETTING.AddToParser(parser)
    flags.SKIP_COPYING_GCS_DATA.AddToParser(parser)

  def Run(self, args):
    env_resource = args.CONCEPTS.environment.Parse()
    operation = environments_api_util.LoadSnapshot(
        env_resource,
        args.skip_pypi_packages_installation,
        args.skip_environment_variables_setting,
        args.skip_airflow_overrides_setting,
        args.skip_gcs_data_copying,
        args.snapshot_path,
        release_track=self.ReleaseTrack())
    if args.async_:
      return self._AsynchronousExecution(env_resource, operation)
    else:
      return self._SynchronousExecution(env_resource, operation)

  def _AsynchronousExecution(self, env_resource, operation):
    details = 'with operation [{0}]'.format(operation.name)
    log.UpdatedResource(
        env_resource.RelativeName(),
        kind='environment',
        is_async=True,
        details=details)
    return operation

  def _SynchronousExecution(self, env_resource, operation):
    try:
      operations_api_util.WaitForOperation(
          operation,
          'Waiting for [{}] to be updated with [{}]'.format(
              env_resource.RelativeName(), operation.name),
          release_track=self.ReleaseTrack())
    except command_util.Error as e:
      raise command_util.Error(
          'Failed to load the snapshot of the environment [{}]: {}'.format(
              env_resource.RelativeName(), six.text_type(e)))
