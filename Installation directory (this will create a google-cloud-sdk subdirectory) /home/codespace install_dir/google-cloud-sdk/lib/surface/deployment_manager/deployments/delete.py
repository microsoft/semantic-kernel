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

"""deployments delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deployment_manager import dm_util
from googlecloudsdk.command_lib.deployment_manager import dm_write
from googlecloudsdk.command_lib.deployment_manager import flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

# Number of seconds (approximately) to wait for each delete operation to
# complete.
OPERATION_TIMEOUT = 20 * 60  # 20 mins


@dm_base.UseDmApi(dm_base.DmApiVersion.V2)
class Delete(base.DeleteCommand, dm_base.DmCommand):
  """Delete a deployment.

  This command deletes a deployment and deletes all associated resources.
  """

  detailed_help = {
      'EXAMPLES': """
To delete a deployment, run:

  $ {command} my-deployment

To issue a delete command without waiting for the operation to complete, run:

  $ {command} my-deployment --async

To delete several deployments, run:

  $ {command} my-deployment-one my-deployment-two my-deployment-three

To disable the confirmation prompt on delete, run:

  $ {command} my-deployment -q
""",
  }

  _delete_policy_flag_map = flags.GetDeleteFlagEnumMap(
      (apis.GetMessagesModule('deploymentmanager', 'v2')
       .DeploymentmanagerDeploymentsDeleteRequest.DeletePolicyValueValuesEnum))

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('deployment_name', nargs='+', help='Deployment name.')
    Delete._delete_policy_flag_map.choice_arg.AddToParser(parser)
    flags.AddAsyncFlag(parser)

  def Run(self, args):
    """Run 'deployments delete'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      If --async=true, returns Operation to poll.
      Else, returns boolean indicating whether insert operation succeeded.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    prompt_message = ('The following deployments will be deleted:\n- '
                      + '\n- '.join(args.deployment_name))
    if not args.quiet:
      if not console_io.PromptContinue(message=prompt_message, default=False):
        raise exceptions.OperationError('Deletion aborted by user.')

    operations = []
    errors = []
    for deployment_name in args.deployment_name:
      deployment_ref = self.resources.Parse(
          deployment_name,
          params={'project': properties.VALUES.core.project.GetOrFail},
          collection='deploymentmanager.deployments')
      try:
        operation = self.client.deployments.Delete(
            self.messages.DeploymentmanagerDeploymentsDeleteRequest(
                project=dm_base.GetProject(),
                deployment=deployment_ref.deployment,
                deletePolicy=(Delete._delete_policy_flag_map.
                              GetEnumForChoice(args.delete_policy)),
            )
        )
        if args.async_:
          operations.append(operation)
        else:
          op_name = operation.name
          try:
            # TODO(b/62720778): Refactor to use waiter.CloudOperationPoller
            operation = dm_write.WaitForOperation(
                self.client,
                self.messages,
                op_name,
                'delete',
                dm_base.GetProject(),
                timeout=OPERATION_TIMEOUT)
            dm_util.LogOperationStatus(operation, 'Delete')
          except exceptions.OperationError as e:
            errors.append(exceptions.OperationError(
                'Delete operation {0} failed.\n{1}'.format(op_name, e)))
          completed_operation = self.client.operations.Get(
              self.messages.DeploymentmanagerOperationsGetRequest(
                  project=dm_base.GetProject(),
                  operation=op_name,
              )
          )
          operations.append(completed_operation)
      except apitools_exceptions.HttpError as error:
        errors.append(api_exceptions.HttpException(
            error, dm_api_util.HTTP_ERROR_FORMAT))

    if errors:
      raise core_exceptions.MultiError(errors)
    return operations
