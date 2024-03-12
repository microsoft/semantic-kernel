# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Commands for reading and manipulating security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class NetworkEdgeSecurityServices(base.Group):
  """Read and manipulate network edge security services."""
  pass


NetworkEdgeSecurityServices.category = base.LOAD_BALANCING_CATEGORY

NetworkEdgeSecurityServices.detailed_help = {
    'DESCRIPTION':
        """
       Read and manipulate network edge security services.

       Network edge security services are used to protect network load balancing
       resources and instances with external IPs.

       For example, to add advanced protection for a given region, create a
       network edge security service in that region and attach a security policy
       with ADVANCED DDoS protection enabled.
    """,
}
