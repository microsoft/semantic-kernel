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
"""Utilities for the Tag Manager server."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

TAGS_API_VERSION = 'v3'


def TagClient():
  """Returns a client instance of the CRM Tags service."""
  return apis.GetClientInstance('cloudresourcemanager', TAGS_API_VERSION)


def TagMessages():
  """Returns the messages module for the Tags service."""
  return apis.GetMessagesModule('cloudresourcemanager', TAGS_API_VERSION)


def TagKeysService():
  """Returns the tag keys service class."""
  client = TagClient()
  return client.tagKeys


def TagValuesService():
  """Returns the tag values service class."""
  client = TagClient()
  return client.tagValues


def TagBindingsService():
  """Returns the tag bindings service class."""
  client = TagClient()
  return client.tagBindings


def EffectiveTagsService():
  """Returns the effective tags service class."""
  client = TagClient()
  return client.effectiveTags


def TagHoldsService():
  """Returns the tag holds service class."""
  client = TagClient()
  return client.tagValues_tagHolds


def OperationsService():
  """Returns the operations service class."""
  client = TagClient()
  return client.operations
