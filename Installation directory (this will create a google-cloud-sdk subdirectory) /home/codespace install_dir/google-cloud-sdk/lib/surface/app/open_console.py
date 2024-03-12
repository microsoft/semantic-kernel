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
"""The Open Console command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import browser_dispatcher
from googlecloudsdk.core import properties
from six.moves import urllib


CONSOLE_URL = 'https://console.developers.google.com/appengine?{query}'
LOGS_URL = 'https://console.developers.google.com/logs?{query}'


def _CreateDevConsoleURL(project, service='default', version=None, logs=False):
  """Creates a URL to a page in the Developer Console according to the params.

  Args:
    project: The app engine project id
    service: A service belonging to the project
    version: A version belonging to the service, or all versions if omitted
    logs: If true, go to the log section instead of the dashboard
  Returns:
    The URL to the respective page in the Developer Console
  """
  if service is None:
    service = 'default'
  query = [('project', project), ('serviceId', service)]
  if version:
    query.append(('versionId', version))
  query_string = urllib.parse.urlencode(query)
  return (LOGS_URL if logs else CONSOLE_URL).format(query=query_string)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class OpenConsole(base.Command):
  """Open the App Engine dashboard, or log viewer, in a web browser.

  """

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          Open the App Engine dashboard for the default service:

              $ {command}

          Open the service specific dashboard view:

              $ {command} --service="myService"

          Open the version specific dashboard view:

              $ {command} --service="myService" --version="v1"

          Open the log viewer for the default service:

              $ {command} --logs
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--service',
        '-s',
        help=('The service to consider. If not specified, use the '
              'default service.'))
    parser.add_argument(
        '--version',
        '-v',
        help=('The version to consider. If not specified, '
              'all versions for the given service are considered.'))
    parser.add_argument(
        '--logs',
        '-l',
        action='store_true',
        default=False,
        help='Open the log viewer instead of the App Engine dashboard.')

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    url = _CreateDevConsoleURL(project, args.service, args.version, args.logs)
    browser_dispatcher.OpenURL(url)
