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

"""deployments create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.api_lib.deployment_manager import exceptions as dm_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.deployment_manager import alpha_flags
from googlecloudsdk.command_lib.deployment_manager import dm_util
from googlecloudsdk.command_lib.deployment_manager import dm_write
from googlecloudsdk.command_lib.deployment_manager import flags
from googlecloudsdk.command_lib.deployment_manager import importer
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
import six

# Number of seconds (approximately) to wait for create operation to complete.
OPERATION_TIMEOUT = 20 * 60  # 20 mins


@base.UnicodeIsSupported
@base.ReleaseTracks(base.ReleaseTrack.GA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2)
class Create(base.CreateCommand, dm_base.DmCommand):
  """Create a deployment.

  This command inserts (creates) a new deployment based on a provided config
  file.
  """

  detailed_help = {
      'EXAMPLES': """
To create a new deployment from a top-level YAML file, run:

  $ {command} my-deployment --config=config.yaml --description="My deployment"

To create a new deployment from a top-level template file, run:

  $ gcloud deployment-manager deployments create my-deployment \
  --template=template.{jinja|py} \
  --properties="string-key:'string-value',integer-key:12345"

To create a new deployment directly from a composite type, run:

  $ gcloud deployment-manager deployments create my-deployment \
  --composite-type=<project-id>/composite:<type-name> \
  --properties="string-key:'string-value',integer-key:12345"

To preview a deployment without actually creating resources, run:

  $ {command} my-new-deployment --config=config.yaml --preview

To instantiate a deployment that has been previewed, issue an update command for that deployment without specifying a config file.

More information is available at https://cloud.google.com/deployment-manager/docs/configuration/.
""",
  }

  _create_policy_flag_map = arg_utils.ChoiceEnumMapper(
      '--create-policy',
      (apis.GetMessagesModule('deploymentmanager', 'v2beta')
       .DeploymentmanagerDeploymentsUpdateRequest.CreatePolicyValueValuesEnum),
      help_str='Create policy for resources that have changed in the update',
      default='create-or-acquire')

  @staticmethod
  def Args(parser, version=base.ReleaseTrack.GA):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
      version: The version this tool is running as. base.ReleaseTrack.GA
          is the default.
    """
    group = parser.add_mutually_exclusive_group()

    config_group = parser.add_mutually_exclusive_group(required=True)

    flags.AddConfigFlags(config_group)
    flags.AddAsyncFlag(group)
    flags.AddDeploymentNameFlag(parser)
    flags.AddPropertiesFlag(parser)
    labels_util.AddCreateLabelsFlags(parser)

    group.add_argument(
        '--automatic-rollback-on-error',
        help='If the create request results in a deployment with resource '
        'errors, delete that deployment immediately after creation. '
        '(default=False)',
        dest='automatic_rollback',
        default=False,
        action='store_true')

    parser.add_argument(
        '--description',
        help='Optional description of the deployment to insert.',
        dest='description')

    parser.add_argument(
        '--preview',
        help='Preview the requested create without actually instantiating the '
        'underlying resources. (default=False)',
        dest='preview',
        default=False,
        action='store_true')

    parser.display_info.AddFormat(flags.RESOURCES_AND_OUTPUTS_FORMAT)

  def Epilog(self, resources_were_displayed):
    """Called after resources are displayed if the default format was used.

    Args:
      resources_were_displayed: True if resources were displayed.
    """
    if not resources_were_displayed:
      log.status.Print('No resources or outputs found in your deployment.')

  def Run(self, args):
    """Run 'deployments create'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      If --async=true, returns Operation to poll.
      Else, returns a struct containing the list of resources and list of
        outputs in the deployment.

    Raises:
      HttpException: An http error response was received while executing api
          request.
      ConfigError: Config file could not be read or parsed, or the
          deployment creation operation encountered an error.
    """
    deployment_ref = self.resources.Parse(
        args.deployment_name,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='deploymentmanager.deployments')
    if (not args.IsSpecified('format')) and (args.async_):
      args.format = flags.OPERATION_FORMAT

    deployment = self.messages.Deployment(
        name=deployment_ref.deployment,
        target=importer.BuildTargetConfig(self.messages,
                                          config=args.config,
                                          template=args.template,
                                          composite_type=args.composite_type,
                                          properties=args.properties)

    )

    self._SetMetadata(args, deployment)

    try:
      operation = self.client.deployments.Insert(
          self._BuildRequest(
              args=args, project=dm_base.GetProject(), deployment=deployment))

      # Fetch and print the latest fingerprint of the deployment.
      fingerprint = dm_api_util.FetchDeploymentFingerprint(
          self.client,
          self.messages,
          dm_base.GetProject(),
          deployment_ref.deployment)
      dm_util.PrintFingerprint(fingerprint)

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
            operation_description='create',
            project=dm_base.GetProject(),
            timeout=OPERATION_TIMEOUT)
        dm_util.LogOperationStatus(operation, 'Create')
      except apitools_exceptions.HttpError as error:
        # TODO(b/37911296): Use gcloud default error handling.
        raise exceptions.HttpException(error, dm_api_util.HTTP_ERROR_FORMAT)
      except dm_exceptions.OperationError as error:
        response = self._HandleOperationError(error,
                                              args,
                                              operation,
                                              dm_base.GetProject(),
                                              deployment_ref)
        if getattr(args, 'automatic_rollback', False):
          args.format = flags.OPERATION_FORMAT
        return response

      return dm_api_util.FetchResourcesAndOutputs(self.client, self.messages,
                                                  dm_base.GetProject(),
                                                  deployment_ref.deployment)

  def _BuildRequest(self,
                    args,
                    project,
                    deployment,
                    supports_create_policy=False):
    request = self.messages.DeploymentmanagerDeploymentsInsertRequest(
        project=project, deployment=deployment, preview=args.preview)
    if supports_create_policy and args.create_policy:
      parsed_create_flag = Create._create_policy_flag_map.GetEnumForChoice(
          args.create_policy).name
      request.createPolicy = (
          self.messages.DeploymentmanagerDeploymentsInsertRequest.
          CreatePolicyValueValuesEnum(parsed_create_flag))
    return request

  def _HandleOperationError(
      self, error, args, operation, project, deployment_ref):
    if args.automatic_rollback:
      delete_operation = self._PerformRollback(deployment_ref.deployment,
                                               six.text_type(error))
      create_operation = dm_api_util.GetOperation(self.client, self.messages,
                                                  operation, project)

      return [create_operation, delete_operation]

    raise error

  def _SetMetadata(self, args, deployment):
    if args.description:
      deployment.description = args.description
    label_dict = labels_util.GetUpdateLabelsDictFromArgs(args)
    if label_dict:
      deployment.labels = [
          self.messages.DeploymentLabelEntry(key=k, value=v)
          for k, v in sorted(six.iteritems(label_dict))
      ]

  def _PerformRollback(self, deployment_name, error_message):
    # Print information about the failure.
    log.warning('There was an error deploying '
                + deployment_name + ':\n' + error_message)

    log.status.Print('`--automatic-rollback-on-error` flag was supplied; '
                     'deleting failed deployment...')

    # Delete the deployment.
    try:
      delete_operation = self.client.deployments.Delete(
          self.messages.DeploymentmanagerDeploymentsDeleteRequest(
              project=dm_base.GetProject(),
              deployment=deployment_name,
          )
      )
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, dm_api_util.HTTP_ERROR_FORMAT)

    # TODO(b/37481635): Use gcloud default operation polling.
    dm_write.WaitForOperation(self.client,
                              self.messages,
                              delete_operation.name,
                              'delete',
                              dm_base.GetProject(),
                              timeout=OPERATION_TIMEOUT)

    completed_operation = dm_api_util.GetOperation(self.client,
                                                   self.messages,
                                                   delete_operation,
                                                   dm_base.GetProject())
    return completed_operation


@base.UnicodeIsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@dm_base.UseDmApi(dm_base.DmApiVersion.ALPHA)
class CreateAlpha(Create):
  """Create a deployment.

  This command inserts (creates) a new deployment based on a provided config
  file.
  """

  @staticmethod
  def Args(parser):
    Create.Args(parser, version=base.ReleaseTrack.ALPHA)
    alpha_flags.AddCredentialFlag(parser)
    parser.display_info.AddFormat(alpha_flags.RESOURCES_AND_OUTPUTS_FORMAT)
    Create._create_policy_flag_map.choice_arg.AddToParser(parser)

  def _SetMetadata(self, args, deployment):
    if args.credential:
      deployment.credential = dm_util.CredentialFrom(self.messages,
                                                     args.credential)
    super(CreateAlpha, self)._SetMetadata(args, deployment)

  def _BuildRequest(self, args, project, deployment):
    return super(CreateAlpha, self)._BuildRequest(
        args=args,
        project=project,
        deployment=deployment,
        supports_create_policy=True)


@base.UnicodeIsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2BETA)
class CreateBeta(Create):
  """Create a deployment.

  This command inserts (creates) a new deployment based on a provided config
  file.
  """

  @staticmethod
  def Args(parser):
    Create.Args(parser, version=base.ReleaseTrack.BETA)
    Create._create_policy_flag_map.choice_arg.AddToParser(parser)

  def _BuildRequest(self, args, project, deployment):
    return super(CreateBeta, self)._BuildRequest(
        args=args,
        project=project,
        deployment=deployment,
        supports_create_policy=True)
