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

"""deployments update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.api_lib.deployment_manager import dm_labels
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

# Number of seconds (approximately) to wait for update operation to complete.
OPERATION_TIMEOUT = 20 * 60  # 20 mins


@base.UnicodeIsSupported
@base.ReleaseTracks(base.ReleaseTrack.GA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2)
class Update(base.UpdateCommand, dm_base.DmCommand):
  """Update a deployment based on a provided config file.

  This command will update a deployment with the new config file provided.
  Different policies for create, update, and delete policies can be specified.
  """

  detailed_help = {
      'EXAMPLES': """
To update an existing deployment with a new config YAML file, run:

  $ {command} my-deployment --config=new_config.yaml

To update an existing deployment with a new config template file, run:

  $ {command} my-deployment --template=new_config.{jinja|py}

To update an existing deployment with a composite type as a new config, run:

  $ {command} my-deployment --composite-type=<project-id>/composite:<new-config>


To preview an update to an existing deployment without actually modifying the resources, run:

  $ {command} my-deployment --config=new_config.yaml --preview

To apply an update that has been previewed, provide the name of the previewed deployment, and no config file:

  $ {command} my-deployment

To specify different create, update, or delete policies, include any subset of the following flags:

  $ {command} my-deployment --config=new_config.yaml --create-policy=acquire --delete-policy=abandon

To perform an update without waiting for the operation to complete, run:

  $ {command} my-deployment --config=new_config.yaml --async

To update an existing deployment with a new config file and a fingerprint, run:

  $ {command} my-deployment --config=new_config.yaml --fingerprint=deployment-fingerprint

Either the `--config`, `--template`, or `--composite-type` flag is required unless launching an already-previewed update to a deployment. If you want to update a deployment's metadata, such as the labels or description, you must run a separate command with `--update-labels`, `--remove-labels`, or `--description`, as applicable.

More information is available at https://cloud.google.com/deployment-manager/docs/deployments/updating-deployments.
""",
  }

  _delete_policy_flag_map = flags.GetDeleteFlagEnumMap(
      (apis.GetMessagesModule('deploymentmanager', 'v2')
       .DeploymentmanagerDeploymentsUpdateRequest.DeletePolicyValueValuesEnum))

  _create_policy_flag_map = arg_utils.ChoiceEnumMapper(
      '--create-policy',
      (apis.GetMessagesModule('deploymentmanager', 'v2')
       .DeploymentmanagerDeploymentsUpdateRequest.CreatePolicyValueValuesEnum),
      help_str='Create policy for resources that have changed in the update',
      default='create-or-acquire')

  _create_policy_v2beta_flag_map = arg_utils.ChoiceEnumMapper(
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
    flags.AddDeploymentNameFlag(parser)
    flags.AddPropertiesFlag(parser)
    flags.AddAsyncFlag(parser)

    parser.add_argument(
        '--description',
        help='The new description of the deployment.',
        dest='description'
    )

    group = parser.add_mutually_exclusive_group()
    flags.AddConfigFlags(group)

    if version in [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]:
      group.add_argument(
          '--manifest-id',
          help='Manifest Id of a previous deployment. '
          'This flag cannot be used with --config.',
          dest='manifest_id')

    labels_util.AddUpdateLabelsFlags(parser, enable_clear=False)

    parser.add_argument(
        '--preview',
        help='Preview the requested update without making any changes to the '
        'underlying resources. (default=False)',
        dest='preview',
        default=False,
        action='store_true')

    if version in [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]:
      Update._create_policy_v2beta_flag_map.choice_arg.AddToParser(parser)
    else:
      Update._create_policy_flag_map.choice_arg.AddToParser(parser)

    Update._delete_policy_flag_map.choice_arg.AddToParser(parser)
    flags.AddFingerprintFlag(parser)

    parser.display_info.AddFormat(flags.RESOURCES_AND_OUTPUTS_FORMAT)

  def Epilog(self, resources_were_displayed):
    """Called after resources are displayed if the default format was used.

    Args:
      resources_were_displayed: True if resources were displayed.
    """
    if not resources_were_displayed:
      log.status.Print('No resources or outputs found in your deployment.')

  def Run(self, args):
    """Run 'deployments update'.

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
    """
    deployment_ref = self.resources.Parse(
        args.deployment_name,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='deploymentmanager.deployments')
    if not args.IsSpecified('format') and args.async_:
      args.format = flags.OPERATION_FORMAT

    patch_request = False
    deployment = self.messages.Deployment(
        name=deployment_ref.deployment,
    )

    if not (args.config is None and args.template is None
            and args.composite_type is None):
      deployment.target = importer.BuildTargetConfig(
          self.messages,
          config=args.config,
          template=args.template,
          composite_type=args.composite_type,
          properties=args.properties)
    elif (self.ReleaseTrack() in [base.ReleaseTrack.ALPHA,
                                  base.ReleaseTrack.BETA]
          and args.manifest_id):
      deployment.target = importer.BuildTargetConfigFromManifest(
          self.client, self.messages,
          dm_base.GetProject(),
          deployment_ref.deployment, args.manifest_id, args.properties)
    # Get the fingerprint from the deployment to update.
    try:
      current_deployment = self.client.deployments.Get(
          self.messages.DeploymentmanagerDeploymentsGetRequest(
              project=dm_base.GetProject(),
              deployment=deployment_ref.deployment
          )
      )

      if args.fingerprint:
        deployment.fingerprint = dm_util.DecodeFingerprint(args.fingerprint)
      else:
        # If no fingerprint is present, default to an empty fingerprint.
        # TODO(b/34966984): Remove the empty default after cleaning up all
        # deployments that has no fingerprint
        deployment.fingerprint = current_deployment.fingerprint or b''

      # Get the credential from the deployment to update.
      if self.ReleaseTrack() in [base.ReleaseTrack.ALPHA] and args.credential:
        deployment.credential = dm_util.CredentialFrom(self.messages,
                                                       args.credential)

      # Update the labels of the deployment

      deployment.labels = self._GetUpdatedDeploymentLabels(
          args, current_deployment)
      # If no config or manifest_id are specified, but try to update labels,
      # only add patch_request header when directly updating a non-previewed
      # deployment

      no_manifest = (self.ReleaseTrack() is
                     base.ReleaseTrack.GA) or not args.manifest_id
      patch_request = not args.config and no_manifest and (
          bool(args.update_labels) or bool(args.remove_labels))
      if args.description is None:
        deployment.description = current_deployment.description
      elif not args.description or args.description.isspace():
        deployment.description = None
      else:
        deployment.description = args.description
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, dm_api_util.HTTP_ERROR_FORMAT)

    if patch_request:
      args.format = flags.DEPLOYMENT_FORMAT
    try:
      # Necessary to handle API Version abstraction below
      parsed_delete_flag = Update._delete_policy_flag_map.GetEnumForChoice(
          args.delete_policy).name
      if self.ReleaseTrack() in [
          base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA
      ]:
        parsed_create_flag = (
            Update._create_policy_v2beta_flag_map.GetEnumForChoice(
                args.create_policy).name)
      else:
        parsed_create_flag = (
            Update._create_policy_flag_map.GetEnumForChoice(
                args.create_policy).name)
      request = self.messages.DeploymentmanagerDeploymentsUpdateRequest(
          deploymentResource=deployment,
          project=dm_base.GetProject(),
          deployment=deployment_ref.deployment,
          preview=args.preview,
          createPolicy=(self.messages.DeploymentmanagerDeploymentsUpdateRequest.
                        CreatePolicyValueValuesEnum(parsed_create_flag)),
          deletePolicy=(self.messages.DeploymentmanagerDeploymentsUpdateRequest.
                        DeletePolicyValueValuesEnum(parsed_delete_flag)))
      client = self.client
      client.additional_http_headers['X-Cloud-DM-Patch'] = six.text_type(
          patch_request)
      operation = client.deployments.Update(request)

      # Fetch and print the latest fingerprint of the deployment.
      updated_deployment = dm_api_util.FetchDeployment(
          self.client, self.messages, dm_base.GetProject(),
          deployment_ref.deployment)
      if patch_request:
        if args.async_:
          log.warning(
              'Updating Deployment metadata is synchronous, --async flag '
              'is ignored.')
        log.status.Print('Update deployment metadata completed successfully.')
        return updated_deployment
      dm_util.PrintFingerprint(updated_deployment.fingerprint)
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
            'update',
            dm_base.GetProject(),
            timeout=OPERATION_TIMEOUT)
        dm_util.LogOperationStatus(operation, 'Update')
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, dm_api_util.HTTP_ERROR_FORMAT)

      return dm_api_util.FetchResourcesAndOutputs(self.client, self.messages,
                                                  dm_base.GetProject(),
                                                  deployment_ref.deployment)

  def _GetUpdatedDeploymentLabels(self, args, deployment):
    update_labels = labels_util.GetUpdateLabelsDictFromArgs(args)
    remove_labels = labels_util.GetRemoveLabelsListFromArgs(args)
    return dm_labels.UpdateLabels(deployment.labels,
                                  self.messages.DeploymentLabelEntry,
                                  update_labels, remove_labels)


@base.UnicodeIsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@dm_base.UseDmApi(dm_base.DmApiVersion.ALPHA)
class UpdateAlpha(Update):
  """Update a deployment based on a provided config file.

  This command will update a deployment with the new config file provided.
  Different policies for create, update, and delete policies can be specified.
  """

  @staticmethod
  def Args(parser):
    Update.Args(parser, version=base.ReleaseTrack.ALPHA)
    alpha_flags.AddCredentialFlag(parser)
    parser.display_info.AddFormat(alpha_flags.RESOURCES_AND_OUTPUTS_FORMAT)


@base.UnicodeIsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2BETA)
class UpdateBeta(Update):
  """Update a deployment based on a provided config file.

  This command will update a deployment with the new config file provided.
  Different policies for create, update, and delete policies can be specified.
  """

  @staticmethod
  def Args(parser):
    Update.Args(parser, version=base.ReleaseTrack.BETA)
