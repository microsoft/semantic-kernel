# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Utilities for Cloud Datastore datastore management commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

_DATASTORE_API_VERSION = 'v1'


def GetMessages():
  """Import and return the appropriate admin messages module."""
  return apis.GetMessagesModule('datastore', _DATASTORE_API_VERSION)


def GetClient():
  """Returns the Cloud Datastore client for the appropriate release track."""
  return apis.GetClientInstance('datastore', _DATASTORE_API_VERSION)


def GetService():
  """Returns the service for interacting with the Datastore Admin service.

  This is used for import/export Datastore indexes.
  """
  return GetClient().projects
