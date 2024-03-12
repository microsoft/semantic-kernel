# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""`gcloud tasks queues list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import list_formats
from googlecloudsdk.command_lib.tasks import parsers


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List all queues."""
  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To list all queues:

              $ {command}
         """,
  }

  @staticmethod
  def Args(parser):
    flags.AddLocationFlag(parser)
    list_formats.AddListQueuesFormats(parser)

  def Run(self, args):
    queues_client = GetApiAdapter(self.ReleaseTrack()).queues
    app_location = args.location or app.ResolveAppLocation(
        parsers.ParseProject())
    region_ref = parsers.ParseLocation(app_location)
    return queues_client.List(region_ref, args.limit, args.page_size)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaList(List):
  """List all queues."""

  @staticmethod
  def Args(parser):
    flags.AddLocationFlag(parser)
    list_formats.AddListQueuesFormats(parser, version=base.ReleaseTrack.ALPHA)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaList(List):
  """List all queues including their type."""

  @staticmethod
  def Args(parser):
    flags.AddLocationFlag(parser)
    list_formats.AddListQueuesFormats(parser, version=base.ReleaseTrack.BETA)
