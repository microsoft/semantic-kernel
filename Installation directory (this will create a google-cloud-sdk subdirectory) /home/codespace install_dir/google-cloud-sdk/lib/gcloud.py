#!/usr/bin/env python
# -*- coding: utf-8 -*- #
#
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""gcloud command line tool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import os
import sys

_GCLOUD_PY_DIR = os.path.dirname(__file__)
_THIRD_PARTY_DIR = os.path.join(_GCLOUD_PY_DIR, 'third_party')

# From Python 3.11 onwards, the script directory is not prepended to sys.path by
# default if PYTHONSAFEPATH env var is set.
# NOMUTANTS--Tested through the installed SDK in e2e.bundle.sanity_test.
if _GCLOUD_PY_DIR not in sys.path:
  sys.path.insert(0, _GCLOUD_PY_DIR)

if os.path.isdir(_THIRD_PARTY_DIR):
  sys.path.insert(0, _THIRD_PARTY_DIR)


def _fix_google_module():
  """Reloads the google module to prefer our vendored copy.

  When python is not invoked with the -S option, it can preload google module
  via .pth file setting its __path__. After this happens, our vendored google
  package may not in the __path__. After our vendored dependency directory is
  put at the first place in the sys.path, google module should be reloaded,
  so that our vendored copy can be preferred.
  """
  if 'google' not in sys.modules:
    return
  import google  # pylint: disable=g-import-not-at-top
  try:
    reload(google)
  except NameError:
    import importlib  # pylint: disable=g-import-not-at-top
    importlib.reload(google)


def reorder_sys_path(sys_path):
  """If site packages are enabled reorder them.

  Make sure bundled_python site-packages appear first in the sys.path.

  Args:
    sys_path: list current sys path

  Returns:
    modified syspath if CLOUDSDK_PYTHON_SITEPACKAGES is on, prefer bundled
    python site packages over all other. Note the returns syspath has the same
    elements but a different order.
  """
  if 'CLOUDSDK_PYTHON_SITEPACKAGES' in os.environ:
    new_path = []
    other_site_packages = []
    for path in sys_path:
      if 'site-packages' in path and 'platform/bundledpythonunix' not in path:
        other_site_packages.append(path)
      else:
        new_path.append(path)
    new_path.extend(other_site_packages)
    return new_path
  else:
    return sys_path


def _import_gcloud_main():
  """Returns reference to gcloud_main module."""
  # pylint:disable=g-import-not-at-top
  import googlecloudsdk.gcloud_main
  return googlecloudsdk.gcloud_main


MIN_SUPPORTED_PY3_VERSION = (3, 8)
MAX_SUPPORTED_PY3_VERSION = (3, 12)


def python_version_string(python_version):
  return '{}.{}'.format(python_version[0], python_version[1])


@contextlib.contextmanager
def gcloud_exception_handler():
  """Handles exceptions from gcloud to provide a helpful message."""
  try:
    yield
  except Exception:  # pylint: disable=broad-except
    # We want to catch *everything* here to display a nice message to the user
    # pylint:disable=g-import-not-at-top
    python_version = sys.version_info[:2]
    if (python_version < MIN_SUPPORTED_PY3_VERSION or
        python_version > MAX_SUPPORTED_PY3_VERSION):
      valid_python_version = False
      if python_version > MAX_SUPPORTED_PY3_VERSION:
        support_message = 'not currently supported by gcloud'
      else:
        support_message = 'no longer supported by gcloud'
      error_message = (
          'You are running gcloud with Python {python_version}, which is '
          '{support_message}.\nInstall a compatible version of Python '
          '{min_python_version}-{max_python_version} and set the '
          'CLOUDSDK_PYTHON environment variable to point to it.'.format(
              python_version=python_version_string(python_version),
              support_message=support_message,
              min_python_version=python_version_string(
                  MIN_SUPPORTED_PY3_VERSION),
              max_python_version=python_version_string(
                  MAX_SUPPORTED_PY3_VERSION))
          )
    else:
      valid_python_version = True
      error_message = (
          'This usually indicates corruption in your gcloud installation or '
          'problems with your Python interpreter.\n\n'
          'Please verify that the following is the path to a working Python '
          '{min_python_version}-{max_python_version} executable:\n    '
          '{executable}\n\nIf it is not, please set the CLOUDSDK_PYTHON '
          'environment variable to point to a working Python '
          'executable.').format(
              executable=sys.executable,
              min_python_version=python_version_string(
                  MIN_SUPPORTED_PY3_VERSION),
              max_python_version=python_version_string(
                  MAX_SUPPORTED_PY3_VERSION))

    # We DON'T want to suggest `gcloud components reinstall` here (ex. as
    # opposed to the similar message in gcloud_main.py), as we know that no
    # commands will work.
    sys.stderr.write(
        (
            'ERROR: gcloud failed to load. {error_message}\n\n'
            'If you are still experiencing problems, please reinstall the '
            'Google Cloud CLI using the instructions here:\n    '
            'https://cloud.google.com/sdk/docs/install\n'
        ).format(error_message=error_message)
    )
    if valid_python_version:
      import traceback
      sys.stderr.write('\n\n{}\n'.format(
          '\n'.join(traceback.format_exc().splitlines())))
    sys.exit(1)


def main():
  with gcloud_exception_handler():
    sys.path = reorder_sys_path(sys.path)
    # pylint:disable=g-import-not-at-top
    from googlecloudsdk.core.util import encoding

  if encoding.GetEncodedValue(os.environ, '_ARGCOMPLETE'):
    try:
      # pylint:disable=g-import-not-at-top
      from googlecloudsdk.command_lib.static_completion import lookup
      lookup.Complete()
      return
    except Exception:  # pylint:disable=broad-except, hide completion errors
      if encoding.GetEncodedValue(os.environ,
                                  '_ARGCOMPLETE_TRACE') == 'static':
        raise

  with gcloud_exception_handler():
    _fix_google_module()
    gcloud_main = _import_gcloud_main()

  sys.exit(gcloud_main.main())


if __name__ == '__main__':
  main()
