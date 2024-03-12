# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Common command-agnostic utility functions for server-ca-certs commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

ACTIVE_CERT_LABEL = 'Current'
NEXT_CERT_LABEL = 'Next'
PREVIOUS_CERT_LABEL = 'Previous'


def ListServerCas(sql_client, sql_messages, instance_ref):
  """Calls the list server CAs endpoint and returns the response."""
  return sql_client.instances.ListServerCas(
      sql_messages.SqlInstancesListServerCasRequest(
          project=instance_ref.project, instance=instance_ref.instance))


def GetServerCaTypeDict(list_server_cas_response):
  """Gets a dictionary mapping Server CA Cert types to certs.

  The keys to the dictionary returned will be some combinatiaon of 'Current',
  'Next', and 'Previous'.

  Args:
    list_server_cas_response: InstancesListServerCasResponse instance.

  Returns:
    A dictionary mapping Server CA Cert types to SslCert instances.
  """
  server_ca_types = {}

  active_id = list_server_cas_response.activeVersion

  # Get the active cert.
  certs = list_server_cas_response.certs
  active_cert = None
  for cert in certs:
    if cert.sha1Fingerprint == active_id:
      active_cert = cert
      break
  if not active_cert:
    # No server CA types can be discerned; return an empty dict.
    return server_ca_types
  server_ca_types[ACTIVE_CERT_LABEL] = active_cert

  # Get the inactive certs.
  inactive_certs = [cert for cert in certs if cert.sha1Fingerprint != active_id]
  if len(inactive_certs) == 1:
    inactive_cert = inactive_certs[0]
    if inactive_cert.createTime > active_cert.createTime:
      # Found the next cert.
      server_ca_types[NEXT_CERT_LABEL] = inactive_cert
    else:
      # Found the previous cert.
      server_ca_types[PREVIOUS_CERT_LABEL] = inactive_cert
  elif len(inactive_certs) > 1:
    # Sort by expiration date.
    inactive_certs = sorted(inactive_certs, key=lambda cert: cert.createTime)
    server_ca_types[PREVIOUS_CERT_LABEL] = inactive_certs[0]
    server_ca_types[NEXT_CERT_LABEL] = inactive_certs[-1]

  return server_ca_types


def GetCurrentServerCa(sql_client, sql_messages, instance_ref):
  """Returns the currently active Server CA Cert."""
  server_ca_types = GetServerCaTypeDict(
      ListServerCas(sql_client, sql_messages, instance_ref))
  return server_ca_types.get(ACTIVE_CERT_LABEL)


def GetNextServerCa(sql_client, sql_messages, instance_ref):
  """Returns the upcoming Server CA Cert."""
  server_ca_types = GetServerCaTypeDict(
      ListServerCas(sql_client, sql_messages, instance_ref))
  return server_ca_types.get(NEXT_CERT_LABEL)


def GetPreviousServerCa(sql_client, sql_messages, instance_ref):
  """Returns the previously active Server CA Cert."""
  server_ca_types = GetServerCaTypeDict(
      ListServerCas(sql_client, sql_messages, instance_ref))
  return server_ca_types.get(PREVIOUS_CERT_LABEL)
