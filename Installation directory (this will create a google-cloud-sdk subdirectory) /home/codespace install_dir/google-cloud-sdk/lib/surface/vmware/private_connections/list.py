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
"""'vmware private-connections list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateconnections import PrivateConnectionsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Lists VMware Engine private connections.
        """,
    'EXAMPLES':
        """
          To list private connections in project `my-project` and region `us-west1` sorted from oldest to newest, run:

            $ {command} --location=us-west1 --project=my-project --sort-by=~create_time

          Or:

            $ {command}  --sort-by=~create_time

          In the second example, the project and the location are taken from gcloud properties core/project and compute/region, respectively.

          To list private connections in project `my-project` from all regions, run:

            $ {command} --location=- --project=my-project

          Or:

            $ {command} --location=-

          In the last example, the project is taken from gcloud properties core/project.
        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Google Cloud Private Connections."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLocationArgToParser(parser, regional=True)
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NAME,'
        'name.segment(-3):label=LOCATION,'
        'serviceNetwork.segment(-4):label=SERVICE_PROJECT_ID,'
        'type, state)')

  def Run(self, args):
    location = args.CONCEPTS.location.Parse()
    client = PrivateConnectionsClient()
    return client.List(location)
