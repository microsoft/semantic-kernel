# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""The command group for the Cloud Recommender API CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Recommender(base.Group):
  """Manage Cloud recommendations and recommendation rules.

  Recommender allows you to retrieve recommendations for Cloud resources,
  helping you to improve security, save costs, and more. Each recommendation
  includes a suggested action, its justification, and its impact.
  Recommendations are grouped into a per-resource collection. To apply a
  recommendation, you must use the desired service's API, not the Recommender.
  Interact with and manage resources in Cloud Recommender.
  """
  category = base.API_PLATFORM_AND_ECOSYSTEMS_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190538831):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
