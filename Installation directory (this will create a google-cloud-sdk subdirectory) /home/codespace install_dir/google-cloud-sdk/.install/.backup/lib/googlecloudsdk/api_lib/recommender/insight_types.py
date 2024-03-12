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
"""Utilities for Recommendation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.recommender import base
from googlecloudsdk.api_lib.recommender import flag_utils


def CreateClient(release_track):
  """Creates Client.

  Args:
    release_track: release_track value, can be ALPHA, BETA, GA

  Returns:
    The versioned client.
  """
  api_version = flag_utils.GetApiVersion(release_track)
  return InsightTypes(api_version)


class InsightTypes(base.ClientBase):
  """Base client to list Insight Types for all versions."""

  def __init__(self, api_version):
    super(InsightTypes, self).__init__(api_version)
    self._service = self._client.insightTypes

  def List(self, page_size, limit=None):
    """List Insight Types.

    Args:
      page_size: int, The number of items to retrieve per request.
      limit: int, The maximum number of records to yield.

    Returns:
      The list of insight types.
    """
    # Using Project message is ok for all entities if the name is correct.
    request = self._messages.RecommenderInsightTypesListRequest()
    return list_pager.YieldFromList(
        self._service,
        request,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        limit=limit,
        field='insightTypes')
