# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utilities for meta generate-command.

Contains utilities for file writing and template selection.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os.path
import re

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from mako import runtime
from mako import template

TEMPLATE_SUFFIX = '_template.tpl'
CRUD_TEMPLATES = frozenset({
    'create_template.tpl', 'delete_template.tpl', 'describe_template.tpl',
    'get_iam_policy_template.tpl', 'list_template.tpl',
    'set_iam_policy_template.tpl'
})


class CollectionNotFoundError(core_exceptions.Error):
  """Exception for attempts to generate unsupported commands."""

  def __init__(self, collection):
    message = '{collection} collection is not found'.format(
        collection=collection)
    super(CollectionNotFoundError, self).__init__(message)


def WriteAllYaml(collection_name, output_dir):
  """Writes declarative YAML file for all supported command types.

  Args:
    collection_name: name of collection to generate commands for.
    output_dir: path to the directory where generated YAML files will be
      written.
  """
  collection_dict = _MakeCollectionDict(collection_name)
  api_message_module = apis.GetMessagesModule(collection_dict['api_name'],
                                              collection_dict['api_version'])
  api_dict = _MakeApiDict(api_message_module, collection_dict)
  collection_dict.update(api_dict)
  for command_template in os.listdir(
      os.path.join(os.path.dirname(__file__), 'command_templates')):
    if command_template.split('/')[-1] not in CRUD_TEMPLATES:
      continue
    should_write_test = WriteYaml(command_template, collection_dict, output_dir,
                                  api_message_module)
    if should_write_test:
      WriteScenarioTest(command_template, collection_dict, output_dir)


def WriteYaml(command_tpl_name, collection_dict, output_dir,
              api_message_module):
  """Writes command's YAML file; returns True if file written, else False.

  Args:
    command_tpl_name: name of command template file
    collection_dict: a mapping of collection info to feed template
    output_dir: path to directory in which to write YAML file. If command YAML
    file already exists in this location, the user will be prompted to
    choose to override it or not.
    api_message_module: the API's message module, used to check if command
    type is supported by API
  Returns:
    True if declarative file is written, False if user chooses not to
    override an existing file OR API does not support command type, and no
    new file is written.
  """
  command_name = command_tpl_name[:-len(TEMPLATE_SUFFIX)]
  command_name_capitalized = ''.join(
      [word.capitalize() for word in command_name.split('_')])
  if command_name == 'describe':
    command_name_capitalized = 'Get'
  collection_prefix = ''.join([
      _GetResourceMessageClassName(word)
      for word in collection_dict['collection_name'].split('.')
  ])
  expected_message_name = collection_prefix + command_name_capitalized + 'Request'
  alt_create_message_name = collection_prefix + 'InsertRequest'
  command_supported = False
  for message_name in dir(api_message_module):
    if message_name == expected_message_name or message_name == alt_create_message_name:
      # Note: APIs with nonstandard naming may not have all commands created
      command_supported = True
  command_yaml_tpl = _TemplateFileForCommandPath(command_tpl_name)
  command_filename = command_name + '.yaml'
  full_command_path = os.path.join(output_dir, command_filename)
  file_already_exists = os.path.exists(full_command_path)
  overwrite = False
  if file_already_exists:
    overwrite = console_io.PromptContinue(
        default=False,
        throw_if_unattended=True,
        message='{command_filename} already exists, and continuing will '
        'overwrite the old file. The scenario test skeleton file for this '
        'command will only be generated if you continue'.format(
            command_filename=command_filename))
  if (not file_already_exists or overwrite) and command_supported:
    with files.FileWriter(full_command_path) as f:
      ctx = runtime.Context(f, **collection_dict)
      command_yaml_tpl.render_context(ctx)
    log.status.Print('New file written at ' + full_command_path)
    return True
  else:
    log.status.Print('No new file written at ' + full_command_path)
    return False


def WriteScenarioTest(command_tpl_name, collection_dict, test_output_dir):
  """Writes declarative YAML file for command.

  Args:
    command_tpl_name: name of command template file
    collection_dict: a mapping of collection info to feed template
    test_output_dir: path to directory in which to write YAML test file
  """
  test_tpl = _TemplateFileForCommandPath(
      'scenario_unit_test_template.tpl', test=True)
  test_filename = command_tpl_name[:-len(TEMPLATE_SUFFIX)] + '.scenario.yaml'
  full_test_path = os.path.join(test_output_dir, test_filename)
  with files.FileWriter(full_test_path) as f:
    ctx = runtime.Context(f, **collection_dict)
    test_tpl.render_context(ctx)
  log.status.Print('New test written at ' + full_test_path)


def _TemplateFileForCommandPath(command_template_filename, test=False):
  """Returns Mako template corresping to command_template_filename.

  Args:
    command_template_filename: name of file containing template (no path).
    test: if the template file should be a test file, defaults to False.
  """
  if test:
    template_dir = 'test_templates'
  else:
    template_dir = 'command_templates'
  template_path = os.path.join(
      os.path.dirname(__file__), template_dir,
      command_template_filename)
  return template.Template(filename=template_path)


def _MakeSingular(plural_noun):
  """Returns singular of plural noun.

  Args:
    plural_noun: noun, str, to make .
  """
  return plural_noun[:-1]


def _GetReleaseTracks(api_version):
  """Returns a string representation of release tracks.

  Args:
    api_version: API version to generate release tracks for.
  """
  if 'alpha' in api_version:
    return '[ALPHA]'
  elif 'beta' in api_version:
    return '[ALPHA, BETA]'
  else:
    return '[ALPHA, BETA, GA]'


def _MakeCollectionDict(collection_name):
  """Returns a dictionary of collection attributes from Registry.

  Args:
    collection_name: Name of collection to create dictionary about.
  """
  collection_info = resources.REGISTRY.GetCollectionInfo(collection_name)
  collection_dict = {}
  collection_dict['collection_name'] = collection_name
  collection_dict['api_name'] = collection_info.api_name

  collection_dict['uppercase_api_name'] = collection_info.api_name.capitalize()
  flat_paths = collection_info.flat_paths
  collection_dict['use_relative_name'] = 'false' if not flat_paths else 'true'
  collection_dict['api_version'] = collection_info.api_version
  collection_dict['release_tracks'] = _GetReleaseTracks(
      collection_info.api_version)
  collection_dict['plural_resource_name'] = collection_info.name.split('.')[-1]
  collection_dict['singular_name'] = _MakeSingular(
      collection_dict['plural_resource_name'])
  collection_dict['flags'] = ' '.join([
      '--' + param + '=my-' + param
      for param in collection_info.params
      if (param not in (collection_dict['singular_name'], 'project'))
  ])
  collection_dict['collection_name'] = collection_name
  # the following is a best guess at desired parent for list command scope
  collection_dict[
      'parent'] = 'location' if 'location' in collection_name else 'project'
  return collection_dict


def _MakeApiDict(message_module, collection_dict):
  """Returns a dictionary of API attributes from its messages module.

  Args:
    message_module: the messages module for the API (default version)
    collection_dict: a dictionary containing collection info from registry
  """
  api_dict = {}
  try:
    resource_message = getattr(message_module,
                               _GetResourceMessageClassName(
                                   collection_dict['singular_name']))
    args = [
        field.__dict__['name']
        for field in resource_message.all_fields()
        if field.__dict__['name'] != 'name'
    ]
    api_dict['create_args'] = {
        arg:
        '-'.join([w.lower() for w in re.findall('^[a-z]*|[A-Z][a-z]*', arg)])
        for arg in args
    }  # dict is { camelCaseName: camel-case-name }
  except AttributeError:
    api_dict['create_args'] = {}
    log.status.Print('Cannot find ' +
                     _GetResourceMessageClassName(
                         collection_dict['singular_name']) +
                     ' in message module.')
  return api_dict


def _GetResourceMessageClassName(singular_name):
  """Returns the properly capitalized resource class name."""
  resource_name = singular_name.strip()
  if len(resource_name) > 1:
    return resource_name[0].upper() + resource_name[1:]

  return resource_name.capitalize()
