# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Commands for managing Compute Engine network endpoint groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class NetworkEndpointGroups(base.Group):
  """Read and manipulate Compute Engine network endpoint groups."""

  category = base.NETWORKING_CATEGORY


NetworkEndpointGroups.detailed_help = {
    'DESCRIPTION': """
        Read and manipulate network endpoint groups.

        For more information about network endpoint groups, see the
        [network endpoint groups documentation](https://cloud.google.com/load-balancing/docs/negs/).

        See also: [Network endpoint groups API](https://cloud.google.com/compute/docs/reference/rest/v1/networkEndpointGroups).
    """,
}
