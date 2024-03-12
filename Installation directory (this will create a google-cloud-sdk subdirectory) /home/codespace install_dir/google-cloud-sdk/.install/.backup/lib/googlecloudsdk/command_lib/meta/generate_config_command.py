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
"""Utilities for meta generate-config-commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import os.path

from googlecloudsdk.core import branding
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import name_parsing
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files
from mako import runtime
from mako import template

_COMMAND_PATH_COMPONENTS = ('third_party', 'py', 'googlecloudsdk', 'surface')
_SPEC_PATH_COMPONENTS = ('cloud', 'sdk', 'surface_specs', 'gcloud')
_TEST_PATH_COMPONENTS = ('third_party', 'py', 'googlecloudsdk', 'tests', 'unit',
                         'surface')


class CollectionNotFoundError(core_exceptions.Error):
  """Exception for attempts to generate unsupported commands."""

  def __init__(self, collection):
    message = '{collection} collection is not found'.format(
        collection=collection)
    super(CollectionNotFoundError, self).__init__(message)


def WriteConfigYaml(collection, output_root, resource_data, release_tracks,
                    enable_overwrites):
  """Writes <comand|spec|test> declarative command files for collection.

  Args:
    collection: Name of collection to generate commands for.
    output_root: Path to the root of the directory. Should just be $PWD when
      executing the `meta generate-config-commands` command.
    resource_data: Resource map data for the given resource.
    release_tracks: Release tracks to generate files for.
    enable_overwrites: True to enable overwriting of existing config export
      files.
  """
  log.status.Print('[{}]:'.format(collection))
  collection_info = resources.REGISTRY.GetCollectionInfo(collection)
  _RenderSurfaceSpecFiles(output_root, resource_data,
                          collection_info, release_tracks, enable_overwrites)
  _RenderCommandGroupInitFile(output_root, resource_data,
                              collection_info, release_tracks,
                              enable_overwrites)
  _RenderCommandFile(output_root, resource_data, collection_info,
                     release_tracks, enable_overwrites)
  _RenderTestFiles(output_root, resource_data, collection_info,
                   enable_overwrites)


def _RenderFile(file_path,
                file_template,
                context,
                enable_overwrites):
  """Renders a file to given path using the provided template and context."""
  render_file = False
  overwrite = False
  if not os.path.exists(file_path):
    render_file = True
  elif enable_overwrites:
    render_file = True
    overwrite = True

  if render_file:
    log.status.Print(' -- Generating: File: [{}], Overwrite: [{}]'.format(
        file_path, overwrite))
    with files.FileWriter(file_path, create_path=True) as f:
      ctx = runtime.Context(f, **context)
      file_template.render_context(ctx)
  else:
    log.status.Print(' >> Skipped: File: [{}] --'.format(file_path))


def _WriteFile(file_path, file_contents, enable_overwrites):
  if not os.path.exists(file_path) or enable_overwrites:
    with files.FileWriter(file_path, create_path=True) as f:
      f.write(file_contents)


def _BuildFilePath(output_root, sdk_path, home_directory, *argv):
  path_args = (output_root,) + sdk_path + tuple(
      home_directory.split('.')) + tuple(
          path_component for path_component in argv)
  file_path = os.path.join(*path_args)
  return file_path


def _BuildTemplate(template_file_name):
  dir_name = os.path.dirname(__file__)
  template_path = os.path.join(dir_name, 'config_export_templates',
                               template_file_name)
  file_template = template.Template(filename=template_path)
  return file_template


def _RenderCommandGroupInitFile(output_root, resource_data, collection_info,
                                release_tracks, enable_overwrites):
  file_path = _BuildFilePath(output_root, _COMMAND_PATH_COMPONENTS,
                             resource_data.home_directory, 'config',
                             '__init__.py')
  file_template = _BuildTemplate('command_group_init_template.tpl')
  context = _BuildCommandGroupInitContext(collection_info, release_tracks,
                                          resource_data)
  _RenderFile(file_path, file_template, context, enable_overwrites)


def _RenderCommandFile(output_root, resource_data, collection_info,
                       release_tracks, enable_overwrites):
  file_path = _BuildFilePath(output_root, _COMMAND_PATH_COMPONENTS,
                             resource_data.home_directory,
                             'config', 'export.yaml')
  file_template = _BuildTemplate('command_template.tpl')
  context = _BuildCommandContext(collection_info, release_tracks, resource_data)
  _RenderFile(
      file_path,
      file_template,
      context,
      enable_overwrites)


def _RenderSurfaceSpecFiles(output_root, resource_data, collection_info,
                            release_tracks, enable_overwrites):
  """Render surface spec files (both GROUP.yaml and command spec file.)"""
  context = _BuildSurfaceSpecContext(collection_info, release_tracks,
                                     resource_data)

  # Render GROUP.yaml
  group_template = _BuildTemplate('surface_spec_group_template.tpl')
  group_file_path = _BuildFilePath(output_root, _SPEC_PATH_COMPONENTS,
                                   resource_data.home_directory, 'config',
                                   'GROUP.yaml')
  _RenderFile(group_file_path, group_template, context, enable_overwrites)

  # Render spec file
  spec_path = _BuildFilePath(output_root, _SPEC_PATH_COMPONENTS,
                             resource_data.home_directory, 'config',
                             'export.yaml')
  spec_template = _BuildTemplate('surface_spec_template.tpl')
  _RenderFile(spec_path, spec_template, context, enable_overwrites)


def _RenderTestFiles(output_root, resource_data, collection_info,
                     enable_overwrites):
  """Render python test file using template and context."""
  context = _BuildTestContext(collection_info, resource_data)

  # Render init file.
  init_path = _BuildFilePath(output_root, _TEST_PATH_COMPONENTS,
                             resource_data.home_directory, '__init__.py')
  init_template = _BuildTemplate('python_blank_init_template.tpl')
  _RenderFile(init_path, init_template, context, enable_overwrites)

  # Render test file.
  test_path = _BuildFilePath(output_root, _TEST_PATH_COMPONENTS,
                             resource_data.home_directory,
                             'config_export_test.py')
  test_template = _BuildTemplate('unit_test_template.tpl')
  _RenderFile(test_path, test_template, context, enable_overwrites)


def _BuildCommandGroupInitContext(collection_info, release_tracks,
                                  resource_data):
  """Makes context dictionary for config init file template rendering."""
  init_dict = {}
  init_dict['utf_encoding'] = '-*- coding: utf-8 -*- #'
  init_dict['current_year'] = datetime.datetime.now().year

  init_dict['branded_api_name'] = branding.Branding().get(
      collection_info.api_name, collection_info.api_name.capitalize())
  init_dict[
      'singular_resource_name_with_spaces'] = name_parsing.convert_collection_name_to_delimited(
          collection_info.name)

  release_track_string = ''
  for x, release_track in enumerate(release_tracks):
    release_track_string += 'base.ReleaseTrack.{}'.format(release_track.upper())
    if x != len(release_tracks) - 1:
      release_track_string += ', '

  init_dict['release_tracks'] = release_track_string

  if 'group_category' in resource_data:
    init_dict['group_category'] = resource_data.group_category

  return init_dict


def _BuildCommandContext(collection_info, release_tracks, resource_data):
  """Makes context dictionary for config export command template rendering."""
  command_dict = {}

  # apiname.collectionNames
  command_dict['collection_name'] = collection_info.name
  # Branded service name
  command_dict['branded_api_name'] = branding.Branding().get(
      collection_info.api_name, collection_info.api_name.capitalize())

  # collection names
  command_dict[
      'plural_resource_name_with_spaces'] = name_parsing.convert_collection_name_to_delimited(
          collection_info.name, make_singular=False)

  # collection name
  command_dict[
      'singular_name_with_spaces'] = name_parsing.convert_collection_name_to_delimited(
          collection_info.name)

  # Collection name
  command_dict['singular_capitalized_name'] = command_dict[
      'singular_name_with_spaces'].capitalize()

  if 'resource_spec_path' in resource_data:
    command_dict[
        'resource_spec_path'] = resource_data.resource_spec_path
  else:
    resource_spec_name = command_dict['singular_name_with_spaces'].replace(
        ' ', '_')
    resource_spec_dir = resource_data.home_directory.split('.')[0]
    command_dict['resource_spec_path'] = '{}.resources:{}'.format(
        resource_spec_dir, resource_spec_name)

  # my-collection-name
  command_dict['resource_argument_name'] = _MakeResourceArgName(
      collection_info.name)

  # Release tracks
  command_dict['release_tracks'] = _GetReleaseTracks(release_tracks)

  # "a" or "an" for correct grammar.
  api_a_or_an = 'a'
  if command_dict['branded_api_name'][0] in 'aeiou':
    api_a_or_an = 'an'
  command_dict['api_a_or_an'] = api_a_or_an

  resource_a_or_an = 'a'
  if command_dict['singular_name_with_spaces'][0] in 'aeiou':
    resource_a_or_an = 'an'
  command_dict['resource_a_or_an'] = resource_a_or_an

  return command_dict


def _BuildSurfaceSpecContext(collection_info, release_tracks, resource_data):
  """Makes context dictionary for surface spec rendering."""
  surface_spec_dict = {}
  surface_spec_dict['release_tracks'] = _GetReleaseTracks(release_tracks)
  # collection_name

  if 'surface_spec_resource_name' in resource_data:
    surface_spec_dict[
        'surface_spec_resource_arg'] = resource_data.surface_spec_resource_name
  elif 'resource_spec_path' in resource_data:
    surface_spec_dict[
        'surface_spec_resource_arg'] = resource_data.resource_spec_path.split(
            ':')[-1].upper()
  else:
    surface_spec_dict[
        'surface_spec_resource_arg'] = _MakeSurfaceSpecResourceArg(
            collection_info)
  return surface_spec_dict


def _BuildTestContext(collection_info, resource_data):
  """Makes context dictionary for config export est files rendering."""
  test_dict = {}
  test_dict['utf_encoding'] = '-*- coding: utf-8 -*- #'
  test_dict['current_year'] = datetime.datetime.now().year
  resource_arg_flags = _MakeResourceArgFlags(collection_info, resource_data)
  resource_arg_positional = _MakeResourceArgName(collection_info.name)
  test_dict['test_command_arguments'] = ' '.join(
      [resource_arg_positional, resource_arg_flags])
  test_dict['pylint_disable'] = ''
  if len(test_dict['test_command_arguments']) > 56:
    test_dict['pylint_disable'] = '  # pylint:disable=line-too-long'
  test_dict['full_collection_name'] = '.'.join(
      [collection_info.api_name, collection_info.name])
  test_dict['test_command_string'] = _MakeTestCommandString(
      resource_data.home_directory)
  return test_dict


def _GetReleaseTracks(release_tracks):
  """Returns a string representation of release tracks.

  Args:
    release_tracks: API versions to generate release tracks for.
  """
  release_tracks_normalized = '[{}]'.format(', '.join(
      [track.upper() for track in sorted(release_tracks)]))
  return release_tracks_normalized


def _MakeSurfaceSpecResourceArg(collection_info):
  """Makes resource arg name for surface specification context."""
  return name_parsing.convert_collection_name_to_delimited(
      collection_info.name, delimiter='_').upper()


def _MakeTestCommandString(home_directory):
  """Makes gcloud command string for test execution."""
  return '{} config export'.format(
      home_directory.replace('_', '-').replace('.', ' '))


def _MakeResourceArgName(collection_name):
  resource_arg_name = 'my-{}'.format(
      name_parsing.convert_collection_name_to_delimited(
          collection_name, delimiter='-'))
  return resource_arg_name


def _MakeResourceArgFlags(collection_info, resource_data):
  """Makes input resource arg flags for config export test file."""
  resource_arg_flags = []

  if getattr(collection_info, 'flat_paths'):
    # Path components will generally be stored in the '' key of flat_paths dict.
    if '' in getattr(collection_info, 'flat_paths', None):
      components = collection_info.flat_paths[''].split('/')

      # Remove surrounding brackets and 'Id' suffix from path component
      resource_arg_flag_names = [
          component.replace('{', '').replace('Id}', '')
          for component in components
          if '{' in component
      ]

      # Remove project component as this isn't needed to specify test args.
      filtered_resource_arg_flag_names = [
          resource_arg for resource_arg in resource_arg_flag_names
          if 'project' not in resource_arg
      ]

      # Get parent components, convert from camelcase to dash delimited
      # e.g. fooBar -> foo-bar
      formatted_resource_arg_flag_names = []
      for resource_arg in filtered_resource_arg_flag_names[:-1]:
        formatted_name = name_parsing.split_name_on_capitals(
            name_parsing.singularize(resource_arg),
            delimiter='-').lower()
        formatted_resource_arg_flag_names.append(formatted_name)

      # Override component name using `resource_attribute_renames` field of
      # declarative map if specified.
      if 'resource_attribute_renames' in resource_data:
        for original_attr_name, new_attr_name in resource_data.resource_attribute_renames.items(
        ):
          for x in range(len(formatted_resource_arg_flag_names)):
            if formatted_resource_arg_flag_names[x] == original_attr_name:
              formatted_resource_arg_flag_names[x] = new_attr_name

      # Format components into command string for unit tests.
      resource_arg_flags = [
          '--{param}=my-{param}'.format(param=resource_arg)
          for resource_arg in formatted_resource_arg_flag_names
      ]

  elif getattr(collection_info, 'params', None):
    for param in collection_info.params:
      modified_param_name = param

      # Remove 'Id' suffix.
      if modified_param_name[-2:] == 'Id':
        modified_param_name = modified_param_name[:-2]

      # Convert component name from camelCase to dash delimited
      # e.g. fooBar -> foo-bar
      modified_param_name = name_parsing.convert_collection_name_to_delimited(
          modified_param_name, delimiter='-', make_singular=False)

      # If component name is not positional resource name, `project`, or `name`
      # format for unit test.
      if (modified_param_name
          not in (name_parsing.convert_collection_name_to_delimited(
              collection_info.name, delimiter='-'), 'project', 'name')):
        resource_arg = '--{param}=my-{param}'.format(param=modified_param_name)
        resource_arg_flags.append(resource_arg)

  return ' '.join(resource_arg_flags)
