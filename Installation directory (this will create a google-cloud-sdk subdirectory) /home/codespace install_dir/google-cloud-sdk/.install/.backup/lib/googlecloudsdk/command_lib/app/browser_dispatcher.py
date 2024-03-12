# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Tools for opening URL:s related to the app in the browser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.app import deploy_command_util
from googlecloudsdk.command_lib.app import exceptions
from googlecloudsdk.command_lib.util import check_browser
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import devshell
from googlecloudsdk.third_party.appengine.api import appinfo


def OpenURL(url):
  """Open a URL in the default web browser in a new tab.

  Args:
    url: The full HTTP(S) URL to open.
  """
  # Import in here for performance reasons
  # pylint: disable=g-import-not-at-top
  import webbrowser
  # Devshell has its own 'browser' handler which simply prints the URL; this is
  # redundant
  if not devshell.IsDevshellEnvironment():
    log.status.Print(
        'Opening [{0}] in a new tab in your default browser.'.format(url))
  webbrowser.open_new_tab(url)


def BrowseApp(project, service, version, launch_browser):
  """Let you browse the given service at the given version.

  Args:
    project: str, project ID.
    service: str, specific service, 'default' if None
    version: str, specific version, latest if None
    launch_browser: boolean, if False only print url

  Returns:
    None if the browser should open the URL
    The relevant output as a dict for calliope format to print if not

  Raises:
    MissingApplicationError: If an app does not exist.
  """
  try:
    url = deploy_command_util.GetAppHostname(
        app_id=project, service=service, version=version,
        use_ssl=appinfo.SECURE_HTTPS, deploy=False)
  except apitools_exceptions.HttpNotFoundError:
    log.debug('No app found:', exc_info=True)
    raise exceptions.MissingApplicationError(project)
  if check_browser.ShouldLaunchBrowser(launch_browser):
    OpenURL(url)
    return None
  else:
    return {
        'url': url,
        'service': service or 'default',
        'version': version,
    }
