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
"""'vmware operations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.operations import OperationsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List VMware Engine operations in a location.
        """,
    'EXAMPLES':
        """
          To list VMware Engine operations in a location `us-west2-a`, run:

            $ {command} --location=us-west2-a

          Or:

            $ {command}

          In the second example, the location is taken from gcloud property compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Google Cloud VMware Engine operations."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLocationArgToParser(parser)
    parser.display_info.AddFormat("""\
            table(
          name.scope("operations"):label=ID,
          name.scope("locations").segment(0):label=LOCATION,
          metadata.target:label=TARGET,
          metadata.verb:label=NAME,
          done:label=DONE
      )""")

  def Run(self, args):
    location = args.CONCEPTS.location.Parse()
    client = OperationsClient()
    return client.List(location)
