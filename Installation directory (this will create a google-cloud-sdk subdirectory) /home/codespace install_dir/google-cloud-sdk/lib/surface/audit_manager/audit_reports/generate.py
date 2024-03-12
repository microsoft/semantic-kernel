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
"""Command to generate a new Audit Report."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.audit_manager import audit_reports
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.audit_manager import exception_utils
from googlecloudsdk.command_lib.audit_manager import flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties


_DETAILED_HELP = {
    'DESCRIPTION': 'Generate a new Audit Report.',
    'EXAMPLES': """ \
        To generate an Audit Report in the `us-central1` region,
        for a project with ID `123` for compliance standard `fedramp_moderate` in `odf` format and store it in `gs://testbucketauditmanager` bucket, run:

          $ {command} --project=123 --location=us-central1 --compliance-standard=fedramp_moderate --report-format=odf --gcs-uri=gs://testbucketauditmanager
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Generate(base.CreateCommand):
  """Generate Audit Report."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddProjectOrFolderFlags(parser, 'for which to generate audit report')
    flags.AddLocationFlag(parser, 'the report should be generated')
    flags.AddComplianceStandardFlag(parser)
    flags.AddReportFormatFlag(parser)
    flags.AddDestinationFlags(parser)
    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

  def Run(self, args):
    """Run the generate command."""
    is_parent_folder = args.folder is not None

    scope = (
        'folders/{folder}'.format(folder=args.folder)
        if is_parent_folder
        else 'projects/{project}'.format(project=args.project)
    )

    scope += '/locations/{location}'.format(location=args.location)

    client = audit_reports.AuditReportsClient()

    try:
      return client.Generate(
          scope,
          args.compliance_standard,
          report_format=args.report_format,
          gcs_uri=args.gcs_uri,
          is_parent_folder=is_parent_folder,
      )

    except apitools_exceptions.HttpError as error:
      exc = exception_utils.AuditManagerError(error)

      if exc.has_error_info(exception_utils.ERROR_REASON_NOT_ENROLLED):
        exc.suggested_command_purpose = 'enroll the resource'
        exc.suggested_command = (
            f'{flags.GetCommandPrefix(args.command_path)} enrollments add'
            f' {flags.GetProjectOrFolderParam(args)} {flags.GetLocationParam(args)}'
            f' {flags.GetEligibleGcsBucketParam(args)}'
        )
      elif exc.has_error_info(exception_utils.ERROR_REASON_PERMISSION_DENIED):
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
