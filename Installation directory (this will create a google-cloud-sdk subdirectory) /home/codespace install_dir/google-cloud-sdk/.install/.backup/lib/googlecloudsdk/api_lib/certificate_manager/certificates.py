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
"""API client library for Certificate Manager certificates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.certificate_manager import api_client


class CertificateClient(object):
  """API client for Certificate Manager certificates."""

  def __init__(self, client=None, messages=None):
    self._client = client or api_client.GetClientInstance()
    self._service = self._client.projects_locations_certificates
    self.messages = messages or self._client.MESSAGES_MODULE

  def Create(self,
             parent_ref,
             cert_id,
             self_managed_cert_data=None,
             description='',
             labels=None):
    """Creates a certificate.

    Args:
      parent_ref: a Resource reference to a
        certificatemanager.projects.locations resource for the parent of this
        certificate.
      cert_id: str, the ID of the cerificate to create.
      self_managed_cert_data: API message for self-managed certificate data.
      description: str, user-provided description.
      labels: Unified GCP Labels for the resource.

    Returns:
      Operation: the long running operation to create a certificate.
    """
    req = self.messages.CertificatemanagerProjectsLocationsCertificatesCreateRequest(
        parent=parent_ref.RelativeName(),
        certificateId=cert_id,
        certificate=self.messages.Certificate(
            labels=labels,
            description=description,
            selfManagedCertData=self_managed_cert_data,
        ))

    return self._service.Create(req)

  def Get(self, cert_ref):
    """Gets certificate.

    Args:
      cert_ref: a Resource reference to a
        certificatemanager.projects.locations.certificates resource to get.

    Returns:
      Certificate API representation.
    """
    get_req = self.messages.CertificatemanagerProjectsLocationsCertificatesGetRequest(
        name=cert_ref.RelativeName())
    return self._service.Get(get_req)

  def List(
      self,
      parent_ref,
      limit=None,
      page_size=None,
      list_filter=None,
      order_by=None,
  ):
    """List certificates in a given project and location.

    Args:
      parent_ref: a Resource reference to a
        certificatemanager.projects.locations resource to list certs for.
      limit: int, the total number of results to return from the API.
      page_size: int, the number of results in each batch from the API.
      list_filter: str, filter to apply in the list request.
      order_by: str, fields used for resource ordering.

    Returns:
      A list of the certificates in the project.
    """
    list_req = self.messages.CertificatemanagerProjectsLocationsCertificatesListRequest(
        parent=parent_ref.RelativeName(), filter=list_filter, orderBy=order_by)
    return list_pager.YieldFromList(
        self._service,
        list_req,
        batch_size=page_size,
        limit=limit,
        current_token_attribute='pageToken',
        next_token_attribute='nextPageToken',
        field='certificates',
        batch_size_attribute='pageSize')

  def Delete(self, cert_ref):
    """Deletes certificate.

    Args:
      cert_ref: a Resource reference to a
        certificatemanager.projects.locations.certificates resource to delete.

    Returns:
      Operation: the long running operation to delete certificate.
    """
    delete_req = self.messages.CertificatemanagerProjectsLocationsCertificatesDeleteRequest(
        name=cert_ref.RelativeName())
    return self._service.Delete(delete_req)

  def Patch(self,
            cert_ref,
            self_managed_cert_data=None,
            labels=None,
            description=None):
    """Updates a certificate.

    Used for updating labels, description and certificate data.

    Args:
      cert_ref: a Resource reference to a
        certificatemanager.projects.locations.certificates resource.
      self_managed_cert_data: API message for self-managed certificate data.
      labels: unified GCP Labels for the resource.
      description: str, new description

    Returns:
      Operation: the long running operation to patch certificate.
    """
    certificate = self.messages.Certificate()
    updated_fields = []
    if self_managed_cert_data:
      certificate.selfManaged = self_managed_cert_data
      updated_fields.append('self_managed')
    if labels:
      certificate.labels = labels
      updated_fields.append('labels')
    if description:
      certificate.description = description
      updated_fields.append('description')
    update_mask = ','.join(updated_fields)

    patch_req = self.messages.CertificatemanagerProjectsLocationsCertificatesPatchRequest(
        certificate=certificate,
        name=cert_ref.RelativeName(),
        updateMask=update_mask)
    return self._service.Patch(patch_req)
