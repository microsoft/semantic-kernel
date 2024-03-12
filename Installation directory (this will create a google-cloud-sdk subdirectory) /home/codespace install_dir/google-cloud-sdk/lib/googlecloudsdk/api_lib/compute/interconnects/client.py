# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Interconnect."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class Interconnect(object):
  """Abstracts Interconnect resource."""

  def __init__(self, ref, compute_client=None):
    self.ref = ref
    self._compute_client = compute_client

  @property
  def _client(self):
    return self._compute_client.apitools_client

  def _MakeCreateRequestTuple(
      self,
      description,
      location,
      interconnect_type,
      requested_link_count,
      link_type,
      admin_enabled,
      noc_contact_email,
      customer_name,
      remote_location,
      requested_features,
  ):
    """Make a tuple for interconnect insert request.

    Args:
      description: String that represents the description of the Cloud
      Interconnect resource.
      location: String that represents the URL of the location resource for
      Cloud Interconnect that Cloud Interconnect should be connected to.
      interconnect_type: InterconnectTypeValueValuesEnum that represents the
      type of Cloud Interconnect.
      requested_link_count: Number of the requested links.
      link_type: LinkTypeValueValuesEnum that represents Cloud Interconnect
      link type.
      admin_enabled: Boolean that represents administrative status of
      Cloud Interconnect.
      noc_contact_email: String that represents the customer's email address.
      customer_name: String that represents the customer's name.
      remote_location: String that represents the Cloud Interconnect remote
      location URL that should be connected to Cloud Interconnect.
      requested_features: List of features requested for this interconnect.

    Returns:
    Insert interconnect tuple that can be used in a request.
    """
    return (self._client.interconnects, 'Insert',
            self._messages.ComputeInterconnectsInsertRequest(
                project=self.ref.project,
                interconnect=self._messages.Interconnect(
                    name=self.ref.Name(),
                    description=description,
                    interconnectType=interconnect_type,
                    linkType=link_type,
                    nocContactEmail=noc_contact_email,
                    requestedLinkCount=requested_link_count,
                    location=location,
                    adminEnabled=admin_enabled,
                    customerName=customer_name,
                    remoteLocation=remote_location,
                    requestedFeatures=requested_features)))

  def _MakePatchRequestTuple(self,
                             description,
                             location,
                             interconnect_type,
                             requested_link_count,
                             link_type,
                             admin_enabled,
                             noc_contact_email,
                             labels,
                             label_fingerprint,
                             macsec_enabled,
                             macsec):
    """Make a tuple for interconnect patch request."""
    kwargs = {}
    if labels is not None:
      kwargs['labels'] = labels
    if label_fingerprint is not None:
      kwargs['labelFingerprint'] = label_fingerprint
    return (self._client.interconnects, 'Patch',
            self._messages.ComputeInterconnectsPatchRequest(
                interconnect=self.ref.Name(),
                interconnectResource=self._messages.Interconnect(
                    name=None,
                    description=description,
                    interconnectType=interconnect_type,
                    linkType=link_type,
                    nocContactEmail=noc_contact_email,
                    requestedLinkCount=requested_link_count,
                    location=location,
                    adminEnabled=admin_enabled,
                    macsecEnabled=macsec_enabled,
                    macsec=macsec,
                    **kwargs),
                project=self.ref.project))

  def _MakeDeleteRequestTuple(self):
    return (self._client.interconnects, 'Delete',
            self._messages.ComputeInterconnectsDeleteRequest(
                project=self.ref.project, interconnect=self.ref.Name()))

  def _MakeDescribeRequestTuple(self):
    return (self._client.interconnects, 'Get',
            self._messages.ComputeInterconnectsGetRequest(
                project=self.ref.project, interconnect=self.ref.Name()))

  def _MakeGetDiagnosticsRequestTuple(self):
    return (self._client.interconnects, 'GetDiagnostics',
            self._messages.ComputeInterconnectsGetDiagnosticsRequest(
                project=self.ref.project, interconnect=self.ref.Name()))

  def _MakeGetMacsecConfigRequestTuple(self):
    return (self._client.interconnects, 'GetMacsecConfig',
            self._messages.ComputeInterconnectsGetMacsecConfigRequest(
                project=self.ref.project, interconnect=self.ref.Name()))

  @property
  def _messages(self):
    return self._compute_client.messages

  def Create(
      self,
      description='',
      location=None,
      interconnect_type=None,
      requested_link_count=None,
      link_type=None,
      admin_enabled=False,
      noc_contact_email=None,
      customer_name=None,
      only_generate_request=False,
      remote_location=None,
      requested_features=None,
  ):
    """Create an interconnect."""
    requests = [
        self._MakeCreateRequestTuple(
            description,
            location,
            interconnect_type,
            requested_link_count,
            link_type,
            admin_enabled,
            noc_contact_email,
            customer_name,
            remote_location,
            requested_features or [],
        )
    ]
    if not only_generate_request:
      resources = self._compute_client.MakeRequests(requests)
      return resources[0]
    return requests

  def Delete(self, only_generate_request=False):
    requests = [self._MakeDeleteRequestTuple()]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def Describe(self, only_generate_request=False):
    requests = [self._MakeDescribeRequestTuple()]
    if not only_generate_request:
      resources = self._compute_client.MakeRequests(requests)
      return resources[0]
    return requests

  def GetDiagnostics(self, only_generate_request=False):
    requests = [self._MakeGetDiagnosticsRequestTuple()]
    if not only_generate_request:
      resources = self._compute_client.MakeRequests(requests)
      return resources[0]
    return requests

  def GetMacsecConfig(self, only_generate_request=False):
    requests = [self._MakeGetMacsecConfigRequestTuple()]
    if not only_generate_request:
      resources = self._compute_client.MakeRequests(requests)
      return resources[0]
    return requests

  def Patch(self,
            description='',
            location=None,
            interconnect_type=None,
            requested_link_count=None,
            link_type=None,
            admin_enabled=False,
            noc_contact_email=None,
            only_generate_request=False,
            labels=None,
            label_fingerprint=None,
            macsec_enabled=None,
            macsec=None):
    """Patch an interconnect."""
    requests = [
        self._MakePatchRequestTuple(description,
                                    location,
                                    interconnect_type,
                                    requested_link_count,
                                    link_type,
                                    admin_enabled,
                                    noc_contact_email,
                                    labels,
                                    label_fingerprint,
                                    macsec_enabled,
                                    macsec)
    ]
    if not only_generate_request:
      resources = self._compute_client.MakeRequests(requests)
      return resources[0]
    return requests
