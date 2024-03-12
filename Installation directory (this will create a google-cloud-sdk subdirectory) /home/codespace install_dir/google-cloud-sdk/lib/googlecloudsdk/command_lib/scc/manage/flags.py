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
"""Specify common flags for management gcloud."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import completers
from googlecloudsdk.command_lib.scc.manage import constants


def CreateParentFlag(required=False) -> base.Argument:
  """Returns a flag for capturing an org, project, or folder name.

  The flag can be provided in one of 2 forms:
    1. --parent=organizations/<id>, --parent=projects/<id or name>,
    --parent=folders/<id>
    2. One of:
      * --organizations=<id> or organizations/<id>
      * --projects=<id or name> or projects/<id or name>
      * --folders=<id> or folders/<id>

  Args:
    required: whether or not this flag is required
  """

  root = base.ArgumentGroup(mutex=True, required=required)

  root.AddArgument(
      base.Argument(
          '--parent',
          required=False,
          help=("""Parent associated with the custom module. Can be one of
              organizations/<id>, projects/<id or name>, folders/<id>"""),
      )
  )

  root.AddArgument(
      base.Argument(
          '--organization',
          required=False,
          metavar='ORGANIZATION_ID',
          completer=completers.OrganizationCompleter,
          help='Organization associated with the custom module.',
      )
  )

  root.AddArgument(
      base.Argument(
          '--project',
          required=False,
          metavar='PROJECT_ID_OR_NUMBER',
          completer=completers.ProjectCompleter,
          help='Project associated with the custom module.',
      )
  )

  root.AddArgument(
      base.Argument(
          '--folder',
          required=False,
          metavar='FOLDER_ID',
          help='Folder associated with the custom module.',
      )
  )

  return root


def CreateModuleIdOrNameArg(
    module_type: constants.CustomModuleType,
) -> base.Argument:
  """A positional argument representing a custom module ID or name."""
  return base.Argument(
      'module_id_or_name',
      help="""The custom module ID or name. The expected format is {parent}/[locations/global]/MODULE_TYPE/{module_id} or just {module_id}. Where module_id is a numeric identifier 1-20 characters
      in length. Parent is of the form organizations/{id}, projects/{id or name},
      folders/{id}.""".replace(
          'MODULE_TYPE', module_type
      ),
  )


def CreateCustomConfigFlag(required=True) -> base.Argument:
  return base.Argument(
      '--custom-config-from-file',
      required=required,
      metavar='CUSTOM_CONFIG',
      help="""Path to a YAML custom configuration file.""",
      type=arg_parsers.FileContents(),
  )


def CreateTestResourceFlag(required=True) -> base.Argument:
  return base.Argument(
      '--resource-from-file',
      required=required,
      metavar='TEST_DATA',
      help="""Path to a YAML file that contains the resource data to validate the Security Health Analytics custom module against.""",
      type=arg_parsers.FileContents(),
  )


def CreateModuleTypeFlag(required=True) -> base.Argument:
  return base.Argument(
      '--module-type',
      required=required,
      metavar='MODULE_TYPE',
      help="""Type of the custom module. For a list of valid module types please visit https://cloud.google.com/security-command-center/docs/custom-modules-etd-overview#custom_modules_and_templates.""",
  )


def CreateValidateOnlyFlag(required=False) -> base.Argument:
  return base.Argument(
      '--validate-only',
      required=required,
      default=None,
      action='store_true',
      help="""If present, the request is validated (including IAM checks) but no action is taken.""",
  )


def CreateUpdateFlags(
    module_type: constants.CustomModuleType,
    file_type,
    required=True,
) -> base.Argument:
  """Returns a custom-config flag or an enablement-state flag, or both."""

  root = base.ArgumentGroup(mutex=False, required=required)
  root.AddArgument(
      base.Argument(
          '--custom-config-file',
          required=False,
          default=None,
          help="""Path to a {} file that contains the custom config to set for the module.""".format(
              file_type
          ),
          type=arg_parsers.FileContents(),
      )
  )
  root.AddArgument(
      CreateEnablementStateFlag(required=False, module_type=module_type)
  )
  return root


def CreateEnablementStateFlag(
    module_type: constants.CustomModuleType,
    required: bool,
):
  """Creates an enablement state flag."""
  if module_type == constants.CustomModuleType.SHA:
    module_name = 'Security Health Analytics'
  elif module_type == constants.CustomModuleType.ETD:
    module_name = 'Event Threat Detection'
  return base.Argument(
      '--enablement-state',
      required=required,
      default=None,
      help="""Sets the enablement state of the {} custom module. Valid options are ENABLED, DISABLED, OR INHERITED.""".format(
          module_name
      ),
  )


def CreateEtdCustomConfigFilePathFlag(required=True) -> base.Argument:
  return base.Argument(
      '--custom-config-file',
      required=required,
      metavar='CUSTOM_CONFIG',
      help="""Path to a JSON custom configuration file of the ETD custom module.""",
      type=arg_parsers.FileContents(),
  )


def CreateDisplayNameFlag(required=True) -> base.Argument:
  return base.Argument(
      '--display-name',
      required=required,
      metavar='DISPLAY-NAME',
      help="""The display name of the custom module.""",
  )
