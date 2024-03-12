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
"""Utilities for calling the Composer API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools
from apitools.base.py import encoding
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
import six

COMPOSER_API_NAME = 'composer'
COMPOSER_GA_API_VERSION = 'v1'
COMPOSER_BETA_API_VERSION = 'v1beta1'
COMPOSER_ALPHA_API_VERSION = 'v1alpha2'

DEFAULT_PAGE_SIZE = 30


def GetApiVersion(release_track=base.ReleaseTrack.GA):
  if release_track == base.ReleaseTrack.BETA:
    return COMPOSER_BETA_API_VERSION
  elif release_track == base.ReleaseTrack.ALPHA:
    return COMPOSER_ALPHA_API_VERSION
  return COMPOSER_GA_API_VERSION


def GetClientInstance(release_track=base.ReleaseTrack.GA):
  return apis.GetClientInstance(
      COMPOSER_API_NAME, GetApiVersion(release_track=release_track))


def GetMessagesModule(release_track=base.ReleaseTrack.GA):
  return apis.GetMessagesModule(
      COMPOSER_API_NAME, GetApiVersion(release_track=release_track))


def AggregateListResults(request_cls,
                         service,
                         location_refs,
                         field,
                         page_size,
                         limit=None,
                         location_attribute='parent'):
  """Collects the results of a List API call across a list of locations.

  Args:
    request_cls: class, the apitools.base.protorpclite.messages.Message class
        corresponding to the API request message used to list resources in a
        location.
    service: apitools.base.py.BaseApiService, a service whose list
        method to call with an instance of `request_cls`
    location_refs: [core.resources.Resource], a list of resource references to
        locations in which to list resources.
    field: str, the name of the field within the list method's response from
        which to extract a list of resources
    page_size: int, the maximum number of resources to retrieve in each API
        call
    limit: int, the maximum number of results to return. None if all available
        results should be returned.
    location_attribute: str, the name of the attribute in `request_cls` that
        should be populated with the name of the location

  Returns:
    A generator over up to `limit` resources if `limit` is not None. If `limit`
    is None, the generator will yield all resources in all requested locations.
  """
  results = []
  for location_ref in location_refs:
    request = request_cls()
    setattr(request, location_attribute, location_ref.RelativeName())
    results = itertools.chain(
        results,
        list_pager.YieldFromList(
            service,
            request=request,
            field=field,
            limit=None if limit is None else limit,
            batch_size=DEFAULT_PAGE_SIZE if page_size is None else page_size,
            batch_size_attribute='pageSize'))
  return itertools.islice(results, limit)


def ParseOperationJsonMetadata(metadata_value, metadata_type):
  if not metadata_value:
    return metadata_type()
  return encoding.JsonToMessage(metadata_type,
                                encoding.MessageToJson(metadata_value))


def DictToMessage(dictionary, msg_type):
  return msg_type(additionalProperties=[
      msg_type.AdditionalProperty(key=key, value=value)
      for key, value in six.iteritems(dictionary)
  ])
