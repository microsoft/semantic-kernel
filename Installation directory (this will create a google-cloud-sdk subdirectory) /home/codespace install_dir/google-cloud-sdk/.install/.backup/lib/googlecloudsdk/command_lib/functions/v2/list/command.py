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
"""This file provides the implementation of the `functions list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _YieldFromLocations(
    locations, project, limit, messages, client, filter_exp
):
  """Yield the functions from the given locations.

  Args:
    locations: List[str], list of gcp regions.
    project: str, Name of the API to modify. E.g. "cloudfunctions"
    limit: int, List messages limit.
    messages: module, Generated messages module.
    client: base_api.BaseApiClient, cloud functions client library.
    filter_exp: Filter expression in list functions request.

  Yields:
    protorpc.message.Message, The resources listed by the service.
  """

  def _ReadAttrAndLogUnreachable(message, attribute):
    if message.unreachable:
      log.warning(
          (
              'The following regions were fully or partially unreachable '
              'for query: %s\n'
              'This could be due to permission setup. Additional information'
              'can be found in: '
              'https://cloud.google.com/functions/docs/troubleshooting'
          ),
          ', '.join(message.unreachable),
      )
    return getattr(message, attribute)

  for location in locations:
    location_ref = resources.REGISTRY.Parse(
        location,
        params={'projectsId': project},
        collection='cloudfunctions.projects.locations',
    )
    for function in list_pager.YieldFromList(
        service=client.projects_locations_functions,
        request=messages.CloudfunctionsProjectsLocationsFunctionsListRequest(
            parent=location_ref.RelativeName(), filter=filter_exp
        ),
        limit=limit,
        field='functions',
        batch_size_attribute='pageSize',
        get_field_func=_ReadAttrAndLogUnreachable,
    ):
      yield function


def Run(args, release_track, filter_exp=None):
  """List Google Cloud Functions."""
  client = api_util.GetClientInstance(release_track=release_track)
  messages = api_util.GetMessagesModule(release_track=release_track)
  project = properties.VALUES.core.project.GetOrFail()
  limit = args.limit

  return _YieldFromLocations(
      args.regions, project, limit, messages, client, filter_exp
  )
