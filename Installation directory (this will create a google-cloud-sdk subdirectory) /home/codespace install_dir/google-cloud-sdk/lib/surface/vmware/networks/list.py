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
"""'vmware networks list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.networks import NetworksClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.networks import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List VMware Engine networks.
        """,
    'EXAMPLES':
        """
          To list VMware Engine networks of type `STANDARD` in your project, run:

            $ {command} --location=global --project=my-project

          Or:

            $ {command}

          In the second example, the project is taken from gcloud properties core/project and the location is taken as `global`.

          To list VMware Engine networks of type `LEGACY` in the location `us-west2` in your project, run:

            $ {command} --location=us-west2 --project=my-project

          Or:

            $ {command} --location=us-west2

          In the last example, the project is taken from gcloud properties core/project. For VMware Engine networks of type `LEGACY`, you must always specify a region as the location.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Google Cloud VMware Engine networks."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLocationArgToParser(parser)
    parser.display_info.AddFormat('table(name.segment(-1):label=NAME,'
                                  'name.segment(-5):label=PROJECT,'
                                  'name.segment(-3):label=LOCATION,'
                                  'createTime,state,type)')

  def Run(self, args):
    location = args.CONCEPTS.location.Parse()

    client = NetworksClient()
    return client.List(location)
