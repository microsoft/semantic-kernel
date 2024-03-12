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
"""'vmware node-types describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.nodetypes import NodeTypesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Display data associated with a VMware Engine node type, such as its compute, storage, and memory.
        """,
    'EXAMPLES':
        """
          To describe node type `standard-72` in location `us-west1-a`, run:

            $ {command} standard-72 --location=us-central1 --project=my-project

          Or:

            $ {command} standard-72

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Display data associated with a Google Cloud VMware Engine node type."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNodeTypeArgToParser(parser, positional=True)

  def Run(self, args):
    resource = args.CONCEPTS.node_type.Parse()
    client = NodeTypesClient()
    return client.Get(resource)
