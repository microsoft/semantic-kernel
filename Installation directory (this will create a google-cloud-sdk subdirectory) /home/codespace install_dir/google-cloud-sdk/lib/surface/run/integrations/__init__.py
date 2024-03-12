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
"""The gcloud run integrations group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.runapps import exceptions
from googlecloudsdk.command_lib.runapps import flags


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA)
class Integrations(base.Group):
  """View and manage your Cloud Run (fully managed) integrations.

  This set of commands can be used to view and manage your Cloud Run
  integrations.
  """

  detailed_help = {
      'EXAMPLES': """
          To list your existing integrations, run:

            $ {command} list
      """,
  }

  @staticmethod
  def Args(parser):
    """Adds --region flag."""
    flags.AddRegionArg(parser)

  def Filter(self, context, args):
    """Runs before command.Run and validates platform with passed args.

    Args:
      context: {str:object}, A set of key-value pairs that can be used for
          common initialization among commands.
      args: argparse.Namespace: The same namespace given to the corresponding
          .Run() invocation.

    Returns:
      The updated context
    """
    del args  # Unused argument
    self._CheckPlatform()
    return context

  def _CheckPlatform(self):
    platform = platforms.GetPlatform()
    if platform != platforms.PLATFORM_MANAGED:
      raise exceptions.PlatformError(
          'This command group is only supported for Cloud Run (fully managed).')
