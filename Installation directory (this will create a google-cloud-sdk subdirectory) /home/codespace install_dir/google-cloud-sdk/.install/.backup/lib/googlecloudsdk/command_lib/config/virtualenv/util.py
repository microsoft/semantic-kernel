# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Library of methods for manipulating virtualenv setup."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
import six

# Python modules to install into virtual env environment
MODULES = [
    'crcmod',
    'grpcio',
    'pyopenssl==23.2.0',
    'google_crc32c',
    'certifi',
    'cryptography',
]

# Enable file name.
ENABLE_FILE = 'enabled'


def IsPy2():
  """Wrap six.PY2, needed because mocking six.PY2 breaks test lib things."""
  return six.PY2


def IsWindows():
  """Wrapped because mocking directly can break test lib things."""
  return platforms.OperatingSystem.IsWindows()


def VirtualEnvExists(ve_dir):
  """Returns True if Virtual Env already exists."""
  return os.path.isdir(ve_dir)


def EnableFileExists(ve_dir):
  """Returns True if enable file exists."""
  return os.path.exists('{}/{}'.format(ve_dir, ENABLE_FILE))


def CreateEnableFile(ve_dir):
  """Create enable file."""
  files.WriteFileContents('{}/{}'.format(ve_dir, ENABLE_FILE), 'enabled')


def RmEnableFile(ve_dir):
  """Remove enable file."""
  os.unlink('{}/{}'.format(ve_dir, ENABLE_FILE))
