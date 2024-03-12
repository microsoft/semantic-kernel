# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""The gcloud run domain-mappings group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import platforms


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DomainMappings(base.Group):
  """View and manage your Cloud Run for Anthos domain mappings.

  This set of commands can be used to view and manage your service's domain
  mappings.

  To view and manage fully managed Cloud Run domain mappings, use
  `gcloud beta run domain-mappings`.
  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To list your Cloud Run domain mappings, run:

            $ {command} list
      """,
  }

  @staticmethod
  def Args(parser):
    """Adds --platform and the various related args."""
    flags.AddPlatformAndLocationFlags(parser, anthos_only=True)

  def Filter(self, context, args):
    """Runs before command.Run and validates platform with passed args."""
    # Ensures a platform is set on the run/platform property and
    # all other passed args are valid for this platform and release track.
    flags.GetAndValidatePlatform(args, self.ReleaseTrack(), flags.Product.RUN)
    self._CheckPlatform()
    return context

  def _CheckPlatform(self):
    if platforms.GetPlatform() == platforms.PLATFORM_MANAGED:
      raise exceptions.PlatformError(
          'This command group is in beta for fully managed Cloud Run; '
          'use `gcloud beta run domain-mappings`.')


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class DomainMappingsBeta(base.Group):
  """View and manage your Cloud Run domain mappings.

  This set of commands can be used to view and manage your service's domain
  mappings.
  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To list your Cloud Run domain mappings, run:

            $ {command} list
      """,
  }

  @staticmethod
  def Args(parser):
    """Adds --platform and the various related args."""
    flags.AddPlatformAndLocationFlags(parser)

  def _CheckPlatform(self):
    pass
