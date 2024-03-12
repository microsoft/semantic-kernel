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
"""General utilities for Certificate Manager commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.certificate_manager import api_client
from googlecloudsdk.api_lib.certificate_manager import operations
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

_OPERATIONS_COLLECTION = 'certificatemanager.projects.locations.operations'
_CERTIFICATE_MAPS_COLLECTION = 'certificatemanager.projects.locations.certificateMaps'
_CERTIFICATE_MAP_ENTRIES_COLLECTION = 'certificatemanager.projects.locations.certificateMaps.certificateMapEntries'
_CERTIFICATES_COLLECTION = 'certificatemanager.projects.locations.certificates'
_PROJECT = lambda: properties.VALUES.core.project.Get(required=True)


def _GetRegistry():
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName('certificatemanager', api_client.API_VERSION)
  return registry


def _ParseOperation(operation):
  return _GetRegistry().Parse(
      operation,
      params={
          'projectsId': _PROJECT,
          'locationsId': 'global'
      },
      collection=_OPERATIONS_COLLECTION)


def _ParseCertificateMap(certificate_map):
  return _GetRegistry().Parse(
      certificate_map,
      params={
          'projectsId': _PROJECT,
          'locationsId': 'global'
      },
      collection=_CERTIFICATE_MAPS_COLLECTION)


def _ParseCertificateMapEntry(certificate_map_entry):
  return _GetRegistry().Parse(
      certificate_map_entry,
      params={
          'projectsId': _PROJECT,
          'locationsId': 'global',
          'certificateMapId': _CERTIFICATE_MAPS_COLLECTION,
      },
      collection=_CERTIFICATE_MAP_ENTRIES_COLLECTION)


def _ParseCertificate(certificate):
  return _GetRegistry().Parse(
      certificate,
      params={
          'projectsId': _PROJECT,
          'locationsId': 'global'
      },
      collection=_CERTIFICATES_COLLECTION)


def WaitForOperation(response, is_async=False):
  """Handles waiting for the operation and printing information about it.

  Args:
    response: Response from the API call
    is_async: If true, do not wait for the operation

  Returns:
    The last information about the operation.
  """
  operation_ref = _ParseOperation(response.name)
  if is_async:
    log.status.Print('Started \'{}\''.format(operation_ref.Name()))
  else:
    message = 'Waiting for \'{}\' to complete'
    operations_client = operations.OperationClient()
    response = operations_client.WaitForOperation(
        operation_ref, message.format(operation_ref.Name()))
  return response


def CertificateMapUriFunc(resource):
  return _ParseCertificateMap(resource.name).SelfLink()


def CertificateMapEntryUriFunc(resource):
  return _ParseCertificateMapEntry(resource.name).SelfLink()


def CertificateUriFunc(resource):
  return _ParseCertificate(resource.name).SelfLink()
