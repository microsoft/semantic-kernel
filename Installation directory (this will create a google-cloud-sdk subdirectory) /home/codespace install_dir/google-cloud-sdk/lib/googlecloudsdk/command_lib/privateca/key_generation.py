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
"""Key generation utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import sys

from googlecloudsdk.command_lib.privateca import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

KEY_OUTPUT_WARNING = """A private key was exported to {}.

Possession of this key file could allow anybody to act as this certificate's
subject. Please make sure that you store this key file in a secure location at
all times, and ensure that only authorized users have access to it.
"""


def RSAKeyGen(key_size=2048):
  """Generates an RSA public-private key pair.

  Args:
    key_size: The size of the RSA key, in number of bytes. Defaults to 2048.

  Returns:
    A tuple with: (private_key, public_key) both serialized in PKCS1 as bytes.
  """
  import_error_msg = ('Cannot load the Pyca cryptography library. Either the '
                      'library is not installed, or site packages are not '
                      'enabled for the Google Cloud SDK. Please consult Cloud '
                      'KMS documentation on adding Pyca to Google Cloud SDK '
                      'for further instructions.\n'
                      'https://cloud.google.com/kms/docs/crypto')
  try:
    # TODO(b/141249289): Move imports to the top of the file. In the
    # meantime, until we're sure that all Private CA SDK users have the
    # cryptography module available, let's not error out if we can't load the
    # module unless we're actually going down this code path.
    # pylint: disable=g-import-not-at-top
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends.openssl.backend import backend
  except ImportError:
    log.err.Print(import_error_msg)
    sys.exit(1)

  # The serialization modules have moved in cryptography version 3.4 and above.
  # Try both the old and new locations to support both versions. See b/183521338
  # for more context.
  try:
    # pylint: disable=g-import-not-at-top
    from cryptography.hazmat.primitives.serialization.base import Encoding
    from cryptography.hazmat.primitives.serialization.base import PrivateFormat
    from cryptography.hazmat.primitives.serialization.base import PublicFormat
    from cryptography.hazmat.primitives.serialization.base import NoEncryption
  except ImportError:
    try:
      # pylint: disable=g-import-not-at-top
      from cryptography.hazmat.primitives.serialization import Encoding
      from cryptography.hazmat.primitives.serialization import PrivateFormat
      from cryptography.hazmat.primitives.serialization import PublicFormat
      from cryptography.hazmat.primitives.serialization import NoEncryption
    except ImportError:
      log.err.Print(import_error_msg)
      sys.exit(1)

  private_key = rsa.generate_private_key(
      public_exponent=65537, key_size=key_size, backend=backend)

  private_key_bytes = private_key.private_bytes(
      Encoding.PEM,
      PrivateFormat.TraditionalOpenSSL,  # PKCS#1
      NoEncryption())

  public_key_bytes = private_key.public_key().public_bytes(
      Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

  return private_key_bytes, public_key_bytes


def ExportPrivateKey(private_key_output_file, private_key_bytes):
  """Export a private key to a filename, printing a warning to the user.

  Args:
    private_key_output_file: The path of the file to export to.
    private_key_bytes: The content in byte format to export.
  """

  try:
    # Make sure this file is only accesible to the running user before writing.
    files.PrivatizeFile(private_key_output_file)
    files.WriteFileContents(private_key_output_file, private_key_bytes)
    # Make file readable only by owner.
    os.chmod(private_key_output_file, 0o400)
    log.warning(KEY_OUTPUT_WARNING.format(private_key_output_file))
  except (files.Error, OSError, IOError):
    raise exceptions.FileOutputError(
        "Error writing to private key output file named '{}'".format(
            private_key_output_file))
