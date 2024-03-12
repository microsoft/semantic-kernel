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

"""A module for diagnosing common network and proxy problems."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import socket
import ssl

from googlecloudsdk.core import config
from googlecloudsdk.core import http
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests as core_requests
from googlecloudsdk.core.diagnostics import check_base
from googlecloudsdk.core.diagnostics import diagnostic_base
from googlecloudsdk.core.diagnostics import http_proxy_setup

import httplib2
import requests
from six.moves import http_client
from six.moves import urllib
import socks

_NETWORK_TIMEOUT = 60  # Timeout in seconds when testing GET requests


class NetworkDiagnostic(diagnostic_base.Diagnostic):
  """Diagnose and fix local network connection issues."""

  def __init__(self):
    intro = ('Network diagnostic detects and fixes local network connection '
             'issues.')
    super(NetworkDiagnostic, self).__init__(
        intro=intro, title='Network diagnostic',
        checklist=[ReachabilityChecker()])


def DefaultUrls():
  """Returns a list of hosts whose reachability is essential for the Cloud SDK.

  Returns:
    A list of urls (str) to check reachability for.
  """
  urls = ['https://accounts.google.com',
          'https://cloudresourcemanager.googleapis.com/v1beta1/projects',
          'https://www.googleapis.com/auth/cloud-platform']

  download_urls = (properties.VALUES.component_manager.snapshot_url.Get() or
                   config.INSTALLATION_CONFIG.snapshot_url)
  urls.extend(u for u in download_urls.split(',')
              if urllib.parse.urlparse(u).scheme in ('http', 'https'))
  return urls


class ReachabilityChecker(check_base.Checker):
  """Checks whether the hosts of given urls are reachable."""

  @property
  def issue(self):
    return 'network connection'

  def Check(self, urls=None, first_run=True):
    """Run reachability check.

    Args:
      urls: iterable(str), The list of urls to check connection to. Defaults to
        DefaultUrls() (above) if not supplied.
      first_run: bool, True if first time this has been run this invocation.

    Returns:
      A tuple of (check_base.Result, fixer) where fixer is a function that can
        be used to fix a failed check, or  None if the check passed or failed
        with no applicable fix.
    """
    if urls is None:
      urls = DefaultUrls()

    failures = []
    # Check reachability using httplib2
    for url in urls:
      fail = CheckURLHttplib2(url)
      if fail:
        failures.append(fail)

    # Check reachability using requests
    for url in urls:
      fail = CheckURLRequests(url)
      if fail:
        failures.append(fail)

    if failures:
      fail_message = ConstructMessageFromFailures(failures, first_run)
      result = check_base.Result(passed=False, message=fail_message,
                                 failures=failures)
      fixer = http_proxy_setup.ChangeGcloudProxySettings
      return result, fixer

    pass_message = 'Reachability Check {0}.'.format('passed' if first_run else
                                                    'now passes')
    result = check_base.Result(passed=True, message='No URLs to check.'
                               if not urls else pass_message)
    return result, None


def CheckURLHttplib2(url):
  try:
    http.Http(timeout=_NETWORK_TIMEOUT).request(url, method='GET')
  except (http_client.HTTPException, socket.error, ssl.SSLError,
          httplib2.HttpLib2Error, socks.HTTPError) as err:
    msg = 'httplib2 cannot reach {0}:\n{1}\n'.format(
        url, err)
    return check_base.Failure(message=msg, exception=err)


def CheckURLRequests(url):
  try:
    core_requests.GetSession(timeout=_NETWORK_TIMEOUT).request('GET', url)
  except requests.exceptions.RequestException as err:
    msg = 'requests cannot reach {0}:\n{1}\n'.format(
        url, err)
    return check_base.Failure(message=msg, exception=err)


def ConstructMessageFromFailures(failures, first_run):
  """Constructs error messages along with diagnostic information."""
  message = 'Reachability Check {0}.\n'.format('failed' if first_run else
                                               'still does not pass')
  for failure in failures:
    message += '    {0}\n'.format(failure.message)
  if first_run:
    message += ('Network connection problems may be due to proxy or '
                'firewall settings.\n')

  return message
