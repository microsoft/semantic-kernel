# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Utilities for the container analysis commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from six.moves import range

# The maximum number of resource URLs by which to filter when showing
# occurrences. This is required since filtering by too many causes the
# API request to be too large. Instead, the requests are chunkified.
_MAXIMUM_RESOURCE_URL_CHUNK_SIZE = 5


def MakeOccurrenceRequest(
    project_id, resource_filter, occurrence_filter=None, resource_urls=None):
  """Helper function to make Fetch Occurrence Request."""
  client = apis.GetClientInstance('containeranalysis', 'v1alpha1')
  messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
  base_filter = resource_filter
  if occurrence_filter:
    base_filter = (
        '({occurrence_filter}) AND ({base_filter})'.format(
            occurrence_filter=occurrence_filter,
            base_filter=base_filter))
  project_ref = resources.REGISTRY.Parse(
      project_id, collection='cloudresourcemanager.projects')

  if not resource_urls:
    # When there are no resource_urls to filter don't need to do chunkifying
    # logic or add anything to the base filter.
    return list_pager.YieldFromList(
        client.projects_occurrences,
        request=messages.ContaineranalysisProjectsOccurrencesListRequest(
            parent=project_ref.RelativeName(), filter=base_filter),
        field='occurrences',
        batch_size=1000,
        batch_size_attribute='pageSize')

  # Occurrences are filtered by resource URLs. If there are more than roughly
  # _MAXIMUM_RESOURCE_URL_CHUNK_SIZE resource urls in the API request, the
  # request becomes too big and will be rejected. This block chunkifies the
  # resource URLs list and issues multiple API requests to circumvent this
  # limit. The resulting generators (from YieldFromList) are chained together in
  # the final output.
  occurrence_generators = []
  for index in range(0, len(resource_urls), _MAXIMUM_RESOURCE_URL_CHUNK_SIZE):
    chunk = resource_urls[index : (index + _MAXIMUM_RESOURCE_URL_CHUNK_SIZE)]
    url_filter = '%s AND (%s)' % (
        base_filter,
        ' OR '.join(['resource_url="%s"' % url for url in chunk]))
    occurrence_generators.append(
        list_pager.YieldFromList(
            client.projects_occurrences,
            request=messages.ContaineranalysisProjectsOccurrencesListRequest(
                parent=project_ref.RelativeName(), filter=url_filter),
            field='occurrences',
            batch_size=1000,
            batch_size_attribute='pageSize'))
  return itertools.chain(*occurrence_generators)


def _GetNoteRef(note_name, default_project):
  try:
    return resources.REGISTRY.ParseRelativeName(
        note_name, 'containeranalysis.providers.notes')
  except resources.InvalidResourceException:
    # Not a relative name, try to pase as URL or name + project.
    return resources.REGISTRY.Parse(
        note_name,
        params={'providersId': default_project},
        collection='containeranalysis.providers.notes')


def MakeGetNoteRequest(note_name, default_project):
  client = apis.GetClientInstance('containeranalysis', 'v1alpha1')
  messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
  note_ref = _GetNoteRef(note_name, default_project)
  request = messages.ContaineranalysisProvidersNotesGetRequest(
      name=note_ref.RelativeName(),
  )
  return client.providers_notes.Get(request)
