# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to describe a Fault in the Project/Location."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.fault_injection import faults
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.fault_injection import flags


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To List all faults, run:

          $ {command}
        """,
}

_FORMAT = """
  table(
    name.scope("faults"):label=NAME,
    name.scope("projects").segment(1):label=PROJECT,
    name.scope("locations").segment(0):label=LOCATION,
    description,
    action,
    createTime.date(unit=1000, tz_default=UTC)
  )
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Faults."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddListFaultFlags(parser)
    parser.display_info.AddFormat(_FORMAT)

  def Run(self, args):
    """Run the list command."""
    client = faults.FaultsClient()
    location_ref = args.CONCEPTS.location.Parse()
    return client.List(
        limit=args.limit,
        page_size=args.page_size,
        parent=location_ref.RelativeName(),
    )
