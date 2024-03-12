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
"""Useful commands for interacting with the Cloud Firestore Locations API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.firestore import api_utils


def _GetLocationService():
  """Returns the Firestore Location service for interacting with the Firestore Location service."""
  return api_utils.GetClient().projects_locations


def ListLocations(project):
  """Lists locations available to Google Cloud Firestore.

  Args:
    project: the project id to list locations, a string.

  Returns:
    a List of Locations.
  """
  return list_pager.YieldFromList(
      _GetLocationService(),
      api_utils.GetMessages().FirestoreProjectsLocationsListRequest(
          name='projects/{}'.format(project)
      ),
      field='locations',
      batch_size_attribute='pageSize',
  )


def GetLocation(project, location):
  """Gets a location information for Google Cloud Firestore.

  Args:
    project: the project id to get the location information, a string.
    location: the location id to get the location information, a string.

  Returns:
    a Firestore Location.
  """
  return _GetLocationService().Get(
      api_utils.GetMessages().FirestoreProjectsLocationsGetRequest(
          name='projects/{}/locations/{}'.format(project, location)
      )
  )
