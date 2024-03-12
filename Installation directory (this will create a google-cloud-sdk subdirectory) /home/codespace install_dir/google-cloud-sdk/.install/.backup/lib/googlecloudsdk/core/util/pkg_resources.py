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

"""Utilities for accessing local package resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import fnmatch
import glob
import importlib.util
import os
import pkgutil
import sys
import types

from googlecloudsdk.core.util import files


def _GetPackageName(module_name):
  """Returns package name for given module name."""
  last_dot_idx = module_name.rfind('.')
  if last_dot_idx > 0:
    return module_name[:last_dot_idx]
  return ''


def GetResource(module_name, resource_name):
  """Get a resource as a byte string for given resource in same package."""
  return pkgutil.get_data(_GetPackageName(module_name), resource_name)


def GetResourceFromFile(path):
  """Gets the given resource as a byte string.

  This is similar to GetResource(), but uses file paths instead of module names.

  Args:
    path: str, filesystem like path to a file/resource.

  Returns:
    The contents of the resource as a byte string.

  Raises:
    IOError: if resource is not found under given path.
  """
  if os.path.isfile(path):
    return files.ReadBinaryFileContents(path)

  importer = pkgutil.get_importer(os.path.dirname(path))
  if hasattr(importer, 'get_data'):
    return importer.get_data(path)

  raise IOError('File not found {0}'.format(path))


def IsImportable(name, path):
  """Checks if given name can be imported at given path.

  Args:
    name: str, module name without '.' or suffixes.
    path: str, filesystem path to location of the module.

  Returns:
    True, if name is importable.
  """

  if os.path.isdir(path):
    if not os.path.isfile(os.path.join(path, '__init__.py')):
      return path in sys.path
    name_path = os.path.join(path, name)
    if os.path.isdir(name_path):
      # Subdirectory is considered subpackage if it has __init__.py file.
      return os.path.isfile(os.path.join(name_path, '__init__.py'))
    return os.path.exists(name_path + '.py')

  name_path = name.split('.')
  importer = pkgutil.get_importer(os.path.join(path, *name_path[:-1]))
  if not importer:
    return False
  find_spec_exists = hasattr(importer, 'find_spec')
  # zipimporter did not add find_spec until 3.10.
  find_method = importer.find_spec if find_spec_exists else importer.find_module  # pylint: disable=deprecated-method
  return find_method(name_path[-1]) is not None


def GetModuleFromPath(name_to_give, module_path):
  """Loads module at given path under given name.

  Note that it also updates sys.modules with name_to_give.

  Args:
    name_to_give: str, name to assign to loaded module
    module_path: str, python path to location of the module, this is either
      filesystem path or path into egg or zip package

  Returns:
    Imported module

  Raises:
    ImportError: if module cannot be imported.
  """
  if os.path.isfile(os.path.join(module_path, '__init__.py')):
    spec = importlib.util.spec_from_file_location(
        name_to_give, os.path.join(module_path, '__init__.py')
    )
  elif os.path.isfile(module_path + '.py'):
    spec = importlib.util.spec_from_file_location(
        name_to_give, module_path + '.py'
    )
  else:
    # Ideally we could do e.g.:
    #   module_dir = os.path.dirname(module_path)
    #   finder = pkgutil.get_importer(module_dir)
    #   spec = finder.find_spec(module_name)
    # and go through the normal flow below, but there doesn't seem to be a way
    # to customize the module name in that case. So we fall back to creating the
    # ModuleType and populating it ourselves here.
    return _GetModuleFromPathViaPkgutil(module_path, name_to_give)

  module = importlib.util.module_from_spec(spec)
  sys.modules[name_to_give] = module
  spec.loader.exec_module(module)
  return module


def _GetModuleFromPathViaPkgutil(module_path, name_to_give):
  """Loads module by using pkgutil.get_importer mechanism."""
  importer = pkgutil.get_importer(os.path.dirname(module_path))
  if not importer:
    raise ImportError('{0} not found'.format(module_path))

  find_spec_exists = hasattr(importer, 'find_spec')
  find_method = importer.find_spec if find_spec_exists else importer.find_module  # pylint: disable=deprecated-method
  module_name = os.path.basename(module_path)
  if find_method(module_name):  # pylint: disable=deprecated-method
    return _LoadModule(importer, module_path, module_name, name_to_give)
  raise ImportError('{0} not found'.format(module_path))


def _LoadModule(importer, module_path, module_name, name_to_give):
  """Loads the module or package under given name."""
  code = importer.get_code(module_name)
  module = types.ModuleType(name_to_give)
  if importer.is_package(module_name):
    module.__path__ = [module_path]
    module.__file__ = os.path.join(module_path, '__init__.pyc')
  else:
    module.__file__ = module_path + '.pyc'

  # pylint: disable=exec-used
  exec(code, module.__dict__)
  sys.modules[name_to_give] = module
  return module


def _IterModules(file_list, extra_extensions, prefix=None):
  """Yields module names from given list of file paths with given prefix."""
  yielded = set()
  if extra_extensions is None:
    extra_extensions = []
  if prefix is None:
    prefix = ''
  for file_path in file_list:
    if not file_path.startswith(prefix):
      continue

    file_path_parts = file_path[len(prefix) :].split(os.sep)

    if len(file_path_parts) == 2 and file_path_parts[1].startswith(
        '__init__.py'
    ):
      if file_path_parts[0] not in yielded:
        yielded.add(file_path_parts[0])
        yield file_path_parts[0], True

    if len(file_path_parts) != 1:
      continue

    filename = os.path.basename(file_path_parts[0])
    modname, ext = os.path.splitext(filename)
    if modname == '__init__' or (ext != '.py' and ext not in extra_extensions):
      continue

    to_yield = modname if ext == '.py' else filename
    if '.' not in modname and to_yield not in yielded:
      yielded.add(to_yield)
      yield to_yield, False


def _ListPackagesAndFiles(path):
  """List packages or modules which can be imported at given path."""
  importables = []
  for filename in os.listdir(path):
    if os.path.isfile(os.path.join(path, filename)):
      importables.append(filename)
    else:
      pkg_init_filepath = os.path.join(path, filename, '__init__.py')
      if os.path.isfile(pkg_init_filepath):
        importables.append(os.path.join(filename, '__init__.py'))
  return importables


def ListPackage(path, extra_extensions=None):
  """Returns list of packages and modules in given path.

  Args:
    path: str, filesystem path
    extra_extensions: [str], The list of file extra extensions that should be
      considered modules for the purposes of listing (in addition to .py).

  Returns:
    tuple([packages], [modules])
  """
  iter_modules = []
  if os.path.isdir(path):
    iter_modules = _IterModules(_ListPackagesAndFiles(path), extra_extensions)
  else:
    importer = pkgutil.get_importer(path)
    if hasattr(importer, '_files'):
      # pylint:disable=protected-access
      iter_modules = _IterModules(
          importer._files, extra_extensions, importer.prefix
      )
  packages, modules = [], []
  for name, ispkg in iter_modules:
    if ispkg:
      packages.append(name)
    else:
      modules.append(name)
  return sorted(packages), sorted(modules)


@contextlib.contextmanager
def GetFileTextReaderByLine(path):
  """Get a file reader for given path."""
  if os.path.isfile(path):
    f = files.FileReader(path)
    try:
      yield f
    finally:
      f.close()
  else:
    byte_string = GetResourceFromFile(path)
    yield str(byte_string, 'utf-8').split(os.linesep)


def GetFilesFromDirectory(path_dir, filter_pattern='*.*'):
  """Get files from a given directory that match a pattern.

  Args:
    path_dir: str, filesystem path to directory
    filter_pattern: str, pattern to filter files to retrieve.

  Returns:
    List of filtered files from a directory.

  Raises:
    IOError: if resource is not found under given path.
  """
  if os.path.isdir(path_dir):
    return glob.glob(f'{path_dir}/{filter_pattern}')
  else:
    importer = pkgutil.get_importer(path_dir)
    if not hasattr(importer, 'get_data'):
      raise IOError('Path not found {0}'.format(path_dir))

    filtered_files = []
    # pylint:disable=protected-access
    for file_path in importer._files:
      if not file_path.startswith(importer.prefix):
        continue

      file_path_parts = file_path[len(importer.prefix) :].split(os.sep)

      if len(file_path_parts) != 1:
        continue

      if fnmatch.fnmatch(file_path_parts[0], f'{filter_pattern}'):
        filtered_files.append(
            os.path.join(path_dir, file_path_parts[0])
        )
    return filtered_files
