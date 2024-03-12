# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command for listing Stacks resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.run.integrations import flags
from googlecloudsdk.command_lib.run.integrations import run_apps_operations


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Stacks resources."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          List all resources within the current project

              $ {command}

          List all resources of a particular type

              $ {command} --type=redis

          List all resources attached to a particular service

              $ {command} --service=my-service

         """,
  }

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    flags.ListIntegrationsOfService(parser)
    flags.ListIntegrationsOfType(parser)

  def Run(self, args):
    """Lists all the Stacks resources.

    All regions are listed by default similar to Cloud Run services unless
    a specific region is provided with the --region flag.

    Args:
      args: ArgumentParser, used to reference the inputs provided by the user.

    Returns:
      dict with a single key that maps to a list of resources.
      This will be used by the integration_list_printer to format all
      the entries in the list.

      The reason this is not a list is because the printer will only recieve
      one entry at a time and cannot easily format all entries into a table.
    """
    _SetFormat(args)
    resource_type = args.type
    service_name = args.service
    release_track = self.ReleaseTrack()
    region = (None if args.IsSpecified('region')
              else run_apps_operations.ALL_REGIONS)

    with run_apps_operations.Connect(args, release_track) as client:
      # If a region is specified via the --region flag then we need to validate
      # if the region is valid.  Otherwise fetch from all regions by default.
      if args.IsSpecified('region'):
        client.VerifyLocation()
      if resource_type:
        types_utils.CheckValidIntegrationType(resource_type)

      return client.ListIntegrations(resource_type, service_name, region)


def _SetFormat(namespace: parser_extensions.Namespace) -> None:
  columns = [
      # latest_deployment_status does not have a column name
      'formatted_latest_deployment_status:label=',
      'integration_name:label=NAME',
      'integration_type:label=TYPE',
      'region:label=REGION',
      'services:label=BINDINGS',
  ]
  namespace.GetDisplayInfo().AddFormat(
      'table({columns})'.format(columns=','.join(columns))
  )
