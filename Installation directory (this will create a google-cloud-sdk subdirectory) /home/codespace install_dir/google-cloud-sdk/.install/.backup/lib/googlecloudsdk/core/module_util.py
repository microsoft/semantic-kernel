# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Utilities for accessing modules by installation independent paths."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import importlib
import importlib.util
import os
import sys

from googlecloudsdk.core import exceptions
import six


class Error(exceptions.Error):
  """Exceptions for this module."""


class ImportModuleError(Error):
  """ImportModule failed."""


def ImportModule(module_path):
  """Imports a module object given its ModulePath and returns it.

  A module_path from GetModulePath() from any valid installation is importable
  by ImportModule() in another installation of same release.

  Args:
    module_path: The module path to import.

  Raises:
    ImportModuleError: Malformed module path or any failure to import.

  Returns:
    The Cloud SDK object named by module_path.
  """

  # First get the module.
  parts = module_path.split(':')
  if len(parts) > 2:
    raise ImportModuleError(
        'Module path [{}] must be in the form: '
        'package(.module)+(:attribute(.attribute)*)?'.format(module_path))
  try:
    module = importlib.import_module(parts[0])
  except ImportError as e:
    raise ImportModuleError(
        'Module path [{}] not found: {}.'.format(module_path, e))
  if len(parts) == 1:
    return module

  # March down the attributes to get the object within the module.
  obj = module
  attributes = parts[1].split('.')
  for attr in attributes:
    try:
      obj = getattr(obj, attr)
    except AttributeError as e:
      raise ImportModuleError(
          'Module path [{}] not found: {}.'.format(module_path, e))
  return obj


def _GetPrivateModulePath(module_path):
  """Mock hook that returns the module path for module that starts with '__'."""
  del module_path
  return None


def GetModulePath(obj):
  """Returns the module path string for obj, None if it's builtin.

  The module path is relative and importable by ImportModule() from any
  installation of the current release.

  Args:
    obj: The object to get the module path from.

  Returns:
    The module path name for obj if not builtin else None.
  """
  try:
    # An object either has a module ...
    module = obj.__module__
  except AttributeError:
    # ... or it has a __class__ that has a __module__.
    obj = obj.__class__
    module = obj.__module__
  if six.PY3 and module == 'builtins':
    return None
  # For example, '__builtins__' for Python 2 built-in types.
  if module.startswith('__'):
    module = _GetPrivateModulePath(module)  # pylint: disable=assignment-from-none, function is a test mock hook
    if not module:
      return None
  try:
    return module + ':' + obj.__name__
  except AttributeError:
    try:
      return module + ':' + obj.__class__.__name__
    except AttributeError:
      return None


def ImportPath(path):
  """Imports and returns the module given a python source file path."""
  module_name = os.path.splitext(os.path.basename(path))[0]
  spec = importlib.util.spec_from_file_location(module_name, path)
  if not spec:
    raise ImportModuleError(
        'Module file [{}] not found.'.format(path))
  module = importlib.util.module_from_spec(spec)
  sys.modules[module_name] = module
  try:
    spec.loader.exec_module(module)
  except FileNotFoundError as e:
    raise ImportModuleError(
        'Module file [{}] not found: {}.'.format(path, e))
  return module
