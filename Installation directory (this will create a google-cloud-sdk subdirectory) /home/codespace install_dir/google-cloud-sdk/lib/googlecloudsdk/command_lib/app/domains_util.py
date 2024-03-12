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
"""Utilities for `gcloud app domain-mappings`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions

NO_CERTIFICATE_ID_MESSAGE = ('A certificate ID cannot be provided when using'
                             ' automatic certificate management.')


def ParseCertificateManagement(messages, certificate_management):
  if not certificate_management:
    return None
  else:
    return messages.SslSettings.SslManagementTypeValueValuesEnum(
        certificate_management.upper())


def ValidateCertificateArgs(certificate_id, certificate_management):
  if (certificate_management and
      certificate_management.upper() == 'AUTOMATIC' and certificate_id):
    raise exceptions.InvalidArgumentException('certificate-id',
                                              NO_CERTIFICATE_ID_MESSAGE)


def ValidateCertificateArgsForUpdate(certificate_id, no_certificate,
                                     certificate_management):
  ValidateCertificateArgs(certificate_id, certificate_management)

  if certificate_management:
    if certificate_management.upper() == 'AUTOMATIC' and no_certificate:
      raise exceptions.InvalidArgumentException('no-certificate-id',
                                                NO_CERTIFICATE_ID_MESSAGE)
    elif (certificate_management.upper() == 'MANUAL'
          and not certificate_id and not no_certificate):
      raise exceptions.InvalidArgumentException(
          'certificate-id',
          ('A certificate ID or no-certificate must be provided when using '
           'manual certificate management.'))
