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
"""Encrypt a plaintext file using a raw key."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import uuid

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import crc32c
from googlecloudsdk.command_lib.kms import e2e_integrity
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files

CBC_CTR_IV_SIZE = 16


class RawEncrypt(base.Command):
  r"""Encrypt a plaintext file using a raw key.

  Encrypts the given plaintext file using the given CryptoKey containing a raw
  key and writes the result to the named ciphertext file.
  The plaintext file must not be larger than 64KiB.
  For the AES-CBC algorithms, no server-side padding is being done,
  so the plaintext must be a multiple of the block size.

  The supported algorithms are: `AES-128-GCM`, `AES-256-GCM`, `AES-128-CBC`,
  `AES-256-CBC`, `AES-128-CTR`, `and AES-256-CTR`.

  `AES-GCM` provides authentication which means that it accepts additional
  authenticated data (AAD). So, the flag `--additional-authenticated-data-file`
  is only valid with `AES-128-GCM` and `AES-256-GCM` algorithms.

  The initialization vector (flag `--initialization-vector-file`) is only
  supported for `AES-CBC` and `AES-CTR` algorithms, and must be 16B in length.

  Therefore, both additional authenticated data and initialization vector can't
  be provided during encryption. If an additional authenticated data file is
  provided, its contents must also be provided during decryption.
  The file must not be larger than 64KiB.

  The flag `--version` indicates the version of the key to use for
  encryption.

  If `--plaintext-file` or `--additional-authenticated-data-file` or
  `--initialization-vector-file` is set to '-', that file is read from stdin.
  Similarly, if `--ciphertext-file` is set to '-', the ciphertext is written
  to stdout.

  By default, the command performs integrity verification on data sent to and
  received from Cloud KMS. Use `--skip-integrity-verification` to disable
  integrity verification.

  ## EXAMPLES
  The following command reads and encrypts the file `path/to/input/plaintext`.
  The file will be encrypted using the `AES-GCM` CryptoKey `KEYNAME` from the
  KeyRing `KEYRING` in the `global` location using the additional authenticated
  data file `path/to/input/aad`.
  The resulting ciphertext will be written to `path/to/output/ciphertext`.

    $ {command} \
        --key=KEYNAME \
        --keyring=KEYRING \
        --location=global \
        --plaintext-file=path/to/input/plaintext \
        --additional-authenticated-data-file=path/to/input/aad \
        --ciphertext-file=path/to/output/ciphertext

  The following command reads and encrypts the file `path/to/input/plaintext`.
  The file will be encrypted using the `AES-CBC` CryptoKey `KEYNAME` from the
  KeyRing `KEYRING` in the `global` location using the initialization vector
  stored at `path/to/input/aad`.
  The resulting ciphertext will be written to `path/to/output/ciphertext`.

    $ {command} \
        --key=KEYNAME \
        --keyring=KEYRING \
        --location=global \
        --plaintext-file=path/to/input/plaintext \
        --initialization-vector-file=path/to/input/iv \
        --ciphertext-file=path/to/output/ciphertext
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyResourceFlags(parser, 'The key to use for encryption.')
    flags.AddCryptoKeyVersionFlag(parser, 'to use for encryption', True)
    flags.AddPlaintextFileFlag(parser, 'to encrypt')
    flags.AddCiphertextFileFlag(parser, 'to output')
    flags.AddIvFileFlag(parser, 'for encryption')
    flags.AddAadFileFlag(parser)
    flags.AddSkipIntegrityVerification(parser)

  def _ReadFileOrStdin(self, path, max_bytes):
    data = console_io.ReadFromFileOrStdin(path, binary=True)
    if len(data) > max_bytes:
      raise exceptions.BadFileException(
          'The file [{0}] is larger than the maximum size of {1} bytes.'.format(
              path, max_bytes
          )
      )
    return data

  def _PerformIntegrityVerification(self, args):
    return not args.skip_integrity_verification

  def _CreateRawEncryptRequest(self, args):
    if (
        args.initialization_vector_file
        and args.additional_authenticated_data_file
    ):
      raise exceptions.InvalidArgumentException(
          '--initialization-vector-file and'
          ' --additional-authenticated-data-file',
          'both parameters cannot be provided simultaneously.',
      )

    if args.plaintext_file == '-' and (
        args.initialization_vector_file == '-'
        or args.additional_authenticated_data_file == '-'
    ):
      raise exceptions.InvalidArgumentException(
          '--plaintext-file', 'multiple parameters cannot be read from stdin.'
      )

    try:
      # The RawEncrypt API limits the plaintext to 64KiB.
      plaintext = self._ReadFileOrStdin(args.plaintext_file, max_bytes=65536)
    except files.Error as e:
      raise exceptions.BadFileException(
          'Failed to read plaintext file [{0}]: {1}'.format(
              args.plaintext_file, e
          )
      )

    aad = b''
    if args.additional_authenticated_data_file:
      try:
        # The RawEncrypt API limits the AAD to 64KiB.
        aad = self._ReadFileOrStdin(
            args.additional_authenticated_data_file, max_bytes=65536
        )
      except files.Error as e:
        raise exceptions.BadFileException(
            'Failed to read additional authenticated data file [{0}]: {1}'
            .format(args.additional_authenticated_data_file, e)
        )

    iv = b''
    if args.initialization_vector_file:
      try:
        # The RawEncrypt API limits the IV to CBC_CTR_IV_SIZE bytes.
        iv = self._ReadFileOrStdin(
            args.initialization_vector_file, max_bytes=CBC_CTR_IV_SIZE
        )
      except files.Error as e:
        raise exceptions.BadFileException(
            'Failed to read initialization vector file [{0}]: {1}'.format(
                args.initialization_vector_file, e
            )
        )

      if len(iv) != CBC_CTR_IV_SIZE:
        raise exceptions.BadFileException(
            '--initialization-vector-file',
            'the IV size must be {0} bytes.'.format(CBC_CTR_IV_SIZE),
        )

    crypto_key_ref = flags.ParseCryptoKeyVersionName(args)
    messages = cloudkms_base.GetMessagesModule()
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsRawEncryptRequest(  # pylint: disable=line-too-long
        name=crypto_key_ref.RelativeName()
    )

    # Populate request integrity fields.
    if self._PerformIntegrityVerification(args):
      plaintext_crc32c = crc32c.Crc32c(plaintext)
      iv_crc32c = crc32c.Crc32c(iv)
      aad_crc32c = crc32c.Crc32c(aad)
      req.rawEncryptRequest = messages.RawEncryptRequest(
          plaintext=plaintext,
          initializationVector=iv,
          additionalAuthenticatedData=aad,
          plaintextCrc32c=plaintext_crc32c,
          initializationVectorCrc32c=iv_crc32c,
          additionalAuthenticatedDataCrc32c=aad_crc32c,
      )
    else:
      req.rawEncryptRequest = messages.RawEncryptRequest(
          plaintext=plaintext,
          initializationVector=iv,
          additionalAuthenticatedData=aad,
      )

    return req

  def _VerifyResponseIntegrityFields(self, req, resp):
    """Verifies integrity fields in RawEncryptResponse.

    Note: This methods assumes that self._PerformIntegrityVerification() is True
    and that all request CRC32C fields were pupolated.
    Args:
      req:
        messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsRawEncryptRequest()
        object
      resp: messages.RawEncryptResponse() object.

    Returns:
      Void.
    Raises:
      e2e_integrity.ServerSideIntegrityVerificationError if the server reports
      request integrity verification error.
      e2e_integrity.ClientSideIntegrityVerificationError if response integrity
      verification fails.
    """

    # Verify resource name.
    if req.name != resp.name:
      raise e2e_integrity.ResourceNameVerificationError(
          e2e_integrity.GetResourceNameMismatchErrorMessage(req.name, resp.name)
      )

    # plaintext_crc32c was verified server-side.
    if not resp.verifiedPlaintextCrc32c:
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetRequestToServerCorruptedErrorMessage()
      )

    # additional_authenticated_data_crc32c was verified server-side.
    if not resp.verifiedAdditionalAuthenticatedDataCrc32c:
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetRequestToServerCorruptedErrorMessage()
      )

    # initialization_vector_crc32c was verified server-side.
    if not resp.verifiedInitializationVectorCrc32c:
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetRequestToServerCorruptedErrorMessage()
      )

    # Verify ciphertext checksum.
    if not crc32c.Crc32cMatches(resp.ciphertext, resp.ciphertextCrc32c):
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetResponseFromServerCorruptedErrorMessage()
      )

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    req = self._CreateRawEncryptRequest(args)
    resp = None
    try:
      resp = client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.RawEncrypt(
          req
      )
    # Intercept INVALID_ARGUMENT errors related to checksum verification, to
    # present a user-friendly message. All other errors are surfaced as-is.
    except apitools_exceptions.HttpBadRequestError as error:
      e2e_integrity.ProcessHttpBadRequestError(error)

    if self._PerformIntegrityVerification(args):
      self._VerifyResponseIntegrityFields(req, resp)

    try:
      log.WriteToFileOrStdout(
          args.ciphertext_file, resp.ciphertext, binary=True, overwrite=True
      )
      # If an initialization vector file is not provided,
      # store the one created during the encrypt in a randomly named file.
      if not args.initialization_vector_file and resp.initializationVector:
        iv_file_name = './inialization_vector_' + str(uuid.uuid4())[:8]
        files.WriteBinaryFileContents(
            iv_file_name,
            resp.initializationVector,
            overwrite=True,
        )
    except files.Error as e:
      raise exceptions.BadFileException(e)
