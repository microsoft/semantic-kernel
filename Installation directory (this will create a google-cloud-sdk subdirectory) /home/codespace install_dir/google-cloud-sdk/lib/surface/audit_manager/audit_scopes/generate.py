# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command to generate a new Audit Scope."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.audit_manager import audit_scopes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.audit_manager import exception_utils
from googlecloudsdk.command_lib.audit_manager import flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


_DETAILED_HELP = {
    'DESCRIPTION': 'Generate a new Audit Scope.',
    'EXAMPLES': """ \
        To generate an Audit Scope in the `us-central1` region,
        for a project with ID `123` for compliance standard `fedramp_moderate` in `odf` format, run:

          $ {command} --project="123" --location="us-central1" --compliance-standard="fedramp_moderate" --report-format="odf" --output-directory="scopes/currentyear" --output-file-name="auditreport"
        """,
}

_SCOPE_REPORT_CONTENTS = 'scopeReportContents'
_FILE_EXTENSION = '.ods'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Generate(base.CreateCommand):
  """Generate Audit Scope."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddProjectOrFolderFlags(
        parser, 'for which to generate audit scope'
    )
    flags.AddLocationFlag(parser, 'the scope should be generated')
    flags.AddComplianceStandardFlag(parser)
    flags.AddScopeReportFormatFlag(parser)
    flags.AddOutputDirectoryFormatFlag(parser)
    flags.AddOutputFileNameFormatFlag(parser)

  def Run(self, args):
    """Run the generate command."""
    is_parent_folder = args.folder is not None

    scope = (
        'folders/{folder}'.format(folder=args.folder)
        if is_parent_folder
        else 'projects/{project}'.format(project=args.project)
    )
    scope += '/locations/{location}'.format(location=args.location)

    client = audit_scopes.AuditScopesClient()
    try:
      response = client.Generate(
          scope,
          args.compliance_standard,
          report_format=args.report_format,
          is_parent_folder=is_parent_folder,
      )
      self.SaveReport(
          response,
          args.output_directory,
          args.output_file_name,
      )
      return response

    except apitools_exceptions.HttpError as error:
      exc = exception_utils.AuditManagerError(error)

      if exc.has_error_info(exception_utils.ERROR_REASON_PERMISSION_DENIED):
        role = 'roles/auditmanager.auditor'
        user = properties.VALUES.core.account.Get()
        exc.suggested_command_purpose = 'grant permission'
        command_prefix = (
            'gcloud resource-manager folders add-iam-policy-binding'
            if is_parent_folder
            else 'gcloud projects add-iam-policy-binding'
        )
        exc.suggested_command = (
            f'{command_prefix}'
            f' {args.folder if is_parent_folder else args.project}'
            f' --member=user:{user} --role {role}'
        )

      core_exceptions.reraise(exc)

  # TODO: b/324031367 - Add type annotations to all the methods.
  def SaveReport(
      self, response, output_directory, output_file_name
  ):
    """Save the generated scope."""
    is_empty_directory_path = output_directory == ''
    directory_path = '' if is_empty_directory_path else output_directory + '/'
    file_path = directory_path + output_file_name + _FILE_EXTENSION
    content_bytes = response.scopeReportContents
    files.WriteBinaryFileContents(file_path, content_bytes, overwrite=False)
