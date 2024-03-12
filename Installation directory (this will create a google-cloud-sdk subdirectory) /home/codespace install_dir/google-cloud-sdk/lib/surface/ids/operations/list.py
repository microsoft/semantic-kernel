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
"""'ids operations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ids import ids_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ids import flags
from googlecloudsdk.command_lib.util.args import common_args
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List Cloud IDS operation in a project.
        """,
    'EXAMPLES':
        """
          $ {command} --project=my-project

          The project is automatically read from the core/project property if it is defined.
    """,
}

_FORMAT = """\
table(
    name.scope("operations"):label=ID,
    name.scope("locations").segment(0):label=LOCATION,
    metadata.target,
    metadata.verb,
    done
)
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Cloud IDS operations."""

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(flags.MakeGetUriFunc(cls.ReleaseTrack()))
    common_args.ProjectArgument().AddToParser(parser)
    flags.AddZoneArg(
        parser, required=False, help_text='The zone of an operation')

  def Run(self, args):
    project = args.project or properties.VALUES.core.project.GetOrFail()
    zone = args.zone or '-'
    name = 'projects/{}/locations/{}'.format(project, zone)
    client = ids_api.Client(self.ReleaseTrack())
    return client.ListOperations(name, args.limit, args.page_size)


List.detailed_help = DETAILED_HELP
