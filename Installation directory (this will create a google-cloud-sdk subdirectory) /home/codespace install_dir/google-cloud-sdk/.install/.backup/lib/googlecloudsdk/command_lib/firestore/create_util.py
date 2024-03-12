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
"""Utilities for database creation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class AppEngineAppDoesNotExist(apitools_exceptions.Error):
  """An App Engine app must be created first."""


class AppEngineAppRegionDoesNotMatch(apitools_exceptions.Error):
  """An App Engine app must have a matching region."""


class RegionNotSpecified(apitools_exceptions.Error):
  """Must specify a region to use this command."""


def create(region, product_name, enum_value):
  """Helper for implementing Firestore database create comamnds.

  Guides the user through the gcloud app creation process and then updates the
  database type to the requested type.

  Args:
    region: The region of Firestore database.
    product_name: The product name of the database trying to be created.
    enum_value: Enum value representing the product name in the API.

  Raises:
    AppEngineAppDoesNotExist: If no app has been created.
    AppEngineAppRegionDoesNotMatch: If app created but region doesn't match the
     --region flag.
    RegionNotSpecified: User didn't specify --region.
  """
  api_client = appengine_api_client.GetApiClientForTrack(base.ReleaseTrack.GA)

  app = None
  try:
    app = api_client.GetApplication()
  except apitools_exceptions.HttpNotFoundError:
    if region is None:
      raise AppEngineAppDoesNotExist(
          'You must first create a Google App Engine app by running:\n'
          'gcloud app create\n'
          'The region you create the App Engine app in is '
          'the same region that the Firestore database will be created in. '
          'Once an App Engine region has been chosen it cannot be changed.')
    else:
      raise AppEngineAppDoesNotExist(
          'You must first create an Google App Engine app in the '
          'corresponding region by running:\n'
          'gcloud app create --region={region}'.format(region=region))

  current_region = app.locationId

  if not region:
    raise RegionNotSpecified(
        'You must specify a region using the --region flag to use this '
        'command. The region needs to match the Google App Engine region: '
        '--region={current_region}'.format(current_region=current_region))

  if current_region != region:
    raise AppEngineAppRegionDoesNotMatch(
        'The app engine region is {current_region} which is not the same as '
        '{region}. Right now the Firestore region must match the App Engine '
        'region.\n'
        'Try running this command with --region={current_region}'.format(
            current_region=current_region, region=region))
  project = properties.VALUES.core.project.Get(required=True)
  # Set the DB Type to the desired type (if needed)
  if app.databaseType != enum_value:
    api_client.UpdateDatabaseType(enum_value)
  else:
    log.status.Print(
        'Success! Confirmed selection of a {product_name} database for {project}'
        .format(product_name=product_name, project=project))
    return

  log.status.Print(
      'Success! Selected {product_name} database for {project}'.format(
          product_name=product_name, project=project))
