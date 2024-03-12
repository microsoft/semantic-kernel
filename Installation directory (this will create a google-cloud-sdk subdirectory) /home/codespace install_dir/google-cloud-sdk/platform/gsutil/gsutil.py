#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Wrapper module for running gslib.__main__.main() from the command line."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import sys
import warnings

# TODO: gsutil-beta: Distribute a pylint rc file.

ver = sys.version_info
if (ver.major == 2 and ver.minor < 7) or (ver.major == 3 and ver.minor < 5):
  sys.exit('gsutil requires python 2.7 or 3.5+.')

# setup a string to load the correct httplib2
if sys.version_info.major == 2:
  submodule_pyvers = 'python2'
else:
  submodule_pyvers = 'python3'


def OutputAndExit(message):
  sys.stderr.write('%s\n' % message)
  sys.exit(1)


def _fix_google_module():
  """Reloads the google module to prefer our third_party copy.

  When Python is not invoked with the -S option, it may preload the google module via .pth file.
  This leads to the "site_packages" version being preferred over gsutil "third_party" version.
  To force the "third_party" version, insert the path at the start of sys.path and reload the google module.

  This is a hacky. Reloading is required for the rare case that users have
  google-auth already installed in their Python environment.
  Note that this reload may cause an issue for Python 3.5.3 and lower
  because of the weakref issue, fixed in Python 3.5.4:
  https://github.com/python/cpython/commit/9cd7e17640a49635d1c1f8c2989578a8fc2c1de6.
  """
  if 'google' not in sys.modules:
    return
  import importlib  # pylint: disable=g-import-not-at-top
  importlib.reload(sys.modules['google'])


GSUTIL_DIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
if not GSUTIL_DIR:
  OutputAndExit('Unable to determine where gsutil is installed. Sorry, '
                'cannot run correctly without this.\n')

# The wrapper script adds all third_party libraries to the Python path, since
# we don't assume any third party libraries are installed system-wide.
THIRD_PARTY_DIR = os.path.join(GSUTIL_DIR, 'third_party')
VENDORED_DIR = os.path.join(THIRD_PARTY_DIR, 'vendored')

# Flag for whether or not an import wrapper is used to measure time taken for
# individual imports.
MEASURING_TIME_ACTIVE = False

# Filter out "module was already imported" warnings that get printed after we
# add our bundled version of modules to the Python path.
warnings.filterwarnings('ignore',
                        category=UserWarning,
                        message=r'.* httplib2 was already imported from')
warnings.filterwarnings('ignore',
                        category=UserWarning,
                        message=r'.* oauth2client was already imported from')

# List of third-party libraries. The first element of the tuple is the name of
# the directory under third_party and the second element is the subdirectory
# that needs to be added to sys.path.
THIRD_PARTY_LIBS = [
    ('argcomplete', ''),  # For tab-completion (gcloud installs only).
    ('mock', ''),
    ('funcsigs', ''),  # mock dependency
    ('google-reauth-python', ''),  # Package name: google_reauth
    ('pyu2f', ''),  # google_reauth dependency
    ('pyasn1', ''),  # oauth2client dependency
    ('pyasn1-modules', ''),  # oauth2client dependency
    ('rsa', ''),  # oauth2client dependency
    ('apitools', ''),
    ('gcs-oauth2-boto-plugin', ''),
    ('fasteners', ''),  # oauth2client and apitools dependency
    ('monotonic', ''),  # fasteners dependency
    ('pyparsing', ''),  # httplib2 dependency
    ('httplib2', submodule_pyvers),
    ('retry-decorator', ''),
    ('six', ''),  # Python 2 / 3 compatibility dependency
    ('cachetools', 'src'),  # google auth dependency
    ('urllib3', 'src'),  # requests dependency
    ('charset_normalizer', ''),  # requests dependency
    ('chardet', ''),  # requests dependency
    ('certifi', ''),  # requests dependency
    ('idna', ''),  # requests dependency
    ('requests', ''),  # google auth dependency
    ('google-auth-library-python', ''),
]

# The wrapper script adds all third_party libraries to the Python path, since
# we don't assume any third party libraries are installed system-wide.
#
# Note that vendored libraries (e.g. Boto) are added to the Python path in
# gslib/__init__.py, as they will always be present even when bypassing this
# script and invoking gslib.__main__.py's main() method directly.
THIRD_PARTY_DIR = os.path.join(GSUTIL_DIR, 'third_party')
for libdir, subdir in THIRD_PARTY_LIBS:
  if not os.path.isdir(os.path.join(THIRD_PARTY_DIR, libdir)):
    OutputAndExit(
        'There is no %s library under the gsutil third-party directory (%s).\n'
        'The gsutil command cannot work properly when installed this way.\n'
        'Please re-install gsutil per the installation instructions.' %
        (libdir, THIRD_PARTY_DIR))
  sys.path.insert(0, os.path.join(THIRD_PARTY_DIR, libdir, subdir))

CRCMOD_PATH = os.path.join(THIRD_PARTY_DIR, 'crcmod', submodule_pyvers)
CRCMOD_OSX_PATH = os.path.join(THIRD_PARTY_DIR, 'crcmod_osx')
try:
  # pylint: disable=g-import-not-at-top
  import crcmod
except ImportError:
  # Note: the bundled crcmod module under THIRD_PARTY_DIR does not include its
  # compiled C extension, but we still add it to sys.path because other parts of
  # gsutil assume that at least the core crcmod module will be available.
  local_crcmod_path = (CRCMOD_OSX_PATH if 'darwin' in str(sys.platform).lower()
                       else CRCMOD_PATH)
  sys.path.insert(0, local_crcmod_path)


def RunMain():
  _fix_google_module()
  # pylint: disable=g-import-not-at-top
  import gslib.__main__
  sys.exit(gslib.__main__.main())


if __name__ == '__main__':
  RunMain()
