# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Utilities for app creation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


APP_CREATE_WARNING = """\
Creating an App Engine application for a project is irreversible and the region
cannot be changed. More information about regions is at
<https://cloud.google.com/appengine/docs/locations>.
"""


class UnspecifiedRegionError(exceptions.Error):
  """Region is not provided on the command line and running interactively."""


class AppAlreadyExistsError(exceptions.Error):
  """The app which is getting created already exists."""


def CheckAppNotExists(api_client, project):
  """Raises an error if the app already exists.

  Args:
    api_client: The App Engine Admin API client
    project: The GCP project

  Raises:
    AppAlreadyExistsError if app already exists
  """
  try:
    app = api_client.GetApplication()  # Should raise NotFoundError
  except apitools_exceptions.HttpNotFoundError:
    pass
  else:
    region = ' in region [{}]'.format(app.locationId) if app.locationId else ''
    raise AppAlreadyExistsError(
        'The project [{project}] already contains an App Engine '
        'application{region}.  You can deploy your application using '
        '`gcloud app deploy`.'.format(project=project, region=region))


def CreateApp(api_client,
              project,
              region,
              suppress_warning=False,
              service_account=None):
  """Create an App Engine app in the given region.

  Prints info about the app being created and displays a progress tracker.

  Args:
    api_client: The App Engine Admin API client
    project: The GCP project
    region: The region to create the app
    suppress_warning: True if user doesn't need to be warned this is
        irreversible.
    service_account: The app level service account for the App Engine app.

  Raises:
    AppAlreadyExistsError if app already exists
  """
  if not suppress_warning:
    log.status.Print('You are creating an app for project [{project}].'.format(
        project=project))
    if service_account:
      log.status.Print(
          'Designating app-level default service account to be [{service_account}].'
          .format(service_account=service_account))
    log.warning(APP_CREATE_WARNING)
  try:
    api_client.CreateApp(region, service_account=service_account)
  except apitools_exceptions.HttpConflictError:
    raise AppAlreadyExistsError(
        'The project [{project}] already contains an App Engine application. '
        'You can deploy your application using `gcloud app deploy`.'.format(
            project=project))


def CreateAppInteractively(api_client,
                           project,
                           regions=None,
                           extra_warning='',
                           service_account=None):
  """Interactively choose a region and create an App Engine app.

  The caller is responsible for calling this method only when the user can be
  prompted interactively.

  Example interaction:

      Please choose the region where you want your App Engine application
      located:

        [1] us-east1      (supports standard and flexible)
        [2] europe-west   (supports standard)
        [3] us-central    (supports standard and flexible)
        [4] cancel
      Please enter your numeric choice:  1

  Args:
    api_client: The App Engine Admin API client
    project: The GCP project
    regions: The list of regions to choose from; if None, all possible regions
             are listed
    extra_warning: An additional warning to print before listing regions.
    service_account: The app level service account for the App Engine app.

  Raises:
    AppAlreadyExistsError if app already exists
  """
  log.status.Print('You are creating an app for project [{}].'.format(project))
  log.warning(APP_CREATE_WARNING)

  regions = regions or sorted(set(api_client.ListRegions()), key=str)
  if extra_warning:
    log.warning(extra_warning)
  idx = console_io.PromptChoice(
      regions,
      message=('Please choose the region where you want your App Engine '
               'application located:\n\n'),
      cancel_option=True)
  region = regions[idx]
  CreateApp(
      api_client,
      project,
      region.region,
      suppress_warning=True,
      service_account=service_account)
