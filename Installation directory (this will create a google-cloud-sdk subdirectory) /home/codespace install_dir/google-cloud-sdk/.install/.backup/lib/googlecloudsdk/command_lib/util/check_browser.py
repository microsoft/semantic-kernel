# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Decide whether launching a browser is a good idea."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import platforms


# These are environment variables that can indicate a running compositor on
# Linux.
_DISPLAY_VARIABLES = ['DISPLAY', 'WAYLAND_DISPLAY', 'MIR_SOCKET']

# A list of results for webbrowser.get().name that indicate we should not
# attempt to open a web browser for the user.
_WEBBROWSER_NAMES_BLOCKLIST = [
    'www-browser',
]


def ShouldLaunchBrowser(attempt_launch_browser):
  """Determines if a browser can be launched.

  Args:
    attempt_launch_browser: bool, True to launch a browser if it's possible in
      the user's environment; False to not even try.

  Returns:
    True if the tool should actually launch a browser, based on user preference
    and environment.
  """
  import webbrowser  # pylint:disable=g-import-not-at-top, For performance.

  # Sometimes it's not possible to launch the web browser. This often
  # happens when people ssh into other machines.
  launch_browser = attempt_launch_browser
  if launch_browser:
    current_os = platforms.OperatingSystem.Current()
    if (current_os is platforms.OperatingSystem.LINUX and
        not any(encoding.GetEncodedValue(os.environ, var) for var
                in _DISPLAY_VARIABLES)):
      launch_browser = False
    try:
      browser = webbrowser.get()
      if (hasattr(browser, 'name')
          and browser.name in _WEBBROWSER_NAMES_BLOCKLIST):
        launch_browser = False
    except webbrowser.Error:
      launch_browser = False

  return launch_browser
