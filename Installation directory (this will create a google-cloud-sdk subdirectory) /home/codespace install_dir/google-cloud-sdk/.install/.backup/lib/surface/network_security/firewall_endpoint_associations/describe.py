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
"""Describe endpoint association command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.firewall_endpoint_associations import association_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import association_flags

DETAILED_HELP = {
    'DESCRIPTION': """
          Describe a firewall endpoint association.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To get a description of a firewall endpoint association called
            `my-association`, run:

              $ {command} my-association --zone=us-central1-a --project=my-project
              OR
              $ {command} projects/my-project/locations/us-central1-a/firewallEndpointAssociations/my-association

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe a Firewall Plus endpoint association."""

  @classmethod
  def Args(cls, parser):
    association_flags.AddAssociationResource(cls.ReleaseTrack(), parser)

  def Run(self, args):
    client = association_api.Client(self.ReleaseTrack())

    association = args.CONCEPTS.firewall_endpoint_association.Parse()

    return client.DescribeAssociation(association.RelativeName())


Describe.detailed_help = DETAILED_HELP
