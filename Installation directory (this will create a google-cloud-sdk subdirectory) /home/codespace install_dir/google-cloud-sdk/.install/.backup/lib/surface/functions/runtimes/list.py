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
"""List runtimes available to Google Cloud Functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.v2.runtimes.list import command as command_v2


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List runtimes available to Google Cloud Functions."""

  detailed_help = {
      'EXAMPLES':
          """\
          To list the available runtimes, run:

            $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    parser.display_info.AddFormat("""
      table(
        name,
        stage,
        environments()
      )
    """)
    parser.display_info.AddUriFunc(flags.GetLocationsUri)

    flags.AddRegionFlag(
        parser, help_text='Only show runtimes within the region.')

  def Run(self, args):
    return command_v2.Run(args, self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List runtimes available to Google Cloud Functions."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """List runtimes available to Google Cloud Functions."""
