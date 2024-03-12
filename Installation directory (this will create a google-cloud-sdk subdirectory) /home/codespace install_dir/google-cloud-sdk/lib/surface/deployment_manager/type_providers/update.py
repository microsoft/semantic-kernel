# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""type-providers update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.api_lib.deployment_manager import dm_labels
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deployment_manager import dm_write
from googlecloudsdk.command_lib.deployment_manager import flags
from googlecloudsdk.command_lib.deployment_manager import type_providers
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def LogResource(request, is_async):
  log.UpdatedResource(request.typeProvider,
                      kind='type_provider',
                      is_async=is_async)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2BETA)
class Update(base.UpdateCommand, dm_base.DmCommand):
  """Update a type provider.

  This command updates a type provider.
  """

  detailed_help = {
      'EXAMPLES': """\
          To update a type provider, run:

            $ {command} my-type-provider --api-options-file=my-options.yaml --descriptor-url=<descriptor URL> --description="My type."
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
    type_providers.AddTypeProviderNameFlag(parser)
    type_providers.AddApiOptionsFileFlag(parser)
    type_providers.AddDescriptionFlag(parser)
    type_providers.AddDescriptorUrlFlag(parser)
    type_providers.AddCustomCaCertificateFlag(parser)
    labels_util.AddUpdateLabelsFlags(parser, enable_clear=False)

  def Run(self, args):
    """Run 'type-providers update'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    type_provider_ref = type_providers.GetReference(self.resources,
                                                    args.provider_name)
    project = type_provider_ref.project
    name = type_provider_ref.typeProvider
    get_request = self.messages.DeploymentmanagerTypeProvidersGetRequest(
        project=project,
        typeProvider=name)

    existing_tp = self.client.typeProviders.Get(get_request)

    labels = dm_labels.UpdateLabels(
        existing_tp.labels,
        self.messages.TypeProviderLabelEntry,
        labels_util.GetUpdateLabelsDictFromArgs(args),
        labels_util.GetRemoveLabelsListFromArgs(args))
    type_provider = self.messages.TypeProvider(
        name=name,
        description=args.description,
        descriptorUrl=(args.
                       descriptor_url),
        customCertificateAuthorityRoots=args.custom_certificate_authority_roots,
        labels=labels)
    type_providers.AddOptions(self.messages,
                              args.api_options_file,
                              type_provider)

    update_request = self.messages.DeploymentmanagerTypeProvidersUpdateRequest(
        project=project,
        typeProvider=args.provider_name,
        typeProviderResource=type_provider)

    dm_write.Execute(self.client,
                     self.messages,
                     self.resources,
                     update_request,
                     args.async_,
                     self.client.typeProviders.Update,
                     LogResource)
