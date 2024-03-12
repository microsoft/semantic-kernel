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
"""Management API gcloud errors."""

from googlecloudsdk.command_lib.scc.manage import constants
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources


class Error(exceptions.Error):
  """Base error for this module."""


class InvalidParentError(Error):
  """An error representing an invalid CRM parent."""

  def __init__(self, bad_parent_arg: str):
    super(Error, self).__init__(
        f'"{bad_parent_arg}" is not a valid parent. The parent name should'
        ' begin with "organizations/", "projects/", or "folders/".'
    )


class MissingCustomModuleNameOrIdError(Error):
  """An error representing a missing custom module name or id."""

  def __init__(self):
    super(Error, self).__init__('Missing custom module name or ID.')


class InvalidCustomModuleIdError(Error):
  """An error representing a custom module ID that does not conform to _CUSTOM_MODULE_ID_REGEX."""

  def __init__(self, bad_module_id_arg: str):
    if bad_module_id_arg is None:
      super(Error, self).__init__('Missing custom module ID.')
    else:
      super(Error, self).__init__(
          f'"{bad_module_id_arg}" is not a valid custom module ID. The ID'
          ' should consist only of numbers and be 1-20 characters in length.'
      )


class InvalidCustomModuleNameError(Error):
  """An error representing an invalid custom module name."""

  def __init__(self, bad_module_name_arg: str, module_type: str):
    valid_formats = '\n\n\t\t'.join(_GetValidNameFormatForModule(module_type))

    super(Error, self).__init__(
        f'"{bad_module_name_arg}" is not a valid custom module name.\n\n\tThe'
        f' expected format is one of:\n\n\t\t{valid_formats}\n'
    )


def _GetValidNameFormatForModule(
    module_type: constants.CustomModuleType,
) -> str:
  """Returns a list of name format strings for the given module_type."""

  collections = [
      f'securitycentermanagement.organizations.locations.{module_type}',
      f'securitycentermanagement.projects.locations.{module_type}',
      f'securitycentermanagement.folders.locations.{module_type}',
  ]

  return [
      resources.REGISTRY.GetCollectionInfo(collection).GetPath('')
      for collection in collections
  ]


class InvalidCustomConfigFileError(Error):
  """Error if a custom config file is improperly formatted."""


class InvalidResourceFileError(Error):
  """Error if a test data file is improperly formatted."""


class InvalidConfigValueFileError(Error):
  """Error if a config value file is improperly formatted."""


class InvalidUpdateMaskInputError(Error):
  """Error if neither a custom configuration or an enablement state were given to update."""


class InvalidEnablementStateError(Error):
  """Error if an enablement state is anything but ENABLED or DISABLED."""
