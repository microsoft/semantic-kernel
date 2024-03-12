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
"""Command to Create an Overwatch using blueprint plan."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.scc.slz_overwatch import overwatch as api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.slz_overwatch import overwatch_flags as flags
from googlecloudsdk.command_lib.scc.slz_overwatch import util

_DETAILED_HELP = {
    'BRIEF':
        'Create a Secured Landing Zone overwatch using the JSON file of '
        'blueprint plan.',
    'EXAMPLES':
        textwrap.dedent("""\
        The following command creates an overwatch with ID `overwatch01`
        under the organization with ID `123` and region `us-west1`
        using the blueprint plan file named `blueprint.json`.

        $ {command} organizations/123/locations/us-west1/overwatches/overwatch01 \
          --blueprint-plan-file=blueprint.json
        """)
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Create(base.Command):
  """Create an overwatch using blueprint plan."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.add_overwatch_path_flag(parser)
    flags.get_blueprint_plan_flag().AddToParser(parser)

  def Run(self, args):
    overwatch = args.CONCEPTS.overwatch.Parse()
    blueprint_base64 = util.base_64_encoding(args.blueprint_plan_file)
    location = overwatch.AsDict()['locationsId']
    with util.override_endpoint(location):
      client = api.SLZOverwatchClient()
      return client.Create(overwatch, blueprint_base64)
