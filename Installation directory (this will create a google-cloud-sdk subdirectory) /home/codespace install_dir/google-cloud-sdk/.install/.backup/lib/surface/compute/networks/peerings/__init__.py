# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Commands for reading and manipulating network peerings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Peerings(base.Group):
  """List, create, and delete, and update VPC Network Peering."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class PeeringsAlpha(base.Group):
  """List, create, delete, and update VPC Network Peering."""

Peerings.detailed_help = {
    'DESCRIPTION': """
        Read and manipulate VPC Network Peering connections.

        For more information about VPC Network Peering, see the
        [VPC Network Peering documentation](https://cloud.google.com/vpc/docs/vpc-peering).

        See also: [Network API](https://cloud.google.com/compute/docs/reference/rest/v1/networks).
    """,
}
