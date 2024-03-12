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
  """Open the specified service(s) in a browser.

  """

  detailed_help = {
      'EXAMPLES': """\
          To show the url for the default service in the browser, run:

              $ {command} default

          To show version `v1` of service `myService` in the browser, run:

              $ {command} myService --version="v1"

          To show multiple services side-by-side, run:

              $ {command} default otherService

          To show multiple services side-by-side with a specific version, run:

              $ {command} s1 s2 --version=v1
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
          table(
            service:label=SERVICE,
            url:label=URL
          )
    """)
    flags.LAUNCH_BROWSER.AddToParser(parser)
    parser.add_argument(
        'services',
        nargs='+',
        help="""\
        The services to open (optionally filtered by the --version flag).""")
    parser.add_argument(
        '--version',
        '-v',
        help="""\
            If specified, open services with a given version. If not
            specified, use a version based on the service's traffic split .
            """)

  def Run(self, args):
    """Launch a browser, or return a table of URLs to print."""
    project = properties.VALUES.core.project.Get(required=True)
    outputs = []
    for service in args.services:
      outputs.append(browser_dispatcher.BrowseApp(project,
                                                  service,
                                                  args.version,
                                                  args.launch_browser))
    if any(outputs):
      if args.launch_browser:
        # We couldn't find a browser to launch
        log.status.Print(
            'Did not detect your browser. Go to these links to view your app:')
      return outputs
    return None
