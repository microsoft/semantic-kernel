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
"""Command which checks that upgrading a Cloud Composer environment does not result in PyPI module conflicts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.composer import operations_util as operations_api_util
from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import flags
from googlecloudsdk.command_lib.composer import image_versions_util as image_versions_command_util
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import log
import six

DETAILED_HELP = {
    'EXAMPLES':
        """\
        To check that upgrading to the 'composer-1.16.5-airflow-1.10.15' image
          in a Cloud Composer environment named 'env-1' does not cause
          PyPI package conflicts,
          run:

          $ {command} env-1 --image-version=composer-1.16.5-airflow-1.10.15
      """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CheckUpgrade(base.Command):
  """Check that upgrading a Cloud Composer environment does not result in PyPI module conflicts."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(parser, 'to check upgrade for')
    base.ASYNC_FLAG.AddToParser(parser)

    flags.AddEnvUpgradeFlagsToGroup(parser)

  def Run(self, args):
    env_resource = args.CONCEPTS.environment.Parse()
    env_details = environments_api_util.Get(env_resource, self.ReleaseTrack())
    if (
        args.airflow_version or args.image_version
    ) and image_versions_command_util.IsDefaultImageVersion(args.image_version):
      message = image_versions_command_util.BuildDefaultComposerVersionWarning(
          args.image_version, args.airflow_version
      )
      log.warning(message)
    if args.airflow_version:
      # Converts airflow_version arg to image_version arg
      args.image_version = (
          image_versions_command_util.ImageVersionFromAirflowVersion(
              args.airflow_version,
              env_details.config.softwareConfig.imageVersion,
          )
      )

      # Checks validity of image_version upgrade request.
    if args.image_version:
      upgrade_validation = (
          image_versions_command_util.IsValidImageVersionUpgrade(
              env_details.config.softwareConfig.imageVersion, args.image_version
          )
      )
      if not upgrade_validation.upgrade_valid:
        raise command_util.InvalidUserInputError(upgrade_validation.error)

    operation = environments_api_util.CheckUpgrade(
        env_resource, args.image_version, release_track=self.ReleaseTrack())
    if args.async_:
      return self._AsynchronousExecution(env_resource, operation,
                                         args.image_version)
    else:
      return self._SynchronousExecution(env_resource, operation,
                                        args.image_version)

  def _AsynchronousExecution(self, env_resource, operation, image_version):
    details = 'to image {0} with operation [{1}]'.format(
        image_version, operation.name)
    # pylint: disable=protected-access
    # none of the log.CreatedResource, log.DeletedResource etc. matched
    log._PrintResourceChange(
        'check',
        env_resource.RelativeName(),
        kind='environment',
        is_async=True,
        details=details,
        failed=None)
    # pylint: enable=protected-access
    log.Print('If you want to see the result, run:')
    log.Print('gcloud composer operations describe ' + operation.name)

  def _SynchronousExecution(self, env_resource, operation, image_version):
    try:
      operations_api_util.WaitForOperation(
          operation,
          ('Waiting for [{}] to be checked for PyPI package conflicts when'
           ' upgrading to {}. Operation [{}]').format(
               env_resource.RelativeName(), image_version, operation.name),
          release_track=self.ReleaseTrack())

      completed_operation = operations_api_util.GetService(
          self.ReleaseTrack()).Get(
              api_util.GetMessagesModule(self.ReleaseTrack())
              .ComposerProjectsLocationsOperationsGetRequest(
                  name=operation.name))

      log.Print('\nIf you want to see the result once more, run:')
      log.Print('gcloud composer operations describe ' + operation.name + '\n')

      log.Print('If you want to see history of all operations to be able'
                ' to display results of previous check-upgrade runs, run:')
      log.Print('gcloud composer operations list\n')

      log.Print('Response: ')

      return completed_operation.response
    except command_util.Error as e:
      raise command_util.Error(
          ('Error while checking for PyPI package conflicts'
           ' [{}]: {}').format(env_resource.RelativeName(), six.text_type(e)))
