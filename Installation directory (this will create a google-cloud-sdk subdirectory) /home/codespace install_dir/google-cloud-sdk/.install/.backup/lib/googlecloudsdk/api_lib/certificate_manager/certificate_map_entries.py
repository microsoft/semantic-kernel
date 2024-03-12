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
"""API client library for Certificate Manager certificate map entries."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.certificate_manager import api_client


class CertificateMapEntryClient(object):
  """API client for Certificate Manager certificate map entries."""

  def __init__(self, client=None, messages=None):
    self._client = client or api_client.GetClientInstance()
    self._service = self._client.projects_locations_certificateMaps_certificateMapEntries
    self.messages = messages or self._client.MESSAGES_MODULE

  def Create(self,
             parent_ref,
             entry_id,
             hostname=None,
             cert_refs=None,
             description=None,
             labels=None):
    """Creates a certificate map entry.

    Args:
      parent_ref: a Resource reference to a
        certificatemanager.projects.locations.certificateMaps resource for the
        parent of this certificate map entry.
      entry_id: str, the ID of the entry to create.
      hostname: str, hostname of map entry. If None, primary entry is created.
      cert_refs: Resource references to
        certificatemanager.projects.locations.certificates resources to be
        attached to this entry.
      description: str, user-provided description.
      labels: Unified GCP Labels for the resource.

    Returns:
      Operation: the long running operation to create a map entry.
    """
    req = self.messages.CertificatemanagerProjectsLocationsCertificateMapsCertificateMapEntriesCreateRequest(
        parent=parent_ref.RelativeName(),
        certificateMapEntryId=entry_id,
        certificateMapEntry=self.messages.CertificateMapEntry(
            labels=labels,
            hostname=hostname,
            matcher=self.messages.CertificateMapEntry.MatcherValueValuesEnum
            .PRIMARY if not hostname else None,
            certificates=[ref.RelativeName() for ref in cert_refs],
            description=description,
        ))

    return self._service.Create(req)

  def Get(self, entry_ref):
    """Gets certificate map entry.

    Args:
      entry_ref: a Resource reference to a
        certificatemanager.projects.locations.certificateMaps.certificateMapEntries
        resource to get.

    Returns:
      Certificate Map Entry API representation.
    """
    get_req = self.messages.CertificatemanagerProjectsLocationsCertificateMapsCertificateMapEntriesGetRequest(
        name=entry_ref.RelativeName())
    return self._service.Get(get_req)

  def List(
      self,
      parent_ref,
      limit=None,
      page_size=None,
      list_filter=None,
      order_by=None,
  ):
    """List certificate map entries in a given certificate map.

    Args:
      parent_ref: a Resource reference to a
        certificatemanager.projects.locations.certificateMaps resource to list
        entries for.
      limit: int, the total number of results to return from the API.
      page_size: int, the number of results in each batch from the API.
      list_filter: str, filter to apply in the list request.
      order_by: str, fields used for resource ordering.

    Returns:
      A list of the entries in the certificate map.
    """
    list_req = self.messages.CertificatemanagerProjectsLocationsCertificateMapsCertificateMapEntriesListRequest(
        parent=parent_ref.RelativeName(), filter=list_filter, orderBy=order_by)
    return list_pager.YieldFromList(
        self._service,
        list_req,
        batch_size=page_size,
        limit=limit,
        current_token_attribute='pageToken',
        next_token_attribute='nextPageToken',
        field='certificateMapEntries',
        batch_size_attribute='pageSize')

  def Delete(self, entry_ref):
    """Deletes certificate map entry.

    Args:
      entry_ref: a Resource reference to a
        certificatemanager.projects.locations.certificateMaps.certificateMapEntries
        resource to delete.

    Returns:
      Operation: the long running operation to delete certificate map entry.
    """
    delete_req = self.messages.CertificatemanagerProjectsLocationsCertificateMapsCertificateMapEntriesDeleteRequest(
        name=entry_ref.RelativeName())
    return self._service.Delete(delete_req)

  def Patch(self, entry_ref, labels=None, description=None, cert_refs=None):
    """Updates a certificate map entry.

    Used for updating labels, description and attached certificates.

    Args:
      entry_ref: a Resource reference to a
        certificatemanager.projects.locations.certificateMaps.certificateMapEntries
        resource.
      labels: unified GCP Labels for the resource.
      description: str, new description
      cert_refs: Resource references to
        certificatemanager.projects.locations.certificates resources to be
        attached to this entry.

    Returns:
      Operation: the long running operation to patch certificate map entry.
    """
    certificate_map_entry = self.messages.CertificateMapEntry()
    updated_fields = []
    if labels is not None:
      certificate_map_entry.labels = labels
      updated_fields.append('labels')
    if description is not None:
      certificate_map_entry.description = description
      updated_fields.append('description')
    if cert_refs is not None:
      certificate_map_entry.certificates.extend(
          [ref.RelativeName() for ref in cert_refs])
      updated_fields.append('certificates')
    update_mask = ','.join(updated_fields)

    patch_req = self.messages.CertificatemanagerProjectsLocationsCertificateMapsCertificateMapEntriesPatchRequest(
        certificateMapEntry=certificate_map_entry,
        name=entry_ref.RelativeName(),
        updateMask=update_mask)
    return self._service.Patch(patch_req)
