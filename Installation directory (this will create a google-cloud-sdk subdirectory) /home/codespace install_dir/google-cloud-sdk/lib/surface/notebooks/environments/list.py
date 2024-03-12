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
"""'notebooks environments list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.notebooks import environments as env_util
from googlecloudsdk.api_lib.notebooks import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.command_lib.notebooks import flags
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION':
        """
        Request for listing environments.
    """,
    'EXAMPLES':
        """
    To list environments in location 'us-central1-a', run:

      $ {command} --location=us-central1-a
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Request for listing environments."""

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    parser.display_info.AddFormat("""
        table(name.segment(-1),
        name.segment(-3):label=LOCATION,
        name.segment(-5):label=PROJECT,
        vmImage.imageFamily,
        vmImage.imageName,
        containerImage.repository)
    """)
    parser.display_info.AddUriFunc(env_util.GetEnvironmentURI)
    flags.AddListEnvironmentFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    release_track = self.ReleaseTrack()
    client = util.GetClient(release_track)
    messages = util.GetMessages(release_track)
    if (not args.IsSpecified('location')) and (
        not properties.VALUES.notebooks.location.IsExplicitlySet()):
      raise parser_errors.RequiredError(argument='--location')

    environment_service = client.projects_locations_environments
    return list_pager.YieldFromList(
        environment_service,
        env_util.CreateEnvironmentListRequest(args, messages),
        field='environments',
        limit=args.limit,
        batch_size_attribute='pageSize')


List.detailed_help = DETAILED_HELP
