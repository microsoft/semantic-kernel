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
"""Command that saves environment snapshots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.composer import operations_util as operations_api_util
from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import log
import six

DETAILED_HELP = {
    'EXAMPLES':
        textwrap.dedent("""\
          To save a snapshot of the environment named env-1, run:

            $ {command} env-1
        """)
}


class SaveSnapshot(base.Command):
  """Save a snapshot of the environment."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(parser,
                                            'where the snapshot must be saved')
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        '--snapshot-location',
        type=str,
        help='The Cloud Storage location where to save the snapshot. It must '
        'start with the prefix gs://. Default value is /snapshots directory in '
        'the Cloud Storage bucket of the environment.')

  def Run(self, args):
    env_resource = args.CONCEPTS.environment.Parse()
    operation = environments_api_util.SaveSnapshot(
        env_resource, args.snapshot_location, release_track=self.ReleaseTrack())
    if args.async_:
      return self._AsynchronousExecution(env_resource, operation)
    else:
      return self._SynchronousExecution(env_resource, operation)

  def _AsynchronousExecution(self, env_resource, operation):
    log.UpdatedResource(
        env_resource.RelativeName(),
        kind='environment',
        is_async=True,
        details='with operation [{}]'.format(operation.name))

    log.status.Print('If you want to see the result, run:')
    log.status.Print('gcloud composer operations describe ' + operation.name)

    return operation

  def _SynchronousExecution(self, env_resource, operation):
    try:
      operations_api_util.WaitForOperation(
          operation,
          'Waiting for [{}] to be updated with [{}]'.format(
              env_resource.RelativeName(), operation.name),
          release_track=self.ReleaseTrack())

      completed_operation = operations_api_util.GetService(
          self.ReleaseTrack()).Get(
              api_util.GetMessagesModule(self.ReleaseTrack())
              .ComposerProjectsLocationsOperationsGetRequest(
                  name=operation.name))

      log.status.Print('\nIf you want to see the result once more, run:')
      log.status.Print('gcloud composer operations describe ' + operation.name +
                       '\n')

      log.status.Print(
          'If you want to see history of all operations to be able'
          ' to display results of previous check-upgrade runs, run:')
      log.status.Print('gcloud composer operations list\n')

      log.status.Print('Response: ')

      return completed_operation.response
    except command_util.Error as e:
      raise command_util.Error(
          'Failed to save the snapshot of the environment [{}]: {}'.format(
              env_resource.RelativeName(), six.text_type(e)))
