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
"""Command for creating or replacing an application from YAML specification."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run.integrations import flags
from googlecloudsdk.command_lib.run.integrations import messages_util
from googlecloudsdk.command_lib.run.integrations import run_apps_operations


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA)
class Update(base.Command):
  """Update a Cloud Run Integration."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To update a redis integration to change the cache size

              $ {command} redis-integration --parameters=memory-size-gb=5

         """,
  }

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    flags.AddNamePositionalArg(parser)
    flags.AddServiceUpdateArgs(parser)
    flags.AddParametersArg(parser)
    flags.AddServiceAccountArg(parser)

  def Run(self, args):
    """Update a Cloud Run Integration."""

    add_service = args.add_service
    remove_service = args.remove_service
    integration_name = args.name
    parameters = flags.GetParameters(args)
    release_track = self.ReleaseTrack()

    with run_apps_operations.Connect(args, release_track) as client:
      client.VerifyLocation()

      client.UpdateIntegration(
          name=integration_name,
          parameters=parameters,
          add_service=add_service,
          remove_service=remove_service)

      resource = client.GetIntegrationGeneric(integration_name)
      resource_status = client.GetIntegrationStatus(resource.id)
      metadata = types_utils.GetTypeMetadataByResource(resource)

      pretty_print.Info('')
      pretty_print.Success(
          messages_util.GetSuccessMessage(
              integration_type=metadata.integration_type,
              integration_name=integration_name,
              action='updated',
          )
      )

      call_to_action = messages_util.GetCallToAction(
          metadata, resource, resource_status
      )

      # Call to action should not be shown upon service removals.
      if call_to_action and not remove_service:
        pretty_print.Info('')
        pretty_print.Info(call_to_action)
        pretty_print.Info(
            messages_util.CheckStatusMessage(
                self.ReleaseTrack(), integration_name
            )
        )
