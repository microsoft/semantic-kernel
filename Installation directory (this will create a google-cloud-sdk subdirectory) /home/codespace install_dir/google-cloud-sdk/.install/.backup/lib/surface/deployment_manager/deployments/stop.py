# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""deployments stop command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.deployment_manager import dm_util
from googlecloudsdk.command_lib.deployment_manager import dm_write
from googlecloudsdk.command_lib.deployment_manager import flags

# Number of seconds (approximately) to wait for stop operation to complete.
OPERATION_TIMEOUT = 20 * 60  # 20 mins


@dm_base.UseDmApi(dm_base.DmApiVersion.V2)
class Stop(base.Command, dm_base.DmCommand):
  """Stop a pending or running deployment update or creation.

  This command will stop a currently running or pending operation on
  a deployment.
  """

  detailed_help = {
      'EXAMPLES': """
To stop a running operation on a deployment, run:

  $ {command} my-deployment

To issue a stop command without waiting for the operation to complete, run:

  $ {command} my-deployment --async

To stop a running operation on a deployment providing a fingerprint, run:

  $ {command} my-deployment --fingerprint=deployment-fingerprint
""",
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.AddAsyncFlag(parser)
    flags.AddDeploymentNameFlag(parser)
    flags.AddFingerprintFlag(parser)

  def Run(self, args):
    """Run 'deployments stop'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      If --async=true, returns Operation to poll.
      Else, returns boolean indicating whether stop operation succeeded.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    if args.fingerprint:
      fingerprint = dm_util.DecodeFingerprint(args.fingerprint)
    else:
      # If no fingerprint is present, default to an empty fingerprint.
      # TODO(b/34966984): Remove the empty default after cleaning up all
      # deployments that has no fingerprint
      fingerprint = dm_api_util.FetchDeploymentFingerprint(
          self.client,
          self.messages,
          dm_base.GetProject(),
          args.deployment_name) or b''
    try:
      operation = self.client.deployments.Stop(
          self.messages.DeploymentmanagerDeploymentsStopRequest(
              project=dm_base.GetProject(),
              deployment=args.deployment_name,
              deploymentsStopRequest=(
                  self.messages.DeploymentsStopRequest(
                      fingerprint=fingerprint)
              ),
          )
      )
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, dm_api_util.HTTP_ERROR_FORMAT)
    if args.async_:
      return operation
    else:
      op_name = operation.name
      try:
        operation = dm_write.WaitForOperation(
            self.client,
            self.messages,
            op_name,
            'stop',
            dm_base.GetProject(),
            timeout=OPERATION_TIMEOUT)
        dm_util.LogOperationStatus(operation, 'Stop')
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, dm_api_util.HTTP_ERROR_FORMAT)
      try:
        # Fetch a list of the stopped resources.
        response = self.client.resources.List(
            self.messages.DeploymentmanagerResourcesListRequest(
                project=dm_base.GetProject(),
                deployment=args.deployment_name,
            )
        )
        # TODO(b/36055861): Pagination
        return response.resources if response.resources else []
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, dm_api_util.HTTP_ERROR_FORMAT)
