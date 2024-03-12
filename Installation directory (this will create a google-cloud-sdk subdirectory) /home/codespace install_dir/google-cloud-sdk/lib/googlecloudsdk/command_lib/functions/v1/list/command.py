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

from apitools.base.py import exceptions as api_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.functions.v1 import util
from googlecloudsdk.calliope import exceptions as base_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _GetFunctionsAndLogUnreachable(message, attribute):
  """Response callback to log unreachable while generating functions."""
  if message.unreachable:
    log.warning(
        'The following regions were fully or partially unreachable '
        'for query: %s'
        'This could be due to permission setup. Additional information'
        'can be found in: '
        'https://cloud.google.com/functions/docs/troubleshooting'
        % ', '.join(message.unreachable)
    )
  return getattr(message, attribute)


def YieldFromLocations(locations, project, limit, messages, client):
  """Yield the functions from the given locations."""
  for location in locations:
    location_ref = resources.REGISTRY.Parse(
        location,
        params={'projectsId': project},
        collection='cloudfunctions.projects.locations',
    )
    for function in _YieldFromLocation(location_ref, limit, messages, client):
      yield function


def _YieldFromLocation(location_ref, limit, messages, client):
  """Yield the functions from the given location."""
  list_generator = list_pager.YieldFromList(
      service=client.projects_locations_functions,
      request=_BuildRequest(location_ref, messages),
      limit=limit,
      field='functions',
      batch_size_attribute='pageSize',
      get_field_func=_GetFunctionsAndLogUnreachable,
  )

  # Decorators (e.g. util.CatchHTTPErrorRaiseHTTPException) don't work
  # for generators. We have to catch the exception above the iteration loop,
  # but inside the function.
  try:
    for item in list_generator:
      yield item
  except api_exceptions.HttpError as error:
    msg = util.GetHttpErrorMessage(error)
    exceptions.reraise(base_exceptions.HttpException(msg))


def _BuildRequest(location_ref, messages):
  return messages.CloudfunctionsProjectsLocationsFunctionsListRequest(
      parent=location_ref.RelativeName()
  )


def Run(args):
  """List Google Cloud Functions."""
  client = util.GetApiClientInstance()
  messages = util.GetApiMessagesModule()
  project = properties.VALUES.core.project.GetOrFail()
  limit = args.limit

  return YieldFromLocations(args.regions, project, limit, messages, client)
