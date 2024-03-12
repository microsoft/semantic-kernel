# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Helpers for testing IAM permissions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import iam as kms_iam
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.command_lib.privateca import exceptions

# Permissions needed on a KMS key for creating a CA.
_CA_CREATE_PERMISSIONS_ON_KEY = [
    'cloudkms.cryptoKeys.setIamPolicy',
]

# Permissions needed on a project for creating a CA.
_CA_CREATE_PERMISSIONS_ON_PROJECT = [
    'privateca.certificateAuthorities.create'
]

# Permissions needed on a CA Pool for issuing certificates.
_CERTIFICATE_CREATE_PERMISSIONS_ON_CA_POOL = ['privateca.certificates.create']


def _CheckAllPermissions(actual_permissions, expected_permissions, resource):
  """Raises an exception if the expected permissions are not all present."""
  # IAM won't return more permissions than requested, so equality works here.
  diff = set(expected_permissions) - set(actual_permissions)
  if diff:
    raise exceptions.InsufficientPermissionException(
        resource=resource, missing_permissions=diff)


def CheckCreateCertificateAuthorityPermissions(project_ref, kms_key_ref=None):
  """Ensures that the current user has the required permissions to create a CA.

  Args:
    project_ref: The project where the new CA will be created.
    kms_key_ref: optional, The KMS key that will be used by the CA.

  Raises:
    InsufficientPermissionException: If the user is missing permissions.
  """
  _CheckAllPermissions(
      projects_api.TestIamPermissions(
          project_ref, _CA_CREATE_PERMISSIONS_ON_PROJECT).permissions,
      _CA_CREATE_PERMISSIONS_ON_PROJECT, 'project')
  if kms_key_ref:
    _CheckAllPermissions(
        kms_iam.TestCryptoKeyIamPermissions(
            kms_key_ref, _CA_CREATE_PERMISSIONS_ON_KEY).permissions,
        _CA_CREATE_PERMISSIONS_ON_KEY, 'KMS key')


def CheckCreateCertificatePermissions(issuing_ca_pool_ref):
  """Ensures that the current user can issue a certificate from the given Pool.

  Args:
    issuing_ca_pool_ref: The CA pool that will create the certificate.

  Raises:
    InsufficientPermissionException: If the user is missing permissions.
  """
  client = privateca_base.GetClientInstance(api_version='v1')
  messages = privateca_base.GetMessagesModule(api_version='v1')

  test_response = client.projects_locations_caPools.TestIamPermissions(
      messages.PrivatecaProjectsLocationsCaPoolsTestIamPermissionsRequest(
          resource=issuing_ca_pool_ref.RelativeName(),
          testIamPermissionsRequest=messages.TestIamPermissionsRequest(
              permissions=_CERTIFICATE_CREATE_PERMISSIONS_ON_CA_POOL)))
  _CheckAllPermissions(test_response.permissions,
                       _CERTIFICATE_CREATE_PERMISSIONS_ON_CA_POOL, 'issuing CA')
