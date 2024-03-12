# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run.integrations import flags
from googlecloudsdk.command_lib.run.integrations import messages_util
from googlecloudsdk.command_lib.run.integrations import run_apps_operations
from googlecloudsdk.command_lib.runapps import exceptions
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Delete(base.Command):
  """Delete a Cloud Run Integration and its associated resources."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To delete a redis integration and the associated resources

              $ {command} my-redis-integration

         """,
  }

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    flags.AddNamePositionalArg(parser)
    flags.AddServiceAccountArg(parser)

  def Run(self, args):
    """Delete a Cloud Run Integration."""
    integration_name = args.name
    release_track = self.ReleaseTrack()

    console_io.PromptContinue(
        message=(
            'Integration [{}] will be deleted. '
            'This will also delete any resources this integration created.'
        ).format(integration_name),
        throw_if_unattended=True,
        cancel_on_no=True,
    )

    with run_apps_operations.Connect(args, release_track) as client:
      client.VerifyLocation()
      try:
        integration_type = client.DeleteIntegration(name=integration_name)
      except exceptions.IntegrationsOperationError as err:
        pretty_print.Info(messages_util.GetDeleteErrorMessage(integration_name))
        raise err
      else:
        pretty_print.Info('')
        pretty_print.Success(
            messages_util.GetSuccessMessage(
                integration_type=integration_type,
                integration_name=integration_name,
                action='deleted',
            )
        )
