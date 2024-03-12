# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Helpers for parsing certificates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import files
import six


def GetDerCertificate(certificate_file):
  """Read certificate_file and return the certificate in DER encoding.

  Args:
    certificate_file: A file handle to the certificate in PEM or DER format.

  Returns:
    The certificate in DER encoding.

  Raises:
    BadArgumentException: The provided certificate failed to parse as a PEM.
  """
  data = files.ReadBinaryFileContents(certificate_file)
  if b'-----BEGIN CERTIFICATE-----' in data:
    certb64 = data.replace(b'-----BEGIN CERTIFICATE-----', b'', 1)
    certb64 = certb64.replace(b'-----END CERTIFICATE-----', b'', 1)
    # If there's another certificate detected afterwards
    if b'-----BEGIN CERTIFICATE-----' in certb64:
      raise exceptions.BadArgumentException(
          'certificate_file',
          'Cannot place multiple certificates in the same file : {}'.format(
              certificate_file))
    try:
      certb64 = certb64.replace(b'\r', b'').replace(b'\n', b'')
      # Since validate=True isn't supported on Python2's base64.b64decode,
      # re-encode output and compare to original.
      decoded = base64.b64decode(six.ensure_binary(certb64))
      encoded = base64.b64encode(decoded)
      if encoded != certb64:
        raise ValueError('Non-base64 digit found.')
    except Exception as e:
      raise exceptions.BadArgumentException(
          'certificate_file',
          'Recognized {} as a PEM file but failed during parsing : {}'.format(
              certificate_file, e))
    return decoded
  else:
    return data
