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

"""Utilities for the dev_appserver.py wrapper script.

Functions for parsing app.yaml files and installing the required components.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import os

from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
import six

# Runtime ID to component mapping. python27-libs is a special token indicating
# that the real runtime id is python27, and that a libraries section has been
# specified in the app.yaml.
_RUNTIME_COMPONENTS = {
    'java': 'app-engine-java',
    'php55': 'app-engine-php',
    'go': 'app-engine-go',
    'python27-libs': 'app-engine-python-extras',
}


_WARNING_RUNTIMES = {
    'php': ('The Cloud SDK no longer ships runtimes for PHP 5.4.  Please set '
            'your runtime to be "php55".')
}

_YAML_FILE_EXTENSIONS = ('.yaml', '.yml')


_TRUE_VALUES = ['true', 'yes', '1']


_FALSE_VALUES = ['false', 'no', '0']


_UPSTREAM_DEV_APPSERVER_FLAGS = ['--support_datastore_emulator']


class MultipleAppYamlError(Exception):
  """An application configuration has more than one valid app yaml files."""


def GetRuntimes(args):
  """Gets a list of unique runtimes that the user is about to run.

  Args:
    args: A list of arguments (typically sys.argv).

  Returns:
    A set of runtime strings. If python27 and libraries section is populated
    in any of the yaml-files, 'python27-libs', a fake runtime id, will be part
    of the set, in conjunction with the original 'python27'.

  Raises:
    MultipleAppYamlError: The supplied application configuration has duplicate
      app yamls.
  """
  runtimes = set()
  for arg in args:
    # Check all the arguments to see if they're application yaml files or
    # directories that include yaml files.
    yaml_candidate = None
    if (os.path.isfile(arg) and
        os.path.splitext(arg)[1] in _YAML_FILE_EXTENSIONS):
      yaml_candidate = arg
    elif os.path.isdir(arg):
      for extension in _YAML_FILE_EXTENSIONS:
        fullname = os.path.join(arg, 'app' + extension)
        if os.path.isfile(fullname):
          if yaml_candidate:
            raise MultipleAppYamlError(
                'Directory "{0}" contains conflicting files {1}'.format(
                    arg, ' and '.join(yaml_candidate)))

          yaml_candidate = fullname

    if yaml_candidate:
      try:
        info = yaml.load_path(yaml_candidate)
      except yaml.Error:
        continue

      # safe_load can return arbitrary objects, we need a dict.
      if not isinstance(info, dict):
        continue
      # Grab the runtime from the yaml, if it exists.
      if 'runtime' in info:
        runtime = info.get('runtime')
        if type(runtime) == str:
          if runtime == 'python27' and info.get('libraries'):
            runtimes.add('python27-libs')
          runtimes.add(runtime)
          if runtime in _WARNING_RUNTIMES:
            log.warning(_WARNING_RUNTIMES[runtime])
    elif os.path.isfile(os.path.join(arg, 'WEB-INF', 'appengine-web.xml')):
      # For unstanged Java App Engine apps, which may not have any yaml files.
      runtimes.add('java')
  return runtimes


def GetComponents(runtimes):
  """Gets a list of required components.

  Args:
    runtimes: A list containing the required runtime ids.
  Returns:
    A list of components that must be present.
  """
  # Always install python.
  components = ['app-engine-python']
  for requested_runtime in runtimes:
    for component_runtime, component in six.iteritems(_RUNTIME_COMPONENTS):
      if component_runtime in requested_runtime:
        components.append(component)
  return components


def _ParseBoolean(value):
  """This is upstream logic from dev_appserver for parsing boolean arguments.

  Args:
    value: value assigned to a flag.

  Returns:
    A boolean parsed from value.

  Raises:
    ValueError: value.lower() is not in _TRUE_VALUES + _FALSE_VALUES.
  """
  if isinstance(value, bool):
    return value
  if value:
    value = value.lower()
    if value in _TRUE_VALUES:
      return True
    if value in _FALSE_VALUES:
      return False
    repr_value = (repr(value) for value in  _TRUE_VALUES + _FALSE_VALUES)
    raise ValueError('%r unrecognized boolean; known booleans are %s.' %
                     (value, ', '.join(repr_value)))
  return True


def ParseDevAppserverFlags(args):
  """Parse flags from app engine dev_appserver.py.

  Only the subset of args are parsed here. These args are listed in
  _UPSTREAM_DEV_APPSERVER_FLAGS.

  Args:
    args: A list of arguments (typically sys.argv).

  Returns:
    options: An argparse.Namespace containing the command line arguments.
  """
  upstream_args = [
      arg for arg in args if
      any(arg.startswith(upstream_arg) for upstream_arg
          in _UPSTREAM_DEV_APPSERVER_FLAGS)]
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--support_datastore_emulator', dest='support_datastore_emulator',
      type=_ParseBoolean, const=True, nargs='?', default=False)
  return parser.parse_args(upstream_args)
