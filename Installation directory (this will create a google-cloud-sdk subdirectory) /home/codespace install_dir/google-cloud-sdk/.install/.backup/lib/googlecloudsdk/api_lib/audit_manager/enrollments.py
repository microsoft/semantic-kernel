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
"""Utilities for Audit Manager API, Enrollments Endpoints."""

from googlecloudsdk.api_lib.audit_manager import util


class EnrollmentsClient(object):
  """Client for operations in Audit Manager API."""

  def __init__(self, client=None, messages=None):
    self.client = client or util.GetClientInstance()
    self.messages = messages or util.GetMessagesModule(client)

  def Add(
      self,
      scope,
      eligible_gcs_buckets,
      is_parent_folder,
  ):
    """Generate an Audit Report.

    Args:
      scope: str, the scope to be enrolled.
      eligible_gcs_buckets: str, List of destination among which customer can
        choose to upload their reports during the audit process.
      is_parent_folder: bool, whether the parent is folder and not project.

    Returns:
      Described audit operation resource.
    """
    service = (
        self.client.folders_locations
        if is_parent_folder
        else self.client.projects_locations
    )

    inner_req = self.messages.EnrollResourceRequest()
    inner_req.destinations = list(
        map(self.Gcs_uri_to_eligible_destination, eligible_gcs_buckets)
    )

    req = (
        self.messages.AuditmanagerFoldersLocationsEnrollResourceRequest()
        if is_parent_folder
        else self.messages.AuditmanagerProjectsLocationsEnrollResourceRequest()
    )

    req.scope = scope
    req.enrollResourceRequest = inner_req
    return service.EnrollResource(req)

  def Gcs_uri_to_eligible_destination(self, gcs_uri):
    dest = self.messages.EligibleDestination()
    dest.eligibleGcsBucket = gcs_uri
    return dest
