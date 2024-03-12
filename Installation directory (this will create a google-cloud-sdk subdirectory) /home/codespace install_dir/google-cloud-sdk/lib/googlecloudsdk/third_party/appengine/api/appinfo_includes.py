# Copyright 2010 Google LLC. All Rights Reserved.
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

"""Used to parse app.yaml files while following builtins/includes directives."""

# WARNING: This file is externally viewable by our users.  All comments from
# this file will be stripped.  The docstrings will NOT.  Do not put sensitive
# information in docstrings.  If you must communicate internal information in
# this source file, please place them in comments only.

# To add a new builtin handler definition:
# - create a new directory in apphosting/ext/builtins/foo
# - modify the apphosting/ext/builtins/BUILD file and include your new
#   include.yaml file in the INCLUDE_YAML_FILES constant

from __future__ import absolute_import
from __future__ import unicode_literals


import logging
import os

from googlecloudsdk.third_party.appengine.api import appinfo
from googlecloudsdk.third_party.appengine.api import appinfo_errors
from googlecloudsdk.third_party.appengine.ext import builtins


class IncludeFileNotFound(Exception):
  """Raised if a specified include file cannot be found on disk."""


def Parse(appinfo_file):
  """Parse an AppYaml file and merge referenced includes and builtins.

  Args:
    appinfo_file: an opened file, for example the result of open('app.yaml').

  Returns:
    The parsed appinfo.AppInfoExternal object.
  """
  appyaml, _ = ParseAndReturnIncludePaths(appinfo_file)
  return appyaml


def ParseAndReturnIncludePaths(appinfo_file):
  """Parse an AppYaml file and merge referenced includes and builtins.

  Args:
    appinfo_file: an opened file, for example the result of open('app.yaml').

  Returns:
    A tuple where the first element is the parsed appinfo.AppInfoExternal
    object and the second element is a list of the absolute paths of the
    included files, in no particular order.
  """
  try:
    appinfo_path = appinfo_file.name
    if not os.path.isfile(appinfo_path):
      raise Exception('Name defined by appinfo_file does not appear to be a '
                      'valid file: %s' % appinfo_path)
  except AttributeError:
    raise Exception('File object passed to ParseAndMerge does not define '
                    'attribute "name" as as full file path.')

  appyaml = appinfo.LoadSingleAppInfo(appinfo_file)
  appyaml, include_paths = _MergeBuiltinsIncludes(appinfo_path, appyaml)

  # Reimplement appinfo.py handler checks after merge.
  if not appyaml.handlers:
    # Add a placeholder handler for VM runtime apps.
    # TODO(b/65159665): Do not require this placeholder entry.
    if appyaml.IsVm():
      appyaml.handlers = [appinfo.URLMap(url='.*', script='PLACEHOLDER')]
    else:
      appyaml.handlers = []
  if len(appyaml.handlers) > appinfo.MAX_URL_MAPS:
    raise appinfo_errors.TooManyURLMappings(
        'Found more than %d URLMap entries in application configuration' %
        appinfo.MAX_URL_MAPS)
  if appyaml.runtime == 'python27' and appyaml.threadsafe:
    for handler in appyaml.handlers:
      if (handler.script and (handler.script.endswith('.py') or
                              '/' in handler.script)):
        raise appinfo_errors.ThreadsafeWithCgiHandler(
            'Threadsafe cannot be enabled with CGI handler: %s' %
            handler.script)

  return appyaml, include_paths


def _MergeBuiltinsIncludes(appinfo_path, appyaml):
  """Merges app.yaml files from builtins and includes directives in appyaml.

  Args:
    appinfo_path: the application directory.
    appyaml: the yaml file to obtain builtins and includes directives from.

  Returns:
    A tuple where the first element is the modified appyaml object
    incorporating the referenced yaml files, and the second element is a list
    of the absolute paths of the included files, in no particular order.
  """

  # If no builtin handlers are defined, initialize a BuiltinHandler object
  # with "default: on".
  if not appyaml.builtins:
    appyaml.builtins = [appinfo.BuiltinHandler(default='on')]
  # Turn on defaults if not included in config.
  else:
    if not appinfo.BuiltinHandler.IsDefined(appyaml.builtins, 'default'):
      appyaml.builtins.append(appinfo.BuiltinHandler(default='on'))

  # Returns result of merging all discovered AppInclude objects.
  # TODO(user): Stop using vm_settings.vm_runtime. b/9513210.
  runtime_for_including = appyaml.runtime
  if runtime_for_including == 'vm':
    runtime_for_including = appyaml.vm_settings.get('vm_runtime', 'python27')
  aggregate_appinclude, include_paths = (
      _ResolveIncludes(appinfo_path,
                       appinfo.AppInclude(builtins=appyaml.builtins,
                                          includes=appyaml.includes),
                       os.path.dirname(appinfo_path),
                       runtime_for_including))

  return (
      appinfo.AppInclude.MergeAppYamlAppInclude(appyaml,
                                                aggregate_appinclude),
      include_paths)


def _ResolveIncludes(included_from, app_include, basepath, runtime, state=None):
  """Recursively includes all encountered builtins/includes directives.

  This function takes an initial AppInclude object specified as a parameter
  and recursively evaluates every builtins/includes directive in the passed
  in AppInclude and any files they reference.  The sole output of the function
  is an AppInclude object that is the result of merging all encountered
  AppInclude objects.  This must then be merged with the root AppYaml object.

  Args:
    included_from: file that included file was included from.
    app_include: the AppInclude object to resolve.
    basepath: application basepath.
    runtime: name of the runtime.
    state: contains the list of included and excluded files as well as the
           directives of all encountered AppInclude objects.

  Returns:
    A two-element tuple where the first element is the AppInclude object merged
    from following all builtins/includes defined in provided AppInclude object;
    and the second element is a list of the absolute paths of the included
    files, in no particular order.

  Raises:
    IncludeFileNotFound: if file specified in an include statement cannot be
      resolved to an includeable file (result from _ResolvePath is False).
  """

  class RecurseState(object):
    # Store the absolute path of included and excluded files mapping to the
    # first file to include/exclude them.  Keys are used to prevent duplicates
    # and to detect the case where included builtins are later excluded or
    # vice versa.  Values are used to print intelligible errors.

    def __init__(self):
      self.includes = {}
      self.excludes = {}
      self.aggregate_appinclude = appinfo.AppInclude()

  # Initialize return result and includes/excludes dicts.
  if not state:
    state = RecurseState()

  # Merge AppInclude directives with aggregate_appinclude.
  appinfo.AppInclude.MergeAppIncludes(state.aggregate_appinclude, app_include)

  # Construct includes list from builtins.
  includes_list = _ConvertBuiltinsToIncludes(included_from, app_include,
                                             state, runtime)

  # Then extend list with includes directives.
  includes_list.extend(app_include.includes or [])

  # Recurse through includes.
  for i in includes_list:
    inc_path = _ResolvePath(included_from, i, basepath)
    if not inc_path:
      raise IncludeFileNotFound('File %s listed in includes directive of %s '
                                'could not be found.' % (i, included_from))

    if inc_path in state.excludes:
      logging.warning('%s already disabled by %s but later included by %s',
                      inc_path, state.excludes[inc_path], included_from)
    elif not inc_path in state.includes:
      state.includes[inc_path] = included_from
      with open(inc_path, 'r') as yaml_file:
        try:
          inc_yaml = appinfo.LoadAppInclude(yaml_file)
          _ResolveIncludes(inc_path, inc_yaml, basepath, runtime, state=state)
        except appinfo_errors.EmptyConfigurationFile:
          # Do not print empty warnings for default include file.
          if not os.path.basename(os.path.dirname(inc_path)) == 'default':
            logging.warning('Nothing to include in %s', inc_path)
    # No info printed on duplicate includes.

  return state.aggregate_appinclude, list(state.includes.keys())


def _ConvertBuiltinsToIncludes(included_from, app_include, state, runtime):
  includes_list = []
  if app_include.builtins:
    builtins_list = appinfo.BuiltinHandler.ListToTuples(app_include.builtins)
    for builtin_name, on_or_off in builtins_list:
      # Ignore keys mapped to None.
      if not on_or_off:
        continue

      # Retrieve absolute path of builtins yaml file.
      yaml_path = builtins.get_yaml_path(builtin_name, runtime)

      if on_or_off == 'on':
        includes_list.append(yaml_path)
      elif on_or_off == 'off':
        if yaml_path in state.includes:
          logging.warning('%s already included by %s but later disabled by %s',
                          yaml_path, state.includes[yaml_path], included_from)
        state.excludes[yaml_path] = included_from
      else:
        logging.error('Invalid state for AppInclude object loaded from %s; '
                      'builtins directive "%s: %s" ignored.',
                      included_from, builtin_name, on_or_off)

  return includes_list


def _ResolvePath(included_from, included_path, basepath):
  """Gets the absolute path of the file to be included.

  Resolves in the following order:
  - absolute path or relative to working directory
    (path as specified resolves to a file)
  - relative to basepath
    (basepath + path resolves to a file)
  - relative to file it was included from
    (included_from + included_path resolves to a file)

  Args:
    included_from: absolute path of file that included_path was included from.
    included_path: file string from includes directive.
    basepath: the application directory.

  Returns:
    absolute path of the first file found for included_path or ''.
  """

  # Check relative to file it was included from.
  # NOTE: Relative check must come before absolute path / working directory and
  # basepath checks.  If file name is, for instance, include.yaml, and the same
  # file name exists in the working directory or basepath, it's clear that a
  # bare name reference in up/up.yaml to include include.yaml probably means
  # up/include.yaml, not basepath/include.yaml.
  path = os.path.join(os.path.dirname(included_from), included_path)
  if not _IsFileOrDirWithFile(path):
    # Check relative to basepath.
    path = os.path.join(basepath, included_path)
    if not _IsFileOrDirWithFile(path):
      # Check as absolute path or relative to working directory.
      path = included_path
      if not _IsFileOrDirWithFile(path):
        return ''

  if os.path.isfile(path):
    return os.path.normcase(os.path.abspath(path))

  return os.path.normcase(os.path.abspath(os.path.join(path, 'include.yaml')))


def _IsFileOrDirWithFile(path):
  """Determine if a path is a file or a directory with an appropriate file."""
  return os.path.isfile(path) or (
      os.path.isdir(path) and
      os.path.isfile(os.path.join(path, 'include.yaml')))
