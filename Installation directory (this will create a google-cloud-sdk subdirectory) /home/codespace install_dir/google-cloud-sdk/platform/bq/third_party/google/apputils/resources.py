#!/usr/bin/env python
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Wrapper around setuptools' pkg_resources with more Google-like names.

This module is not very useful on its own, but many Google open-source projects
are used to a different naming scheme, and this module makes the transition
easier.
"""

__author__ = 'dborowitz@google.com (Dave Borowitz)'

import atexit

import pkg_resources


def _Call(func, name):
  """Call a pkg_resources function.

  Args:
    func: A function from pkg_resources that takes the arguments
          (package_or_requirement, resource_name); for more info,
          see http://peak.telecommunity.com/DevCenter/PkgResources
    name: A name of the form 'module.name:path/to/resource'; this should
          generally be built from __name__ in the calling module.

  Returns:
    The result of calling the function on the split resource name.
  """
  pkg_name, resource_name = name.split(':', 1)
  return func(pkg_name, resource_name)


def GetResource(name):
  """Get a resource as a string; see _Call."""
  return _Call(pkg_resources.resource_string, name)


def GetResourceAsFile(name):
  """Get a resource as a file-like object; see _Call."""
  return _Call(pkg_resources.resource_stream, name)


_extracted_files = False


def GetResourceFilename(name):
  """Get a filename for a resource; see _Call."""
  global _extracted_files  # pylint: disable-msg=W0603
  if not _extracted_files:
    atexit.register(pkg_resources.cleanup_resources)
    _extracted_files = True

  return _Call(pkg_resources.resource_filename, name)
