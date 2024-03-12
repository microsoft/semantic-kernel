# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command for listing available Cloud Run (fully managed) regions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import commands


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(commands.List):
  """List available Cloud Run (fully managed) regions."""

  detailed_help = {
      'DESCRIPTION': """
          {description}
          """,
      'EXAMPLES': """
          To list available Cloud Run (fully managed) regions:

              $ {command}
          """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    parser.display_info.AddFormat(
        'table(locationId:label=NAME:sort=1):({alias})'.format(
            alias=commands.SUPPORTS_PZS_ALIAS
        )
    )
    parser.display_info.AddUriFunc(cls._GetResourceUri)

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def Run(self, args):
    """List available routes."""
    client = global_methods.GetServerlessClientInstance()
    self.SetPartialApiEndpoint(client.url)
    return global_methods.ListLocations(client)
