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
"""Utilities for the interactive gcloud debugger.

Contains things like:
  - Common imports pre-imported
  - Easy utility wrappers
  - Pre-initialized API clients

That make interactive debugging with gcloud a dream.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import code
# `site` initializes the interactive mode (defines `exit`/`quit`, sets up
# copyright notice, etc.).
import site  # pylint: disable=unused-import

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.generated_clients.apis import apis_map


################################################################################
# Consoles: Infrastructure for `gcloud meta debug`
################################################################################
_BANNER = r"""
                   _     _     _     _     _     _     _
                  / \   / \   / \   / \   / \   / \   / \
                 ( W ) ( E ) ( L ) ( C ) ( O ) ( M ) ( E )
                  \_/   \_/   \_/   \_/   \_/   \_/   \_/

                _____               ________)
               |_   _|___          (, /         /)      /)
                 | | | . |           /___, _   (/_     // ___    _
                 |_| |___|          /     (_(_/_) (_(_(/_(_)(_(_/_)_
                                 (_/
             _                 _       _      _
            | |               | |     | |    | |
   __ _  ___| | ___  _   _  __| |   __| | ___| |__  _   _  __ _  __ _  ___ _ __
  / _` |/ __| |/ _ \| | | |/ _` |  / _` |/ _ \ '_ \| | | |/ _` |/ _` |/ _ \ '__|
 | (_| | (__| | (_) | |_| | (_| | | (_| |  __/ |_) | |_| | (_| | (_| |  __/ |
  \__, |\___|_|\___/ \__,_|\__,_|  \__,_|\___|_.__/ \__,_|\__, |\__, |\___|_|
   __/ |                                                   __/ | __/ |
  |___/                                                   |___/ |___/
"""


def _PythonConsole():
  """Run a console based on the built-in code.InteractiveConsole."""
  try:
    # pylint: disable=g-import-not-at-top
    import readline
    import rlcompleter
    # pylint: disable=g-import-not-at-top
  except ImportError:
    pass
  else:
    readline.set_completer(rlcompleter.Completer(globals()).complete)
    readline.parse_and_bind('tab: complete')
  console = code.InteractiveConsole(globals())
  console.interact(_BANNER)


def _PdbConsole():
  """Run a console based on the built-in pdb."""
  import pdb  # pylint: disable=g-import-not-at-top
  pdb.set_trace()


def _IpdbConsole():
  """Run a console based on IPython's ipdb."""
  try:
    import ipdb  # pylint: disable=g-import-not-at-top
    ipdb.set_trace()
  except ImportError:
    log.error('Could not start the ipdb debugger. Please ensure that it is '
              'installed, or try the default debugger with `--mode=python`.')


def _PudbConsole():
  """Run a console based on PuDB."""
  try:
    import pudb  # pylint: disable=g-import-not-at-top
    pudb.set_trace()
  except ImportError:
    log.error('Could not start the PuDB debugger. Please ensure that it is '
              'installed, or try the default debugger with `--mode=python`.')


CONSOLES = {
    'python': _PythonConsole,
    'pdb': _PdbConsole,
    'ipdb': _IpdbConsole,
    'pudb': _PudbConsole,
}


################################################################################
# Common Cloud SDK imports
################################################################################
# pylint: disable=g-import-not-at-top
# pylint: disable=g-bad-import-order
from googlecloudsdk.core import log  # pylint: disable=unused-import
from googlecloudsdk.core import properties  # pylint: disable=unused-import
from googlecloudsdk.core.console import console_io  # pylint: disable=unused-import
from googlecloudsdk.core.util import files  # pylint: disable=unused-import
# pylint: enable=g-import-not-at-top
# pylint: enable=g-bad-import-order


################################################################################
# Pre-initialized API clients
################################################################################
def LoadApis():
  """Populate the global module namespace with API clients."""
  for api_name in apis_map.MAP:
    # pylint:disable=protected-access
    globals()[api_name] = apis.GetClientInstance(
        api_name, apis_internal._GetDefaultVersion(api_name))


def _PopulateApiNamesWithLoadMessage():
  """Make API names print instructions for loading the APIs when __repr__'ed.

  For example:

  >>> appengine
  Run `LoadApis()` to load all APIs, including this one.

  Load APIs it lazily because it takes about a second to load all APIs.
  """
  load_apis_message = (
      'Run `{0}()` to load all APIs, including this one.').format(
          LoadApis.__name__)

  class _LoadApisMessage(object):

    def __repr__(self):
      return load_apis_message

  for api_name in apis_map.MAP:
    globals()[api_name] = _LoadApisMessage()


_PopulateApiNamesWithLoadMessage()
