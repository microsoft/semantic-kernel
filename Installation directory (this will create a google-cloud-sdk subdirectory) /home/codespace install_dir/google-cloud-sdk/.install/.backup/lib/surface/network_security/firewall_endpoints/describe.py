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
"""Describe endpoint command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import activation_flags

DETAILED_HELP = {
    'DESCRIPTION': """
          Describe a firewall endpoint.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To get a description of a firewall endpoint called `my-endpoint` in
            zone `us-central1-a` and organization ID 1234, run:

            $ {command} my-endpoint --zone=us-central1-a --organization=1234

            OR

            $ {command} organizations/1234/locations/us-central1-a/firewallEndpoints/my-endpoint

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe a Firewall Plus endpoint."""

  @classmethod
  def Args(cls, parser):
    activation_flags.AddEndpointResource(cls.ReleaseTrack(), parser)

  def Run(self, args):
    client = activation_api.Client(self.ReleaseTrack())

    endpoint = args.CONCEPTS.firewall_endpoint.Parse()

    return client.DescribeEndpoint(endpoint.RelativeName())


Describe.detailed_help = DETAILED_HELP
