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
"""Resource Settings command utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.command_lib.resource_settings import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

SETTINGS_PREFIX = 'settings/'
ORGANIZATION = 'organization'
FOLDER = 'folder'
PROJECT = 'project'


def GetMessageFromFile(filepath, message):
  """Returns a message populated from the JSON or YAML file.

  Args:
    filepath: str, A local path to an object specification in JSON or YAML
      format.
    message: messages.Message, The message class to populate from the file.
  """
  file_contents = files.ReadFileContents(filepath)

  try:
    yaml_obj = yaml.load(file_contents)
    json_str = json.dumps(yaml_obj)
  except yaml.YAMLParseError:
    json_str = file_contents

  try:
    return encoding.JsonToMessage(message, json_str)
  except Exception as e:
    raise exceptions.InvalidInputError('Unable to parse file [{}]: {}.'.format(
        filepath, e))


def GetSettingFromArgs(args):
  """Returns the setting from the user-specified arguments.

  A setting has the following syntax: settings/{setting_name}.

  This handles both cases in which the user specifies and does not specify the
  constraint prefix.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  if args.setting_name.startswith(SETTINGS_PREFIX):
    return args.setting_name

  return SETTINGS_PREFIX + args.setting_name


def GetSettingNameFromArgs(args):
  """Returns the setting name from the user-specified arguments.

  This handles both cases in which the user specifies and does not specify the
  setting prefix.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  if args.setting_name.startswith(SETTINGS_PREFIX):
    return args.setting_name[len(SETTINGS_PREFIX):]

  return args.setting_name


def GetSettingNameFromString(setting):
  """Returns the resource id from the setting path.

  A setting path should start with following syntax:
  [organizations|folders|projects]/{resource_id}/settings/{setting_name}/value

  Args:
    setting: A String that contains the setting path
  """
  return setting.split('/')[3]


def GetParentResourceFromArgs(args):
  """Returns the resource from the user-specified arguments.

  A resource has the following syntax:
  [organizations|folders|projects]/{resource_id}.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  resource_id = args.organization or args.folder or args.project

  if args.organization:
    resource_type = ORGANIZATION
  elif args.folder:
    resource_type = FOLDER
  else:
    resource_type = PROJECT

  return '{}/{}'.format(resource_type + 's', resource_id)


def GetParentResourceFromString(setting):
  """Returns the resource from the user-specified arguments.

  A setting path should start with following syntax:
  [organizations|folders|projects]/{resource_id}/settings/{setting_name}/value

  Args:
    setting: A String that contains the setting path
  """

  resource_type = setting.split('/')[0]
  resource_id = setting.split('/')[1]

  return '{}/{}'.format(resource_type, resource_id)


def GetResourceTypeFromString(setting):
  """Returns the resource type from the setting path.

  A setting path should start with following syntax:
  [organizations|folders|projects]/{resource_id}/settings/{setting_name}/value

  Args:
    setting: A String that contains the setting path
  """

  if setting.startswith('organizations/'):
    resource_type = ORGANIZATION
  elif setting.startswith('folders/'):
    resource_type = FOLDER
  elif setting.startswith('projects/'):
    resource_type = PROJECT
  else:
    resource_type = 'invalid'

  return resource_type


def GetResourceIdFromString(setting):
  """Returns the resource id from the setting path.

  A setting path should start with following syntax:
  [organizations|folders|projects]/{resource_id}/settings/{setting_name}/value

  Args:
    setting: A String that contains the setting path
  """
  return setting.split('/')[1]


def GetSettingsPathFromArgs(args):
  """Returns the settings path from the user-specified arguments.

  A settings path has the following syntax:
  [organizations|folders|projects]/{resource_id}/settings/{setting_name}.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  resource = GetParentResourceFromArgs(args)
  setting_name = GetSettingNameFromArgs(args)

  return '{}/settings/{}'.format(resource, setting_name)


def ValidateSettingPath(setting):
  """Returns the resource id from the setting path.

  A setting path should start with following syntax:
  [organizations|folders|projects]/{resource_id}/settings/{setting_name}/value

  Args:
    setting: A String that contains the setting path
  """

  if GetResourceTypeFromString(setting) == 'invalid':
    return False
  setting_list = setting.split('/')
  if len(setting_list) != 4:
    return False
  elif setting_list[2] != 'settings':
    return False

  return True
