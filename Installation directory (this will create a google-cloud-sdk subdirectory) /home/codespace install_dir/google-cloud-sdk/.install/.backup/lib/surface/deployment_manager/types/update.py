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

"""types update command."""

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
  log.UpdatedResource(request.compositeType,
                      kind='composite_type',
                      is_async=is_async)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2BETA)
class Update(base.UpdateCommand, dm_base.DmCommand):
  """Update a composite type."""

  detailed_help = {
      'EXAMPLES': """
To update a composite type, run:

  $ {command} my-composite-type --status=EXPERIMENTAL --description="My type."
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
    composite_types.AddDescriptionFlag(parser)
    composite_types.AddStatusFlag(parser)
    labels_util.AddUpdateLabelsFlags(parser, enable_clear=False)

  def Run(self, args):
    """Run 'types update'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    composite_type_ref = composite_types.GetReference(self.resources, args.name)
    get_request = self.messages.DeploymentmanagerCompositeTypesGetRequest(
        project=composite_type_ref.project,
        compositeType=args.name)
    existing_ct = self.client.compositeTypes.Get(get_request)

    labels = dm_labels.UpdateLabels(
        existing_ct.labels,
        self.messages.CompositeTypeLabelEntry,
        labels_util.GetUpdateLabelsDictFromArgs(args),
        labels_util.GetRemoveLabelsListFromArgs(args))

    computed_status = self.messages.CompositeType.StatusValueValuesEnum(
        args.status) if args.status is not None else None

    composite_type = self.messages.CompositeType(
        name=args.name,
        description=args.description,
        status=computed_status,
        templateContents=existing_ct.templateContents,
        labels=labels)

    update_request = self.messages.DeploymentmanagerCompositeTypesUpdateRequest(
        project=composite_type_ref.project,
        compositeType=args.name,
        compositeTypeResource=composite_type)

    response = dm_write.Execute(self.client, self.messages, self.resources,
                                update_request, args.async_,
                                self.client.compositeTypes.Update, LogResource)
    dm_util.LogOperationStatus(response, 'Update')
