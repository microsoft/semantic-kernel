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
"""Fetches status of a long running operation."""

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
        'Get status of long running operation.',
    'EXAMPLES':
        textwrap.dedent("""\
        The following command fetches details of the operation with ID `abc`
        in organization with id `123` and location `us-west1`

        $ {command} organizations/123/locations/us-west1/operations/abc
        """)
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Operation(base.DescribeCommand):
  """Get status of long running operation."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.add_operation_flag(parser)

  def Run(self, args):
    operation_id = args.CONCEPTS.operation.Parse()
    location = operation_id.AsDict()['locationsId']
    with util.override_endpoint(location):
      client = api.SLZOverwatchClient()
      return client.Operation(operation_id.RelativeName())
