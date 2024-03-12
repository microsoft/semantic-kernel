# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""types create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.api_lib.deployment_manager import dm_labels
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deployment_manager import composite_types
from googlecloudsdk.command_lib.deployment_manager import dm_util
from googlecloudsdk.command_lib.deployment_manager import dm_write
from googlecloudsdk.command_lib.deployment_manager import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def LogResource(request, is_async):
  log.CreatedResource(request.compositeType.name,
                      kind='composite_type',
                      is_async=is_async)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2BETA)
class Create(base.CreateCommand, dm_base.DmCommand):
  """Create a type.

  This command inserts (creates) a new composite type based on a provided
  configuration file.
  """

  detailed_help = {
      'EXAMPLES': """
To create a new composite type, run:

  $ {command} my-composite-type --template=my-template.jinja --status=EXPERIMENTAL --description="My type."
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
    composite_types.AddCompositeTypeNameFlag(parser)
    composite_types.AddTemplateFlag(parser)
    composite_types.AddDescriptionFlag(parser)
    composite_types.AddStatusFlag(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    """Run 'types create'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    composite_type_ref = composite_types.GetReference(self.resources, args.name)
    update_labels_dict = labels_util.GetUpdateLabelsDictFromArgs(args)
    labels = dm_labels.UpdateLabels([],
                                    self.messages.CompositeTypeLabelEntry,
                                    update_labels=update_labels_dict)
    template_contents = composite_types.TemplateContentsFor(self.messages,
                                                            args.template)

    computed_status = self.messages.CompositeType.StatusValueValuesEnum(
        args.status) if args.status is not None else None

    composite_type = self.messages.CompositeType(
        name=args.name,
        description=args.description,
        status=computed_status,
        templateContents=template_contents,
        labels=labels)
    request = self.messages.DeploymentmanagerCompositeTypesInsertRequest(
        project=composite_type_ref.project,
        compositeType=composite_type)

    response = dm_write.Execute(self.client, self.messages, self.resources,
                                request, args.async_,
                                self.client.compositeTypes.Insert, LogResource)
    dm_util.LogOperationStatus(response, 'Create')
