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
"""'notebooks runtimes list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.notebooks import runtimes as runtime_util
from googlecloudsdk.api_lib.notebooks import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.command_lib.notebooks import flags
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION':
        """
        Request for listing runtimes.
    """,
    'EXAMPLES':
        """
    To list runtimes in a particular location, run:

        $ {command} --location=us-central1
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Request for listing runtimes."""

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    api_version = util.ApiVersionSelector(cls.ReleaseTrack())
    parser.display_info.AddFormat("""
        table(name.segment(-1),
        name.segment(-3):label=LOCATION,
        name.segment(-5):label=PROJECT,
        state,
        machineType.segment(-1),
        network.segment(-1),
        subnet.segment(-1))
    """)
    parser.display_info.AddUriFunc(runtime_util.GetRuntimeURI)
    flags.AddListRuntimeFlags(api_version, parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    release_track = self.ReleaseTrack()
    client = util.GetClient(release_track)
    messages = util.GetMessages(release_track)
    if (not args.IsSpecified('location')) and (
        not properties.VALUES.notebooks.location.IsExplicitlySet()):
      raise parser_errors.RequiredError(argument='--location')
    runtime_service = client.projects_locations_runtimes
    return list_pager.YieldFromList(
        runtime_service,
        runtime_util.CreateRuntimeListRequest(args, messages),
        field='runtimes',
        limit=args.limit,
        batch_size_attribute='pageSize')


List.detailed_help = DETAILED_HELP
