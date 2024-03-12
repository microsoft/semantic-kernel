# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Common flag parsing for management gcloud."""
import json
import re

from apitools.base.py import encoding
from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.command_lib.scc.manage import constants
from googlecloudsdk.command_lib.scc.manage import errors
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.generated_clients.apis.securitycentermanagement.v1 import securitycentermanagement_v1_messages as messages

_CUSTOM_MODULE_ID_REGEX = re.compile('[0-9]{1,20}')


def GetParentResourceNameFromArgs(args) -> str:
  """Returns the relative path to the parent from args.

  Args:
    args: command line args.

  Returns:
    The relative path. e.g. 'projects/foo/locations/global',
    'folders/1234/locations/global'.
  """
  if args.parent:
    return f'{_ParseParent(args.parent).RelativeName()}/locations/global'

  return f'{_GetParentResourceFromArgs(args).RelativeName()}/locations/global'


def _GetParentResourceFromArgs(args):
  if args.organization:
    return resources.REGISTRY.Parse(
        args.organization, collection='cloudresourcemanager.organizations'
    )
  elif args.folder:
    return folders.FoldersRegistry().Parse(
        args.folder, collection='cloudresourcemanager.folders'
    )
  else:
    return resources.REGISTRY.Parse(
        args.project or properties.VALUES.core.project.Get(required=True),
        collection='cloudresourcemanager.projects',
    )


def GetModuleIdFromArgs(args) -> str:
  """Returns the module id from args."""
  if not args.module_id_or_name:
    raise errors.InvalidCustomModuleIdError(None)

  match = _CUSTOM_MODULE_ID_REGEX.fullmatch(args.module_id_or_name)

  if match:
    return match[0]
  else:
    raise errors.InvalidCustomModuleIdError(args.module_id_or_name)


def GetModuleNameFromArgs(args, module_type: constants.CustomModuleType) -> str:
  """Returns the specified module name from args if it exists.

  Otherwise, an exception is raised detailing the parsing error along with the
  expectation.

  Args:
    args: the args
    module_type: the module type (see
      googlecloudsdk.command_lib.scc.manage.constants)

  Raises:
    MissingCustomModuleNameOrIdError: no module name or id was specified.
    InvalidCustomModuleNameError: the specified module name was invalid.
    InvalidCustomModuleIdError: the specified module id was invalid.
  """

  if not args.module_id_or_name:
    raise errors.MissingCustomModuleNameOrIdError()

  # First try to see if we can parse a resource name
  collections = [
      f'securitycentermanagement.organizations.locations.{module_type}',
      f'securitycentermanagement.projects.locations.{module_type}',
      f'securitycentermanagement.folders.locations.{module_type}',
  ]

  is_possible_resource_name = (
      _IsPossibleResourceName(args.module_id_or_name)
      or len(args.GetSpecifiedArgNames()) == 1
  )

  for collection in collections:
    try:
      return resources.REGISTRY.Parse(
          args.module_id_or_name, collection=collection
      ).RelativeName()
    except resources.RequiredFieldOmittedException:
      pass

  if is_possible_resource_name:
    # The error messages provided by the default gcloud parsing are awful so we
    # detect a resource name misformatting here and print a better error
    raise errors.InvalidCustomModuleNameError(
        args.module_id_or_name, module_type
    )

  parent = GetParentResourceNameFromArgs(args)
  module_id = GetModuleIdFromArgs(args)

  return f'{parent}/{module_type}/{module_id}'


def _ParseParent(parent: str) -> str:
  """Extracts parent name from a string of the form {organizations|projects|folders}/<id>."""

  if parent.startswith('organizations/'):
    return resources.REGISTRY.Parse(
        parent, collection='cloudresourcemanager.organizations'
    )
  elif parent.startswith('folders/'):
    return folders.FoldersRegistry().Parse(
        parent, collection='cloudresourcemanager.folders'
    )
  elif parent.startswith('projects/'):
    return resources.REGISTRY.Parse(
        parent,
        collection='cloudresourcemanager.projects',
    )
  else:
    raise errors.InvalidParentError(parent)


def _IsPossibleResourceName(name: str) -> bool:
  return (
      name.startswith('organizations')
      or name.startswith('projects')
      or name.startswith('folders')
  )


def GetCustomConfigFromArgs(file):
  """Process the custom config file for the custom module."""
  if file is not None:
    try:
      config_dict = yaml.load(file)
      return encoding.DictToMessage(config_dict, messages.CustomConfig)
    except yaml.YAMLParseError as ype:
      raise errors.InvalidCustomConfigFileError(
          'Error parsing custom config file [{}]'.format(ype)
      )


def GetTestResourceFromArgs(file):
  """Process the test resource data file for the custom module to test against."""
  try:
    resource_dict = yaml.load(file)

    return encoding.DictToMessage(resource_dict, messages.SimulatedResource)
  except yaml.YAMLParseError as ype:
    raise errors.InvalidResourceFileError(
        'Error parsing resource file [{}]'.format(ype)
    )


def GetConfigValueFromArgs(file):
  """Process the config custom file for the custom module."""
  if file is not None:
    try:
      config = json.loads(file)
      return encoding.DictToMessage(
          config, messages.EventThreatDetectionCustomModule.ConfigValue
      )
    except json.JSONDecodeError as e:
      raise errors.InvalidConfigValueFileError(
          'Error parsing config value file [{}]'.format(e)
      )
  else:
    return None


def ParseJSONFile(file):
  """Converts the contents of a JSON file into a string."""
  if file is not None:
    try:
      config = json.loads(file)
      return json.dumps(config)
    except json.JSONDecodeError as e:
      raise errors.InvalidConfigValueFileError(
          'Error parsing config value file [{}]'.format(e)
      )
  else:
    return None


def GetEnablementStateFromArgs(
    enablement_state: str,
    module_type: constants.CustomModuleType
):
  """Parse the enablement state."""
  if module_type == constants.CustomModuleType.SHA:
    state_enum = (
        messages.SecurityHealthAnalyticsCustomModule.EnablementStateValueValuesEnum
    )
  elif module_type == constants.CustomModuleType.ETD:
    state_enum = (
        messages.EventThreatDetectionCustomModule.EnablementStateValueValuesEnum
    )
  else:
    raise errors.InvalidModuleTypeError(
        f'Module type "{module_type}" is not a valid module type.'
    )

  if enablement_state is None:
    raise errors.InvalidEnablementStateError(
        'Error parsing enablement state. Enablement state cannot be empty.'
    )

  state = enablement_state.upper()

  if state == 'ENABLED':
    return state_enum.ENABLED
  elif state == 'DISABLED':
    return state_enum.DISABLED
  elif state == 'INHERITED':
    return state_enum.INHERITED
  else:
    raise errors.InvalidEnablementStateError(
        f'Error parsing enablement state. "{state}" is not a valid enablement'
        ' state. Please provide one of ENABLED, DISABLED, or INHERITED.'
    )


def CreateUpdateMaskFromArgs(args):
  """Create an update mask with the args given."""
  if args.enablement_state is not None and args.custom_config_file is not None:
    return 'enablement_state,custom_config'
  elif args.enablement_state is not None:
    return 'enablement_state'
  elif args.custom_config_file is not None:
    return 'custom_config'
  else:
    raise errors.InvalidUpdateMaskInputError(
        'Error parsing Update Mask. Either a custom configuration or an'
        ' enablement state (or both) must be provided to update the custom'
        ' module.'
    )
