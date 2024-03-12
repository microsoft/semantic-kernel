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
"""Command group for gke-fleet."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GkeFleet(base.Group):
  """Centrally manage Google opinionated Fleet configurations for GKE clusters.

  Manage Google opinionated Fleet configurations for GKE
  clusters.
  Fleet provides a centralized control-plane to managed features and services on
  all
  registered cluster.

  A registered cluster is always associated with a Membership, a resource
  within fleet.

  ## EXAMPLES

  Initialize GKE fleets:

    $ {command} init --help

  """

  category = base.COMPUTE_CATEGORY

  def Filter(self, context, args):
    """See base class."""
    base.RequireProjectID(args)
    return context
