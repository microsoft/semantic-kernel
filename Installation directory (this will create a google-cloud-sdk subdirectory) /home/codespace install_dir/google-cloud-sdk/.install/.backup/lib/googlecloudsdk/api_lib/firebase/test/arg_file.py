# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""A library to load and validate test arguments from a YAML argument file.

  The optional, positional ARGSPEC argument on the command line is used to
  specify an ARG_FILE:ARG_GROUP_NAME pair, where ARG_FILE is the path to the
  YAML-format argument file, and ARG_GROUP_NAME is the name of the arg group
  to load and parse.

  The basic format of a YAML argument file is:

  arg-group-1:
    arg1: value1
    arg2: value2

  arg-group-2:
    arg3: value3
    ...

  A special 'include: [<group-list>]' syntax allows composition/merging of
  arg-groups (see example below). Included groups can include: other groups as
  well, with unlimited nesting within one YAML file.

  Precedence of arguments:
    Args appearing on the command line will override any arg specified within
    an argument file.
    Args which are merged into a group using the 'include:' keyword have lower
    precedence than an arg already defined in that group.

  Example of a YAML argument file for use with 'gcloud test run ...' commands:

  memegen-robo-args:
    type: robo
    app: path/to/memegen.apk
    robo-script: crawl_init.json
    include: [common-args, matrix-quick]
    timeout: 5m

  notepad-instr-args:
    type: instrumentation
    app: path/to/notepad.apk
    test: path/to/notepad-test.apk
    include: [common-args, matrix-large]

  common-args:
    results-bucket: gs://my-results-bucket
    timeout: 600

  matrix-quick:
    device-ids: [Nexus5, Nexus6]
    os-version-ids: 21
    locales: en
    orientation: landscape

  matrix-large:
    device-ids: [Nexus5, Nexus6, Nexus7, Nexus9, Nexus10]
    os-version-ids: [18, 19, 21]
    include: all-supported-locales

  all-supported-locales:
    locales: [de, en_US, en_GB, es, fr, it, ru, zh]
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.firebase.test import arg_validate
from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
import six


_ARG_GROUP_PATTERN = re.compile(r'^[a-zA-Z0-9._\-]+\Z')

_INCLUDE = 'include'


def GetArgsFromArgFile(argspec, all_test_args_set):
  """Loads a group of test args from an optional user-supplied arg file.

  Args:
    argspec: string containing an ARG_FILE:ARG_GROUP_NAME pair, where ARG_FILE
      is the path to a file containing groups of test arguments in yaml format,
      and ARG_GROUP_NAME is a yaml object name of a group of arg:value pairs.
    all_test_args_set: a set of strings for every possible gcloud-test argument
      name regardless of test type. Used for validation.

  Returns:
    A {str:str} dict created from the file which maps arg names to arg values.

  Raises:
    BadFileException: the YAML parser encountered an I/O error or syntax error
      while reading the arg-file.
    InvalidTestArgError: an argument name was not a valid gcloud test arg.
    InvalidArgException: an argument has an invalid value or no value.
  """
  if argspec is None:
    return {}

  arg_file, group_name = _SplitArgFileAndGroup(argspec)
  all_arg_groups = _ReadArgGroupsFromFile(arg_file)
  _ValidateArgGroupNames(list(all_arg_groups.keys()))

  args_from_file = {}
  _MergeArgGroupIntoArgs(args_from_file, group_name, all_arg_groups,
                         all_test_args_set)
  log.info('Args loaded from file: ' + six.text_type(args_from_file))
  return args_from_file


def _SplitArgFileAndGroup(file_and_group_str):
  """Parses an ARGSPEC and returns the arg filename and arg group name."""
  index = file_and_group_str.rfind(':')
  if index < 0 or (index == 2 and file_and_group_str.startswith('gs://')):
    raise exceptions.InvalidArgException(
        'arg-spec', 'Format must be ARG_FILE:ARG_GROUP_NAME')
  return file_and_group_str[:index], file_and_group_str[index+1:]


def _ReadArgGroupsFromFile(arg_file):
  """Collects all the arg groups defined in the yaml file into a dictionary.

  Each dictionary key is an arg-group name whose corresponding value is a nested
  dictionary containing arg-name: arg-value pairs defined in that group.

  Args:
    arg_file: str, the name of the YAML argument file to open and parse.

  Returns:
    A dict containing all arg-groups found in the arg_file.

  Raises:
    yaml.Error: If the YAML file could not be read or parsed.
    BadFileException: If the contents of the file are not valid.
  """
  all_groups = {}
  for d in yaml.load_all_path(arg_file):
    if d is None:
      log.warning('Ignoring empty yaml document.')
    elif isinstance(d, dict):
      all_groups.update(d)
    else:
      raise calliope_exceptions.BadFileException(
          'Failed to parse YAML file [{}]: [{}] is not a valid argument '
          'group.'.format(arg_file, six.text_type(d)))
  return all_groups


def _ValidateArgGroupNames(group_names):
  for group_name in group_names:
    if not _ARG_GROUP_PATTERN.match(group_name):
      raise calliope_exceptions.BadFileException(
          'Invalid argument group name [{0}]. Names may only use a-zA-Z0-9._-'
          .format(group_name))


def _MergeArgGroupIntoArgs(
    args_from_file, group_name, all_arg_groups, all_test_args_set,
    already_included_set=None):
  """Merges args from an arg group into the given args_from_file dictionary.

  Args:
    args_from_file: dict of arg:value pairs already loaded from the arg-file.
    group_name: str, the name of the arg-group to merge into args_from_file.
    all_arg_groups: dict containing all arg-groups loaded from the arg-file.
    all_test_args_set: set of str, all possible test arg names.
    already_included_set: set of str, all group names which were already
      included. Used to detect 'include:' cycles.

  Raises:
    BadFileException: an undefined arg-group name was encountered.
    InvalidArgException: a valid argument name has an invalid value, or
      use of include: led to cyclic references.
    InvalidTestArgError: an undefined argument name was encountered.
  """
  if already_included_set is None:
    already_included_set = set()
  elif group_name in already_included_set:
    raise exceptions.InvalidArgException(
        _INCLUDE,
        'Detected cyclic reference to arg group [{g}]'.format(g=group_name))
  if group_name not in all_arg_groups:
    raise calliope_exceptions.BadFileException(
        'Could not find argument group [{g}] in argument file.'
        .format(g=group_name))

  arg_group = all_arg_groups[group_name]
  if not arg_group:
    log.warning('Argument group [{0}] is empty.'.format(group_name))
    return

  for arg_name in arg_group:
    arg = arg_validate.InternalArgNameFrom(arg_name)
    # Must process include: groups last in order to follow precedence rules.
    if arg == _INCLUDE:
      continue

    if arg not in all_test_args_set:
      raise exceptions.InvalidTestArgError(arg_name)
    if arg in args_from_file:
      log.info(
          'Skipping include: of arg [{0}] because it already had value [{1}].'
          .format(arg_name, args_from_file[arg]))
    else:
      args_from_file[arg] = arg_validate.ValidateArgFromFile(
          arg, arg_group[arg_name])

  already_included_set.add(group_name)  # Prevent "include:" cycles

  if _INCLUDE in arg_group:
    included_groups = arg_validate.ValidateStringList(_INCLUDE,
                                                      arg_group[_INCLUDE])
    for included_group in included_groups:
      _MergeArgGroupIntoArgs(args_from_file, included_group, all_arg_groups,
                             all_test_args_set, already_included_set)


# pylint: disable=unused-argument
def ArgSpecCompleter(prefix, parsed_args, **kwargs):
  """Tab-completion function for ARGSPECs in the format ARG_FILE:ARG_GROUP.

  If the ARG_FILE exists, parse it on-the-fly to get the list of every ARG_GROUP
  it contains. If the ARG_FILE does not exist or the ARGSPEC does not yet
  contain a colon, then fall back to standard shell filename completion by
  returning an empty list.

  Args:
    prefix: the partial ARGSPEC string typed by the user so far.
    parsed_args: the argparse.Namespace for all args parsed so far.
    **kwargs: keyword args, not used.

  Returns:
    The list of all ARG_FILE:ARG_GROUP strings which match the prefix.
  """
  try:
    arg_file, group_prefix = _SplitArgFileAndGroup(prefix)
  except exceptions.InvalidArgException:
    return []
  try:
    groups = list(_ReadArgGroupsFromFile(arg_file).keys())
  except yaml.FileLoadError:
    return []
  return [(arg_file + ':' + g) for g in groups if g.startswith(group_prefix)]
