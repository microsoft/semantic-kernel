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

"""The Browse command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import browser_dispatcher
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Browse(base.Command):
  """Open the specified versions in a browser."""

  detailed_help = {
      'EXAMPLES': """\
          To show version `v1` for the default service in the browser, run:

              $ {command} v1

          To show version `v1` of a specific service in the browser, run:

              $ {command} v1 --service="myService"

          To show multiple versions side-by-side, run:

              $ {command} v1 v2 --service="myService"
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
          table(
            version:label=VERSION,
            url:label=URL
          )
    """)
    flags.LAUNCH_BROWSER.AddToParser(parser)
    parser.add_argument(
        'versions',
        nargs='+',
        help="""\
        The versions to open (optionally filtered by the --service flag).""")
    parser.add_argument('--service', '-s',
                        help=('If specified, only open versions from the '
                              'given service. If not specified, use the '
                              'default service.'))

  def Run(self, args):
    """Launch a browser, or return a table of URLs to print."""
    project = properties.VALUES.core.project.Get(required=True)
    outputs = []
    for version in args.versions:
      outputs.append(browser_dispatcher.BrowseApp(project,
                                                  args.service,
                                                  version,
                                                  args.launch_browser))
    if any(outputs):
      if args.launch_browser:
        # We couldn't find a browser to launch
        log.status.Print(
            'Did not detect your browser. Go to these links to view your app:')
      return outputs
    return None
