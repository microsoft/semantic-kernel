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
"""Library for retrieving declarative parsers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os


from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util.declarative.clients import declarative_client_base
from googlecloudsdk.core.util import files


def AddPathFlag(parser, required=False):
  parser.add_argument(
      '--path',
      required=required,
      type=files.ExpandHomeAndVars,
      default='-',
      help=('Path of the directory or file to output configuration(s). To '
            'output configurations to stdout, specify "--path=-".'))


def AddFormatFlag(parser):
  parser.add_argument(
      '--resource-format',
      choices=['krm', 'terraform'],
      help=('Format of the configuration to export. Available configuration '
            'formats are Kubernetes Resource Model YAML (krm) or Terraform '
            'HCL (terraform). Command defaults to "krm".'))


def AddAllFlag(parser, collection='collection'):
  parser.add_argument(
      '--all',
      action='store_true',
      help=(
          'Retrieve all resources within the {}. If `--path` is '
          'specified and is a valid directory, resources will be output as '
          'individual files based on resource name and scope. If `--path` is not '
          'specified, resources will be streamed to stdout.'.format(collection)
      ))


def AddOnErrorFlag(parser):
  parser.add_argument(
      '--on-error',
      choices=['continue', 'halt', 'ignore'],
      default='ignore',
      help=('Determines behavior when a recoverable error is encountered while '
            'exporting a resource. To stop execution when encountering an '
            'error, specify "halt". To log errors when encountered and '
            'continue the export, specify "continue". To continue when errors '
            'are encountered without logging, specify "ignore".'))


def AddListResourcesFlags(parser):
  _GetBulkExportParentGroup(
      parser,
      project_help=('Project ID to list supported '
                    'resources for.'),
      org_help=('Organization ID to list supported '
                'resources for.'),
      folder_help=('Folder ID to list supported '
                   'resources for.'))


def AddResourceTypeFlags(parser):
  """Add resource-type flag to parser."""
  group = parser.add_group(
      mutex=True,
      required=False,
      help='`RESOURCE TYPE FILTERS` - specify resource types to export.',
  )
  group.add_argument(
      '--resource-types',
      type=arg_parsers.ArgList(),
      metavar='RESOURCE_TYPE',
      help="""List of Config Connector KRM Kinds to export.
  For a full list of supported resource types for a given parent scope run:

  $ {parent_command} list-resource-types --[project|organization|folder]=<PARENT>
  """)
  group.add_argument(
      '--resource-types-file',
      type=arg_parsers.FileContents(),
      metavar='RESOURCE_TYPE_FILE',
      help="""A comma (',') or newline ('\\n') separated file containing the list of
      Config Connector KRM Kinds to export.
  For a full list of supported resource types for a given parent scope run:

  $ {parent_command} list-resource-types --[project|organization|folder]=<PARENT>
  """)


def AddBulkExportArgs(parser):
  """Adds flags for the bulk-export command."""
  AddOnErrorFlag(parser)
  AddPathFlag(parser)
  AddFormatFlag(parser)
  # Make a Mutex Group Here!!!!!
  resource_storage_mutex = parser.add_group(
      mutex=True,
      help=(
          'Select `storage-path` if you want to specify the Google Cloud'
          ' Storage bucket bulk-export should use for Cloud Asset Inventory'
          ' Export. Alternatively, you can provide a `RESOURCE TYPE FILTER` to'
          ' filter resources. Filtering resources _does not_ use Google Cloud'
          ' Storage to export resources.'
      ),
  )
  AddResourceTypeFlags(resource_storage_mutex)
  resource_storage_mutex.add_argument(
      '--storage-path',
      required=False,
      help=('Google Cloud Storage path where a Cloud Asset Inventory export '
            'will be stored, example: '
            '`gs://your-bucket-name/your/prefix/path`'))

  _GetBulkExportParentGroup(parser)


def ValidateAllPathArgs(args):
  if args.IsSpecified('all'):
    if args.IsSpecified('path') and not os.path.isdir(args.path):
      raise declarative_client_base.ClientException(
          'Error executing export: "{}" must be a directory when --all is'
          ' specified.'.format(args.path)
      )


def _GetBulkExportParentGroup(
    parser,
    required=False,
    project_help='Project ID',
    org_help='Organization ID',
    folder_help='Folder ID',
):
  """Creates parent flags for resource export.

  Args:
    parser:
    required:
    project_help:
    org_help:
    folder_help:

  Returns:
    Mutext group for resource export parent.
  """
  group = parser.add_group(
      mutex=True,
      required=required,
      help=(
          '`RESOURCE PARENT FLAG` - specify one of the following to determine'
          ' the scope of exported resources.'
      ),
  )
  group.add_argument('--organization', type=str, help=org_help)
  group.add_argument('--project', help=project_help)
  group.add_argument('--folder', type=str, help=folder_help)
  return group


def AddTerraformGenerateImportArgs(parser):
  """Arguments for resource-config terraform generate-import command."""
  input_path_help = (
      'Path to a Terrafrom formatted (.tf) resource file or directory of files '
      'exported via. `gcloud alpha resource-config bulk-export` or '
      'resource surface specific `config export` command.')
  input_path = calliope_base.Argument(
      'INPUT_PATH', type=files.ExpandHomeAndVars, help=input_path_help)

  output_args = calliope_base.ArgumentGroup(
      category='OUTPUT DESTINATION',
      mutex=True,
      help='Specify the destination of the generated script.')

  file_spec_group = calliope_base.ArgumentGroup(
      help=(
          'Specify the exact filenames for the output import script and module'
          ' files.'
      )
  )

  file_spec_group.AddArgument(
      calliope_base.Argument(
          '--output-script-file',
          required=False,
          type=files.ExpandHomeAndVars,
          help=(
              'Specify the full path path for generated import script. If '
              'not set, a default filename of the form '
              '`terraform_import_YYYYMMDD-HH-MM-SS.sh|cmd` will be generated.'
          ),
      )
  )
  file_spec_group.AddArgument(
      calliope_base.Argument(
          '--output-module-file',
          required=False,
          type=files.ExpandHomeAndVars,
          help=(
              'Specify the full path path for generated terraform module file.'
              ' If not set, a default filename of `gcloud-export-modules.tf`'
              ' will be generated.'
          ),
      )
  )
  output_args.AddArgument(file_spec_group)
  output_args.AddArgument(calliope_base.Argument(
      '--output-dir',
      required=False,
      type=files.ExpandHomeAndVars,
      help=('Specify the output directory only for the generated import script.'
            ' If specified directory does not exists it will be created. '
            'Generated script will have a default name of the form '
            '`terraform_import_YYYYMMDD-HH-MM-SS.sh|cmd`')))
  input_path.AddToParser(parser)
  output_args.AddToParser(parser)


def AddInitProviderArgs(parser):
  """Add args for init provider."""
  zone = calliope_base.Argument(
      '--zone',
      required=False,
      help="""Default Google Cloud Zone for Zonal Resources.
        If not specified the current `compute/zone` property will be used.""")

  region = calliope_base.Argument(
      '--region',
      required=False,
      help="""Default Google Cloud Region for Regional Resources.
      If not specified the current `compute/region` property will be used.""")

  billing_group = parser.add_group(
      help="""The below flags specify how the optional `user_project_override` and `billing_project` settings are configured for the Google Terraform Provider.
      See the [Google Terraform Provider Config Reference](https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/provider_reference#user_project_override) for more details.""",
      required=False,
      mutex=True)

  billing_group.add_argument(
      '--use-gcloud-billing-project',
      action='store_true',
      help="""If specified, will set `user_project_override` value in the Terrafom provider config to `true` and
      set `billing_project` to the current gcloud `billing/quota_project` property.""",
      default=False,
      required=False)

  billing_account_group = billing_group.add_group(
      help='Account Override Flags.')
  billing_account_group.add_argument(
      '--tf-user-project-override',
      action='store_true',
      help="""If specified, sets the `user_project_override` value in the Terraform provider config to `true`.""",
      default=False,
      required=True)

  billing_account_group.add_argument(
      '--tf-billing-project',
      help="""If specified, sets the `billing_project` value in the Terraform provider config.""",
      required=False)

  zone.AddToParser(parser)
  region.AddToParser(parser)


# Apply Related flags
def AddApplyPathArg(parser):
  parser.add_argument(
      'PATH',
      help=('File or directory path containing the resources to apply.'))


def AddResolveResourcesArg(parser):
  parser.add_argument(
      '--resolve-references',
      action='store_true',
      default=False,
      hidden=True,
      help=('If True, any resource references in the target file PATH will be '
            'resolved, and those external resources will be applied as well.'))
