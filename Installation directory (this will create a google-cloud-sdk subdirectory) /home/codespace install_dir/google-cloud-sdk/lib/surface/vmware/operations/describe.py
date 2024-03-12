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
"""'vmware operations describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.operations import OperationsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Describe a VMware Engine operation. An operation contains information about the status of a previous request.
        """,
    'EXAMPLES':
        """
          To get details about an operation on a private cloud with the operation ID `operation-111-222-333-444`, run:

            $ {command} operation-111-222-333-444 --location=us-central1 --project=my-project

          Or:

            $ {command} operation-111-222-333-444 --location=us-central1

          In the second example, the location is taken from gcloud property compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Google Cloud VMware Engine operation."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddOperationArgToParser(parser)

  def Run(self, args):
    resource = args.CONCEPTS.operation.Parse()
    client = OperationsClient()
    return client.Get(resource)
