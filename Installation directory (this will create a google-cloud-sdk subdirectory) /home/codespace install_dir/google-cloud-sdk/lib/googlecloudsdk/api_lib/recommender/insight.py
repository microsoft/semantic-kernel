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
"""Utilities for Insight."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.recommender import base
from googlecloudsdk.api_lib.recommender import flag_utils


def CreateClient(release_track):
  """Creates Client."""
  api_version = flag_utils.GetApiVersion(release_track)
  return Insight(api_version)


class Insight(base.ClientBase):
  """Base Insight client for all versions."""

  def __init__(self, api_version):
    super(Insight, self).__init__(api_version)
    self._service = self._client.projects_locations_insightTypes_insights

  def _CreateMarkRequest(self, name, state, state_metadata, etag):
    """Creates MarkRequest with the specified state."""
    # Need to do it this way to dynamically set the versioned MarkRequest
    request_name = 'MarkInsight{}Request'.format(state)
    mark_request = self._GetVersionedMessage(request_name)(etag=etag)

    if state_metadata:
      metadata = encoding.DictToAdditionalPropertyMessage(
          state_metadata,
          self._GetVersionedMessage(request_name).StateMetadataValue,
          sort_items=True)
      mark_request.stateMetadata = metadata

    # Need to do it this way to dynamically set the versioned MarkRequest
    kwargs = {
        'name':
            name,
        flag_utils.ToCamelCase(self._message_prefix + request_name):
            mark_request
    }

    # Using Project message is ok for all entities if the name is correct.
    return self._GetMessage(
        'RecommenderProjectsLocationsInsightTypesInsightsMark{}Request'.format(
            state))(**kwargs)

  def Get(self, name):
    """Gets an Insight.

    Args:
      name: str, the name of the insight being retrieved.

    Returns:
      The Insight message.
    """
    # Using Project message is ok for all entities if the name is correct.
    request = self._messages.RecommenderProjectsLocationsInsightTypesInsightsGetRequest(
        name=name)
    return self._service.Get(request)

  def List(self, parent_name, page_size, limit=None, request_filter=None):
    """List Insights.

    Args:
      parent_name: str, the name of the parent.
      page_size: int, The number of items to retrieve per request.
      limit: int, The maximum number of records to yield.
      request_filter: str, Optional request filter

    Returns:
      The Insight messages.
    """
    # Using Project message is ok for all entities if the name is correct.
    request = self._messages.RecommenderProjectsLocationsInsightTypesInsightsListRequest(
        parent=parent_name, filter=request_filter
    )
    return list_pager.YieldFromList(
        self._service,
        request,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        limit=limit,
        field='insights')

  def MarkAccepted(self, name, state_metadata, etag):
    """Mark an insight's state as ACCEPTED.

    Args:
      name: str, the name of the insight being updated.
      state_metadata: A map of metadata for the state, provided by user or
        automations systems.
      etag: Fingerprint of the Insight. Provides optimistic locking when
        updating states.

    Returns:
      The result insights after being marked as accepted
    """
    request = self._CreateMarkRequest(name, 'Accepted', state_metadata, etag)
    return self._service.MarkAccepted(request)

  def MarkActive(self, name, etag):
    """Mark an insight's state as ACTIVE.

    Args:
      name: str, the name of the insight being updated.
      etag: Fingerprint of the Insight. Provides optimistic locking when
        updating states.

    Returns:
      The result insights after being marked as active
    """
    request = self._CreateMarkRequest(name, 'Active', None, etag)
    return self._service.MarkActive(request)

  def MarkDismissed(self, name, etag):
    """Mark an insight's state as DISMISSED.

    Args:
      name: str, the name of the insight being updated.
      etag: Fingerprint of the Insight. Provides optimistic locking when
        updating states.

    Returns:
      The result insights after being marked as dismissed
    """
    request = self._CreateMarkRequest(name, 'Dismissed', None, etag)
    return self._service.MarkDismissed(request)
