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

"""Helpers to load commands from the filesystem."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import importlib
import os
import re

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import command_release_tracks
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import pkg_resources

from ruamel import yaml
import six

PARTIALS_ATTRIBUTE = '_PARTIALS_'
PARTIALS_DIR = '_partials'


class CommandLoadFailure(Exception):
  """An exception for when a command or group module cannot be imported."""

  def __init__(self, command, root_exception):
    self.command = command
    self.root_exception = root_exception
    super(CommandLoadFailure, self).__init__(
        'Problem loading {command}: {issue}.'.format(
            command=command, issue=six.text_type(root_exception)))


class LayoutException(Exception):
  """An exception for when a command or group .py file has the wrong types."""


class ReleaseTrackNotImplementedException(Exception):
  """An exception for when a command or group does not support a release track.
  """


class YamlCommandTranslator(six.with_metaclass(abc.ABCMeta, object)):
  """An interface to implement when registering a custom command loader."""

  @abc.abstractmethod
  def Translate(self, path, command_data):
    """Translates a yaml command into a calliope command.

    Args:
      path: [str], A list of group names that got us down to this command group
        with respect to the CLI itself.  This path should be used for things
        like error reporting when a specific element in the tree needs to be
        referenced.
      command_data: dict, The parsed contents of the command spec from the
        yaml file that corresponds to the release track being loaded.

    Returns:
      calliope.base.Command, A command class (not instance) that
      implements the spec.
    """
    pass


def FindSubElements(impl_paths, path):
  """Find all the sub groups and commands under this group.

  Args:
    impl_paths: [str], A list of file paths to the command implementation for
      this group.
    path: [str], A list of group names that got us down to this command group
      with respect to the CLI itself.  This path should be used for things
      like error reporting when a specific element in the tree needs to be
      referenced.

  Raises:
    CommandLoadFailure: If the command is invalid and cannot be loaded.
    LayoutException: if there is a command or group with an illegal name.

  Returns:
    ({str: [str]}, {str: [str]), A tuple of groups and commands found where each
    item is a mapping from name to a list of paths that implement that command
    or group. There can be multiple paths because a command or group could be
    implemented in both python and yaml (for different release tracks).
  """
  if len(impl_paths) > 1:
    raise CommandLoadFailure(
        '.'.join(path),
        Exception('Command groups cannot be implemented in yaml'))
  impl_path = impl_paths[0]
  groups, commands = pkg_resources.ListPackage(
      impl_path, extra_extensions=['.yaml'])
  return (_GenerateElementInfo(impl_path, groups),
          _GenerateElementInfo(impl_path, commands))


def _GenerateElementInfo(impl_path, names):
  """Generates the data a group needs to load sub elements.

  Args:
    impl_path: The file path to the command implementation for this group.
    names: [str], The names of the sub groups or commands found in the group.

  Raises:
    LayoutException: if there is a command or group with an illegal name.

  Returns:
    {str: [str], A mapping from name to a list of paths that implement that
    command or group. There can be multiple paths because a command or group
    could be implemented in both python and yaml (for different release tracks).
  """
  elements = {}
  for name in names:
    if re.search('[A-Z]', name):
      raise LayoutException(
          'Commands and groups cannot have capital letters: {0}.'.format(name))
    cli_name = name[:-5] if name.endswith('.yaml') else name
    sub_path = os.path.join(impl_path, name)

    existing = elements.setdefault(cli_name, [])
    existing.append(sub_path)
  return elements


def LoadCommonType(impl_paths, path, release_track,
                   construction_id, is_command, yaml_command_translator=None):
  """Loads a calliope command or group from a file.

  Args:
    impl_paths: [str], A list of file paths to the command implementation for
      this group or command.
    path: [str], A list of group names that got us down to this command group
      with respect to the CLI itself.  This path should be used for things
      like error reporting when a specific element in the tree needs to be
      referenced.
    release_track: ReleaseTrack, The release track that we should load.
    construction_id: str, A unique identifier for the CLILoader that is
      being constructed.
    is_command: bool, True if we are loading a command, False to load a group.
    yaml_command_translator: YamlCommandTranslator, An instance of a translator
      to use to load the yaml data.

  Raises:
    CommandLoadFailure: If the command is invalid and cannot be loaded.

  Returns:
    The base._Common class for the command or group.
  """
  implementations = _GetAllImplementations(
      impl_paths, path, construction_id, is_command, yaml_command_translator)
  return _ExtractReleaseTrackImplementation(
      impl_paths[0], release_track, implementations)()


def Cache(func):
  cached_results = {}
  def ReturnCachedOrCallFunc(*args):
    try:
      return cached_results[args]
    except KeyError:
      result = func(*args)
      cached_results[args] = result
      return result
  return ReturnCachedOrCallFunc


@Cache
def _SafeLoadYamlFile(path):
  return yaml.safe_load(pkg_resources.GetResourceFromFile(path))


@Cache
def _CustomLoadYamlFile(path):
  return CreateYamlLoader(path).load(pkg_resources.GetResourceFromFile(path))


def _GetAllImplementations(impl_paths, path, construction_id, is_command,
                           yaml_command_translator):
  """Gets all the release track command implementations.

  Can load both python and yaml modules.

  Args:
    impl_paths: [str], A list of file paths to the command implementation for
      this group or command.
    path: [str], A list of group names that got us down to this command group
      with respect to the CLI itself.  This path should be used for things
      like error reporting when a specific element in the tree needs to be
      referenced.
    construction_id: str, A unique identifier for the CLILoader that is
      being constructed.
    is_command: bool, True if we are loading a command, False to load a group.
    yaml_command_translator: YamlCommandTranslator, An instance of a translator
      to use to load the yaml data.

  Raises:
    CommandLoadFailure: If the command is invalid and cannot be loaded.

  Returns:
    [(func->base._Common, [base.ReleaseTrack])], A list of tuples that can be
    passed to _ExtractReleaseTrackImplementation. Each item in this list
    represents a command implementation. The first element is a function that
    returns the implementation, and the second element is a list of release
    tracks it is valid for.
  """
  implementations = []
  for impl_file in impl_paths:
    if impl_file.endswith('.yaml'):
      if not is_command:
        raise CommandLoadFailure(
            '.'.join(path),
            Exception('Command groups cannot be implemented in yaml'))
      if _IsCommandWithPartials(impl_file, path):
        data = _LoadCommandWithPartials(impl_file, path)
      else:
        data = _CustomLoadYamlFile(impl_file)
      implementations.extend((_ImplementationsFromYaml(
          path, data, yaml_command_translator)))
    else:
      module = _GetModuleFromPath(impl_file, path, construction_id)
      implementations.extend(_ImplementationsFromModule(
          module.__file__, list(module.__dict__.values()),
          is_command=is_command))
  return implementations


def _IsCommandWithPartials(impl_file, path):
  """Checks if the YAML file is a command with partials.

  Args:
    impl_file: file path to the main YAML command implementation.
    path: [str], A list of group names that got us down to this command group
      with respect to the CLI itself.  This path should be used for things
      like error reporting when a specific element in the tree needs to be
      referenced.

  Raises:
    CommandLoadFailure: If the command is invalid and should not be loaded.

  Returns:
    Whether or not it is a valid command with partials to load.
  """
  found_partial_token = False
  with pkg_resources.GetFileTextReaderByLine(impl_file) as file:
    for line in file:
      line = line.strip()
      if not line or line.startswith('#'):
        continue
      if line == f'{PARTIALS_ATTRIBUTE}: true':
        found_partial_token = True
      elif found_partial_token:
        raise CommandLoadFailure(
            '.'.join(path),
            Exception(
                f'Command with {PARTIALS_ATTRIBUTE} attribute cannot have'
                ' extra content'
            ),
        )
      else:
        break

  return found_partial_token


def _LoadCommandWithPartials(impl_file, path):
  """Loads all YAML partials for a command with partials based on conventions.

  Partial files are loaded using _CustomLoadYamlFile as normal YAML commands.

  Conventions:
  - Partials should be placed in subfolder `_partials`.
  - File names of partials should match the main command name and follow this
  format: _[command_name]_[version|release_track].yaml
  - Release tracks should not be duplicatd across all partials.

  Args:
    impl_file: file path to the main YAML command implementation.
    path: [str], A list of group names that got us down to this command group
      with respect to the CLI itself.  This path should be used for things
      like error reporting when a specific element in the tree needs to be
      referenced.

  Returns:
    List with data loaded from partial YAML files for the main command.
  """
  file_name = os.path.basename(impl_file)
  command_name = file_name[:-5]  # strip .yaml
  partials_dir = os.path.join(os.path.dirname(impl_file), PARTIALS_DIR)
  partial_files = pkg_resources.GetFilesFromDirectory(
      partials_dir, f'_{command_name}_*.yaml'
  )
  command_data_list = []
  for partial_file in partial_files:
    command_data_list.extend(_CustomLoadYamlFile(partial_file))

  _ValidateCommandWithPartials(command_data_list, path)
  return command_data_list


def _ValidateCommandWithPartials(command_data_list, path):
  """Validates that the command with partials do not have duplicated tracks.

  Args:
    command_data_list: List with data loaded from all YAML partials.
    path: [str], A list of group names that got us down to this command group
      with respect to the CLI itself.  This path should be used for things
      like error reporting when a specific element in the tree needs to be
      referenced.

  Raises:
    CommandLoadFailure: If the command is invalid and should not be loaded.
  """
  release_tracks = set()
  for command_data in command_data_list:
    for release_track in command_data['release_tracks']:
      if release_track in release_tracks:
        raise CommandLoadFailure(
            '.'.join(path),
            Exception(
                'Command with partials cannot have duplicated release tracks.'
                f' Found multiple [{release_track}s]'
            ))
      else:
        release_tracks.add(release_track)


def CreateYamlLoader(impl_path):
  """Creates a custom yaml loader that handles includes from common data.

  Args:
    impl_path: str, The path to the file we are loading data from.

  Returns:
    yaml.Loader, A yaml loader to use.
  """
  common_file_path = os.path.join(os.path.dirname(impl_path), '__init__.yaml')
  common_data = None
  try:
    common_data = _SafeLoadYamlFile(common_file_path)
  except IOError:
    pass

  class Constructor(yaml.Constructor):
    """A custom yaml constructor.

    It adds 2 different import capabilities. Assuming __init__.yaml has the
    contents:

    foo:
      a: b
      c: d

    baz:
      - e: f
      - g: h

    The first uses a custom constructor to insert data into your current file,
    so:

    bar: !COMMON foo.a

    results in:

    bar: b

    The second mechanism overrides construct_mapping and construct_sequence to
    post process the data and replace the merge macro with keys from the other
    file. We can't use the custom constructor for this as well because the
    merge key type in yaml is processed before custom constructors which makes
    importing and merging not possible. So:

    bar:
      _COMMON_: foo
      i: j

    results in:

    bar:
      a: b
      c: d
      i: j

    This can also be used to merge list contexts, so:

    bar:
      - _COMMON_baz
      - i: j

    results in:

    bar:
      - e: f
      - g: h
      - i: j

    You may also use the !REF and _REF_ directives in the same way. Instead of
    pulling from the common file, they can pull from an arbitrary yaml file
    somewhere in the googlecloudsdk tree. The syntax looks like:

    bar: !REF googlecloudsdk.foo.bar:a.b.c

    This will load googlecloudsdk/foo/bar.yaml and from that file return the
    a.b.c nested attribute.
    """

    INCLUDE_COMMON_MACRO = '!COMMON'
    MERGE_COMMON_MACRO = '_COMMON_'
    INCLUDE_REF_MACRO = '!REF'
    MERGE_REF_MACRO = '_REF_'

    def construct_mapping(self, *args, **kwargs):
      data = super(Constructor, self).construct_mapping(*args, **kwargs)
      data = self._ConstructMappingHelper(Constructor.MERGE_COMMON_MACRO,
                                          self._GetCommonData, data)
      return self._ConstructMappingHelper(Constructor.MERGE_REF_MACRO,
                                          self._GetRefData, data)

    def _ConstructMappingHelper(self, macro, source_func, data):
      attribute_path = data.pop(macro, None)
      if not attribute_path:
        return data

      modified_data = {}
      for path in attribute_path.split(','):
        modified_data.update(source_func(path))
      # Add the explicit data last so it can override the imports.
      modified_data.update(data)
      return modified_data

    def construct_sequence(self, *args, **kwargs):
      data = super(Constructor, self).construct_sequence(*args, **kwargs)
      data = self._ConstructSequenceHelper(Constructor.MERGE_COMMON_MACRO,
                                           self._GetCommonData, data)
      return self._ConstructSequenceHelper(Constructor.MERGE_REF_MACRO,
                                           self._GetRefData, data)

    def _ConstructSequenceHelper(self, macro, source_func, data):
      new_list = []
      for i in data:
        if isinstance(i, six.string_types) and i.startswith(macro):
          attribute_path = i[len(macro):]
          for path in attribute_path.split(','):
            new_list.extend(source_func(path))
        else:
          new_list.append(i)
      return new_list

    def IncludeCommon(self, node):
      attribute_path = self.construct_scalar(node)
      return self._GetCommonData(attribute_path)

    def IncludeRef(self, node):
      attribute_path = self.construct_scalar(node)
      return self._GetRefData(attribute_path)

    def _GetCommonData(self, attribute_path):
      if not common_data:
        raise LayoutException(
            'Command [{}] references [common command] data but it does not '
            'exist.'.format(impl_path))
      return self._GetAttribute(common_data, attribute_path, 'common command')

    def _GetRefData(self, path):
      """Loads the YAML data from the given reference.

      A YAML reference must refer to a YAML file and an attribute within that
      file to extract.

      Args:
        path: str, The path of the YAML file to import. It must be in the
          form of: package.module:attribute.attribute, where the module path is
          separated from the sub attributes within the YAML by a ':'.

      Raises:
        LayoutException: If the given module or attribute cannot be loaded.

      Returns:
        The referenced YAML data.
      """
      parts = path.split(':')
      if len(parts) != 2:
        raise LayoutException(
            'Invalid Yaml reference: [{}]. References must be in the format: '
            'path(.path)+:attribute(.attribute)*'.format(path))
      path_segments = parts[0].split('.')
      try:
        root_module = importlib.import_module(path_segments[0])
        yaml_path = os.path.join(
            os.path.dirname(root_module.__file__), *path_segments[1:]) + '.yaml'
        data = _SafeLoadYamlFile(yaml_path)
      except (ImportError, IOError) as e:
        raise LayoutException(
            'Failed to load Yaml reference file [{}]: {}'.format(parts[0], e))

      return self._GetAttribute(data, parts[1], yaml_path)

    def _GetAttribute(self, data, attribute_path, location):
      value = data
      for attribute in attribute_path.split('.'):
        value = value.get(attribute, None)
        if not value:
          raise LayoutException(
              'Command [{}] references [{}] data attribute [{}] in '
              'path [{}] but it does not exist.'
              .format(impl_path, location, attribute, attribute_path))
      return value

  loader = yaml.YAML()
  loader.Constructor = Constructor
  loader.constructor.add_constructor(Constructor.INCLUDE_COMMON_MACRO,
                                     Constructor.IncludeCommon)
  loader.constructor.add_constructor(Constructor.INCLUDE_REF_MACRO,
                                     Constructor.IncludeRef)
  return loader


def _GetModuleFromPath(impl_file, path, construction_id):
  """Import the module and dig into it to return the namespace we are after.

  Import the module relative to the top level directory.  Then return the
  actual module corresponding to the last bit of the path.

  Args:
    impl_file: str, The path to the file this was loaded from (for error
      reporting).
    path: [str], A list of group names that got us down to this command group
      with respect to the CLI itself.  This path should be used for things
      like error reporting when a specific element in the tree needs to be
      referenced.
    construction_id: str, A unique identifier for the CLILoader that is
      being constructed.

  Returns:
    The imported module.
  """
  # Make sure this module name never collides with any real module name.
  # Use the CLI naming path, so values are always unique.
  name_to_give = '__calliope__command__.{construction_id}.{name}'.format(
      construction_id=construction_id,
      name='.'.join(path).replace('-', '_'))
  try:
    return pkg_resources.GetModuleFromPath(name_to_give, impl_file)
  # pylint:disable=broad-except, We really do want to catch everything here,
  # because if any exceptions make it through for any single command or group
  # file, the whole CLI will not work. Instead, just log whatever it is.
  except Exception as e:
    exceptions.reraise(CommandLoadFailure('.'.join(path), e))


def _ImplementationsFromModule(mod_file, module_attributes, is_command):
  """Gets all the release track command implementations from the module.

  Args:
    mod_file: str, The __file__ attribute of the module resulting from
      importing the file containing a command.
    module_attributes: The __dict__.values() of the module.
    is_command: bool, True if we are loading a command, False to load a group.

  Raises:
    LayoutException: If there is not exactly one type inheriting CommonBase.

  Returns:
    [(func->base._Common, [base.ReleaseTrack])], A list of tuples that can be
    passed to _ExtractReleaseTrackImplementation. Each item in this list
    represents a command implementation. The first element is a function that
    returns the implementation, and the second element is a list of release
    tracks it is valid for.
  """
  commands = []
  groups = []

  # Collect all the registered groups and commands.
  for command_or_group in module_attributes:
    if getattr(command_or_group, 'IS_COMMAND', False):
      commands.append(command_or_group)
    elif getattr(command_or_group, 'IS_COMMAND_GROUP', False):
      groups.append(command_or_group)

  if is_command:
    if groups:
      # Ensure that there are no groups if we are expecting a command.
      raise LayoutException(
          'You cannot define groups [{0}] in a command file: [{1}]'
          .format(', '.join([g.__name__ for g in groups]), mod_file))
    if not commands:
      # Make sure we found a command.
      raise LayoutException('No commands defined in file: [{0}]'.format(
          mod_file))
    commands_or_groups = commands
  else:
    # Ensure that there are no commands if we are expecting a group.
    if commands:
      raise LayoutException(
          'You cannot define commands [{0}] in a command group file: [{1}]'
          .format(', '.join([c.__name__ for c in commands]), mod_file))
    if not groups:
      # Make sure we found a group.
      raise LayoutException('No command groups defined in file: [{0}]'.format(
          mod_file))
    commands_or_groups = groups

  # pylint:disable=undefined-loop-variable, Linter is just wrong here.
  # We need to use a default param on the lambda so that it captures the value
  # of the variable at the time in the loop or else the closure will just have
  # the last value that was iterated on.
  return [(lambda c=c: c, c.ValidReleaseTracks()) for c in commands_or_groups]


def _ImplementationsFromYaml(path, data, yaml_command_translator):
  """Gets all the release track command implementations from the yaml file.

  Args:
    path: [str], A list of group names that got us down to this command group
      with respect to the CLI itself.  This path should be used for things
      like error reporting when a specific element in the tree needs to be
      referenced.
    data: dict, The loaded yaml data.
    yaml_command_translator: YamlCommandTranslator, An instance of a translator
      to use to load the yaml data.

  Raises:
    CommandLoadFailure: If the command is invalid and cannot be loaded.

  Returns:
    [(func->base._Common, [base.ReleaseTrack])], A list of tuples that can be
    passed to _ExtractReleaseTrackImplementation. Each item in this list
    represents a command implementation. The first element is a function that
    returns the implementation, and the second element is a list of release
    tracks it is valid for.
  """
  if not yaml_command_translator:
    raise CommandLoadFailure(
        '.'.join(path),
        Exception('No yaml command translator has been registered'))

  # pylint:disable=undefined-loop-variable, Linter is just wrong here.
  # We need to use a default param on the lambda so that it captures the value
  # of the variable at the time in the loop or else the closure will just have
  # the last value that was iterated on.
  implementations = [
      (lambda i=i: yaml_command_translator.Translate(path, i),
       {base.ReleaseTrack.FromId(t) for t in i.get('release_tracks', [])})
      for i in command_release_tracks.SeparateDeclarativeCommandTracks(data)]
  return implementations


def _ExtractReleaseTrackImplementation(
    impl_file, expected_track, implementations):
  """Validates and extracts the correct implementation of the command or group.

  Args:
    impl_file: str, The path to the file this was loaded from (for error
      reporting).
    expected_track: base.ReleaseTrack, The release track we are trying to load.
    implementations: [(func->base._Common, [base.ReleaseTrack])], A list of
    tuples where each item in this list represents a command implementation. The
    first element is a function that returns the implementation, and the second
    element is a list of release tracks it is valid for.

  Raises:
    LayoutException: If there is not exactly one type inheriting
        CommonBase.
    ReleaseTrackNotImplementedException: If there is no command or group
      implementation for the request release track.

  Returns:
    object, The single implementation that matches the expected release track.
  """
  # We found a single thing, if it's valid for this track, return it.
  if len(implementations) == 1:
    impl, valid_tracks = implementations[0]
    # If there is a single thing defined, and it does not declare any valid
    # tracks, just assume it is enabled for all tracks that it's parent is.
    if not valid_tracks or expected_track in valid_tracks:
      return impl
    raise ReleaseTrackNotImplementedException(
        'No implementation for release track [{0}] for element: [{1}]'
        .format(expected_track.id, impl_file))

  # There was more than one thing found, make sure there are no conflicts.
  implemented_release_tracks = set()
  for impl, valid_tracks in implementations:
    # When there are multiple definitions, they need to explicitly register
    # their track to keep things sane.
    if not valid_tracks:
      raise LayoutException(
          'Multiple implementations defined for element: [{0}]. Each must '
          'explicitly declare valid release tracks.'.format(impl_file))
    # Make sure no two classes define the same track.
    duplicates = implemented_release_tracks & valid_tracks
    if duplicates:
      raise LayoutException(
          'Multiple definitions for release tracks [{0}] for element: [{1}]'
          .format(', '.join([six.text_type(d) for d in duplicates]), impl_file))
    implemented_release_tracks |= valid_tracks

  valid_commands_or_groups = [impl for impl, valid_tracks in implementations
                              if expected_track in valid_tracks]
  # We know there is at most 1 because of the above check.
  if len(valid_commands_or_groups) != 1:
    raise ReleaseTrackNotImplementedException(
        'No implementation for release track [{0}] for element: [{1}]'
        .format(expected_track.id, impl_file))

  return valid_commands_or_groups[0]
