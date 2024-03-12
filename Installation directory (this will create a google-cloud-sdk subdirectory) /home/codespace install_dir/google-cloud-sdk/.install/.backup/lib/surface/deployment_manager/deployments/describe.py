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

"""deployments describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.deployment_manager import alpha_flags
from googlecloudsdk.command_lib.deployment_manager import flags
from googlecloudsdk.core import properties


class _Results(object):
  """Encapsulate results into a single object to fit the Run() model."""

  def __init__(self, deployment, resources, outputs):
    self.deployment = deployment
    self.resources = resources
    self.outputs = outputs


@base.ReleaseTracks(base.ReleaseTrack.GA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2)
class Describe(base.DescribeCommand, dm_base.DmCommand):
  """Provide information about a deployment.

  This command prints out all available details about a deployment.
  """

  detailed_help = {
      'EXAMPLES': """\
          To display information about a deployment, run:

            $ {command} my-deployment
          """,
  }

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
    parser.display_info.AddFormat("""
              table(
                deployment:format='default(name, id, description, fingerprint,
                insertTime, manifest.basename(), labels, operation.operationType,
                operation.name, operation.progress, operation.status,
                operation.user, operation.endTime, operation.startTime,
                operation.error, operation.warnings, update)',
                resources:format='table(
                  name:label=NAME,
                  type:wrap:label=TYPE,
                  update.state.yesno(no="COMPLETED"),
                  update.intent)',
              outputs:format='table(
                name:label=OUTPUTS,
                finalValue:label=VALUE)'
             )
    """)

  def Run(self, args):
    """Run 'deployments describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The requested Deployment.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    deployment_ref = self.resources.Parse(
        args.deployment_name,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='deploymentmanager.deployments')
    try:
      deployment = self.client.deployments.Get(
          self.messages.DeploymentmanagerDeploymentsGetRequest(
              project=dm_base.GetProject(),
              deployment=deployment_ref.deployment))
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, dm_api_util.HTTP_ERROR_FORMAT)

    try:
      response = self.client.resources.List(
          self.messages.DeploymentmanagerResourcesListRequest(
              project=dm_base.GetProject(), deployment=deployment.name))
      resources = response.resources
      if self.ReleaseTrack() is base.ReleaseTrack.ALPHA:
        if (not args.IsSpecified('format')) and (deployment.update):
          args.format = (
              alpha_flags.PREVIEWED_DEPLOYMENT_AND_RESOURCES_AND_OUTPUTS_FORMAT)
    except apitools_exceptions.HttpError:
      # Couldn't get resources, skip adding them to the table.
      resources = None

    outputs = []

    manifest = dm_api_util.ExtractManifestName(deployment)

    if manifest:
      manifest_response = self.client.manifests.Get(
          self.messages.DeploymentmanagerManifestsGetRequest(
              project=dm_base.GetProject(),
              deployment=deployment_ref.deployment,
              manifest=manifest,
          )
      )
      # We might be lacking a layout if the manifest failed expansion.
      if manifest_response.layout:
        outputs = dm_api_util.FlattenLayoutOutputs(manifest_response.layout)

    return _Results(deployment, resources, outputs)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@dm_base.UseDmApi(dm_base.DmApiVersion.ALPHA)
class DescribeAlpha(Describe):
  """Provide information about a deployment.

  This command prints out all available details about a deployment.
  """

  @staticmethod
  def Args(parser):
    Describe.Args(parser, version=base.ReleaseTrack.ALPHA)
    parser.display_info.AddFormat(
        alpha_flags.DEPLOYMENT_AND_RESOURCES_AND_OUTPUTS_FORMAT)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  """Provide information about a deployment.

  This command prints out all available details about a deployment.
  """

  @staticmethod
  def Args(parser):
    Describe.Args(parser, version=base.ReleaseTrack.BETA)
