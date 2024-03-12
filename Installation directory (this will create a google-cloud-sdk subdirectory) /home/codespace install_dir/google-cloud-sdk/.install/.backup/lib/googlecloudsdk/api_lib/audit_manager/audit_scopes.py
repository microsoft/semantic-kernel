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
"""Utilities for Audit Manager API, Audit Scope Endpoints."""

from googlecloudsdk.api_lib.audit_manager import util


class AuditScopesClient(object):
  """Client for Audit Scopes in Audit Manager API."""

  def __init__(self, client=None, messages=None):
    self.client = client or util.GetClientInstance()
    self.messages = messages or util.GetMessagesModule(client)

    scope_report_format_enum = (
        self.messages.GenerateAuditScopeReportRequest.ReportFormatValueValuesEnum
    )
    self.report_format_map = {
        'odf': scope_report_format_enum.AUDIT_SCOPE_REPORT_FORMAT_ODF
    }

  def Generate(
      self,
      scope,
      compliance_standard,
      report_format,
      is_parent_folder,
  ):
    """Generate an Audit Scope.

    Args:
      scope: str, the scope for which to generate the scope.
      compliance_standard: str, Compliance standard against which the scope
        must be generated.
      report_format: str, The format in which the audit scope should be
        generated.
      is_parent_folder: bool, whether the parent is folder and not project.

    Returns:
      Described audit scope resource.
    """
    service = (
        self.client.folders_locations_auditScopeReports
        if is_parent_folder
        else self.client.projects_locations_auditScopeReports
    )

    inner_req = self.messages.GenerateAuditScopeReportRequest()
    inner_req.complianceStandard = compliance_standard
    inner_req.reportFormat = self.report_format_map[report_format]

    req = (
        self.messages.AuditmanagerFoldersLocationsAuditScopeReportsGenerateRequest()
        if is_parent_folder
        else self.messages.AuditmanagerProjectsLocationsAuditScopeReportsGenerateRequest()
    )

    req.scope = scope
    req.generateAuditScopeReportRequest = inner_req
    return service.Generate(req)
