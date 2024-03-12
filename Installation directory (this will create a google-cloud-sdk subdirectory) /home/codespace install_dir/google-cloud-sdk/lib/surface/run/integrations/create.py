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
from googlecloudsdk.command_lib.runapps import exceptions


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.Command):
  """Create a Cloud Run Integration."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To create and attach a redis instance to a Cloud Run service

              $ {command} --type=redis --service=myservice

          To attach a custom domain to a Cloud Run service

              $ {command} --type=custom-domains --parameters='set-mapping=example.com/*:myservice'

         """,
  }

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    flags.AddTypeArg(parser)
    flags.AddNameArg(parser)
    flags.AddServiceCreateArg(parser)
    flags.AddParametersArg(parser)
    flags.AddServiceAccountArg(parser)

  def Run(self, args):
    """Creates a Cloud Run Integration."""

    integration_type = args.type
    service = args.service
    input_name = args.name
    parameters = flags.GetParameters(args)
    flags.ValidateCreateParameters(integration_type, parameters, service)
    flags.ValidateEnabledGcpApis(integration_type)
    release_track = self.ReleaseTrack()

    with run_apps_operations.Connect(args, release_track) as client:
      client.VerifyLocation()
      self._validateServiceNameAgainstIntegrations(
          client,
          integration_type=integration_type,
          service=service,
          integration_name=input_name,
      )
      integration_name = client.CreateIntegration(
          integration_type=integration_type,
          parameters=parameters,
          service=service,
          name=input_name,
      )
    resource = client.GetIntegrationGeneric(integration_name)
    resource_status = client.GetIntegrationStatus(resource.id)
    metadata = types_utils.GetTypeMetadata(integration_type)

    pretty_print.Info('')
    pretty_print.Success(
        messages_util.GetSuccessMessage(
            integration_type=integration_type,
            integration_name=integration_name,
            action='created',
        )
    )

    call_to_action = messages_util.GetCallToAction(
        metadata, resource, resource_status
    )
    if call_to_action:
      pretty_print.Info('')
      pretty_print.Info(call_to_action)
      pretty_print.Info(
          messages_util.CheckStatusMessage(release_track, integration_name)
      )

  def _validateServiceNameAgainstIntegrations(
      self, client, integration_type, integration_name, service
  ):
    """Checks if the service name matches an integration name."""
    if not service:
      return
    error = exceptions.ArgumentError(
        'Service name cannot be the same as '
        + 'the provided integration name or an '
        + 'existing integration name'
    )
    if service == integration_name:
      raise error
    integrations = client.ListIntegrations(integration_type, None)
    for integration in integrations:
      if integration.integration_name == service:
        raise error
