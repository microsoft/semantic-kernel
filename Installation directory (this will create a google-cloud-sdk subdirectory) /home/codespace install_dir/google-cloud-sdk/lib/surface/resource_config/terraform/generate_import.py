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
"""Command for generating Terraform Import script for exported resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.declarative import flags
from googlecloudsdk.command_lib.util.declarative import terraform_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files


_DETAILED_HELP = {
    'EXAMPLES':
        """
    To generate an import script named `import.sh` and a module file named `modules.tf` based on exported files in `my-dir/`, run:

      $ {command} my-dir/ --output-script-file=import.sh --output-module-file=modules.tf

    To generate an import script with the default `terraform_import_YYYYMMDD-HH-MM-SS.cmd`
    and `gcloud-export-modules.tf` names on Windows, based on exported files in `my-dir/`, run:

      $ {command} my-dir
   """
}


class GenerateImport(base.DeclarativeCommand):
  """Generate Terraform import script for exported resources."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddTerraformGenerateImportArgs(parser)

  def Run(self, args):
    input_path = args.INPUT_PATH
    import_data = terraform_utils.ParseExportFiles(input_path)

    # Generate script file.
    dest_script_file, dest_script_dir = terraform_utils.ProcessOutputParameters(
        args.output_script_file, args.output_dir)
    dest_script_file = dest_script_file or terraform_utils.GenerateDefaultScriptFileName(
    )
    dest_script_dir = dest_script_dir or files.GetCWD()
    with progress_tracker.ProgressTracker(
        message='Generating import script.',
        aborted_message='Aborted script generation.'):
      output_script_filename, script_successes = terraform_utils.GenerateImportScript(
          import_data, dest_script_file, dest_script_dir)
    log.status.Print(
        'Successfully generated {} with imports for {} resources.'.format(
            output_script_filename, script_successes))

    # Generate module file..
    dest_module_file, dest_module_dir = terraform_utils.ProcessOutputParameters(
        args.output_module_file, args.output_dir)
    dest_module_file = dest_module_file or terraform_utils.TF_MODULES_FILENAME
    dest_module_dir = dest_module_dir or files.GetCWD()
    with progress_tracker.ProgressTracker(
        message='Generating terraform modules.',
        aborted_message='Aborted module generation.'):
      output_module_filename, module_successes = terraform_utils.GenerateModuleFile(
          import_data, properties.VALUES.core.project.Get(required=True),
          dest_module_file, dest_module_dir)
    log.status.Print('Successfully generated {} with {} modules.'.format(
        output_module_filename, module_successes))

    return None
