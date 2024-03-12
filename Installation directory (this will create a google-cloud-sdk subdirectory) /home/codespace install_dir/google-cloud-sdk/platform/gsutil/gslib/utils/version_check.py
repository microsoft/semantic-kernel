# -*- coding: utf-8 -*-
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Utility functions to ensure the correct version of Python is used."""

import sys
from sys import version_info

# Key:   Int, supported Python major version
# Value: Int, min supported Python minor version
# We currently support Python >=3.5
MIN_SUPPORTED_PYTHON_VERSION = {3: 5}


def check_python_version_support():
  """Return an exception if running in an unsupported version of Python.

  This function compares the running version of cPython and against the list
  of supported python version. If the running version is less than any of the
  supported versions, return a Tuple of (False, Str(error message)) for the
  caller to handle. Minor versions of Python greater than those listed in the
  supported versions are allowed.

  Args:
    None
  Returns:
    Tuple(Boolean, String)

    A Tuple containing a Boolean and a String. The boolean represents if the
    version is supported, and the String will either be empty, or contain an
    error message.
  """

  major = sys.version_info.major
  minor = sys.version_info.minor

  if major not in MIN_SUPPORTED_PYTHON_VERSION:
    return (False, 'Gsutil does not support running under Python{major}'.format(
        major=major))
  if minor < MIN_SUPPORTED_PYTHON_VERSION[major]:
    lowest_minor = MIN_SUPPORTED_PYTHON_VERSION[major]
    return (
        False,
        'For Python{major}, gsutil requires Python{major}.{lowest_minor}+, but '
        'you are using Python{major}.{minor}'.format(major=major,
                                                     minor=minor,
                                                     lowest_minor=lowest_minor))
  return (True, '')
