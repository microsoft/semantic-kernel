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
"""Utilities for Recommendation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
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
  return Recommendation(api_version)


class Recommendation(base.ClientBase):
  """Base Recommendation client for all versions."""

  def __init__(self, api_version):
    super(Recommendation, self).__init__(api_version)
    self._service = self._client.projects_locations_recommenders_recommendations

  def _CreateMarkRequest(self, name, state, state_metadata, etag):
    """Creates MarkRequest with the specified state."""
    # Need to do it this way to dynamically set the versioned MarkRequest
    request_name = 'MarkRecommendation{}Request'.format(state)
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
        'RecommenderProjectsLocationsRecommendersRecommendationsMark{}Request'
        .format(state))(**kwargs)

  def Get(self, name):
    """Gets a Recommendation.

    Args:
      name: str, the name of the recommendation being retrieved.

    Returns:
      The Recommendation message.
    """
    # Using Project message is ok for all entities if the name is correct.
    request = self._messages.RecommenderProjectsLocationsRecommendersRecommendationsGetRequest(
        name=name)
    return self._service.Get(request)

  def List(self, parent_name, page_size, limit=None):
    """List Recommendations.

    Args:
      parent_name: str, the name of the parent.
      page_size: int, The number of items to retrieve per request.
      limit: int, The maximum number of records to yield.

    Returns:
      The Recommendation messages.
    """
    # Using Project message is ok for all entities if the name is correct.
    request = self._messages.RecommenderProjectsLocationsRecommendersRecommendationsListRequest(
        parent=parent_name)
    return list_pager.YieldFromList(
        self._service,
        request,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        limit=limit,
        field='recommendations')

  def MarkActive(self, name, etag):
    """Mark a recommendation's state as ACTIVE.

    Args:
      name: str, the name of the recommendation being updated.
      etag: Fingerprint of the Recommendation. Provides optimistic locking when
        updating states.

    Returns:
      The result recommendations after being marked as active
    """
    request = self._CreateMarkRequest(name, 'Active', None, etag)
    return self._service.MarkActive(request)

  def MarkDismissed(self, name, etag):
    """Mark a recommendation's state as DISMISSED.

    Args:
      name: str, the name of the recommendation being updated.
      etag: Fingerprint of the Recommendation. Provides optimistic locking when
        updating states.

    Returns:
      The result recommendations after being marked as dismissed
    """
    request = self._CreateMarkRequest(name, 'Dismissed', None, etag)
    return self._service.MarkDismissed(request)

  def MarkClaimed(self, name, state_metadata, etag):
    """Mark a recommendation's state as CLAIMED.

    Args:
      name: str, the name of the recommendation being updated.
      state_metadata: A map of metadata for the state, provided by user or
        automations systems.
      etag: Fingerprint of the Recommendation. Provides optimistic locking when
        updating states.

    Returns:
      The result recommendations after being marked as accepted
    """
    request = self._CreateMarkRequest(name, 'Claimed', state_metadata, etag)
    return self._service.MarkClaimed(request)

  def MarkSucceeded(self, name, state_metadata, etag):
    """Mark a recommendation's state as SUCCEEDED.

    Args:
      name: str, the name of the recommendation being updated.
      state_metadata: A map of metadata for the state, provided by user or
        automations systems.
      etag: Fingerprint of the Recommendation. Provides optimistic locking when
        updating states.

    Returns:
      The result recommendations after being marked as accepted
    """
    request = self._CreateMarkRequest(name, 'Succeeded', state_metadata, etag)
    return self._service.MarkSucceeded(request)

  def MarkFailed(self, name, state_metadata, etag):
    """Mark a recommendation's state as FAILED.

    Args:
      name: str, the name of the recommendation being updated.
      state_metadata: A map of metadata for the state, provided by user or
        automations systems.
      etag: Fingerprint of the Recommendation. Provides optimistic locking when
        updating states.

    Returns:
      The result recommendations after being marked as accepted
    """
    request = self._CreateMarkRequest(name, 'Failed', state_metadata, etag)
    return self._service.MarkFailed(request)
