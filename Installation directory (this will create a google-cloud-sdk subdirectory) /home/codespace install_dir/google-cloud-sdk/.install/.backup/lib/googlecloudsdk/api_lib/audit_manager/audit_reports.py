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
"""Utilities for Audit Manager API, Audit Report Endpoints."""

from googlecloudsdk.api_lib.audit_manager import util


class AuditReportsClient(object):
  """Client for Audit Reports in Audit Manager API."""

  def __init__(self, client=None, messages=None):
    self.client = client or util.GetClientInstance()
    self.messages = messages or util.GetMessagesModule(client)

    report_format_enum = (
        self.messages.GenerateAuditReportRequest.ReportFormatValueValuesEnum
    )
    self.report_format_map = {'odf': report_format_enum.AUDIT_REPORT_FORMAT_ODF}

  def Generate(
      self,
      scope,
      compliance_standard,
      report_format,
      gcs_uri,
      is_parent_folder,
  ):
    """Generate an Audit Report.

    Args:
      scope: str, the scope for which to generate the report.
      compliance_standard: str, Compliance standard against which the Report
        must be generated.
      report_format: str, The format in which the audit report should be
        generated.
      gcs_uri: str, Destination Cloud storage bucket where report and evidence
        must be uploaded.
      is_parent_folder: bool, whether the parent is folder and not project.

    Returns:
      Described audit operation resource.
    """
    service = (
        self.client.folders_locations_auditReports
        if is_parent_folder
        else self.client.projects_locations_auditReports
    )

    inner_req = self.messages.GenerateAuditReportRequest()
    inner_req.complianceStandard = compliance_standard
    inner_req.reportFormat = self.report_format_map[report_format]
    inner_req.gcsUri = gcs_uri

    req = (
        self.messages.AuditmanagerFoldersLocationsAuditReportsGenerateRequest()
        if is_parent_folder
        else self.messages.AuditmanagerProjectsLocationsAuditReportsGenerateRequest()
    )

    req.scope = scope
    req.generateAuditReportRequest = inner_req
    return service.Generate(req)
