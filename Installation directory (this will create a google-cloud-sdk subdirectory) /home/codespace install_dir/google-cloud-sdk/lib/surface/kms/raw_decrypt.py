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
"""Decrypt a ciphertext file using a raw key."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

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


class RawDecrypt(base.Command):
  r"""Decrypt a ciphertext file using a raw key.

  `{command}` decrypts the given ciphertext file using the given CryptoKey
  containing a raw key and writes the result to the named plaintext file.
  The ciphertext file must not be larger than 64KiB.

  The supported algorithms are: `AES-128-GCM`, `AES-256-GCM`, `AES-128-CBC`,
  `AES-256-CBC`, `AES-128-CTR`, `and AES-256-CTR`.

  `AES-GCM` provides authentication which means that it accepts additional
  authenticated data (AAD). So, the flag `--additional-authenticated-data-file`
  is only valid with `AES-128-GCM` and `AES-256-GCM` algorithms. If AAD is
  provided during encryption, it must be provided during decryption too.
  The file must not be larger than 64KiB.

  If `--plaintext-file` or `--additional-authenticated-data-file` or
  `--initialization-vector-file` is set to '-', that file is read from stdin.
  Similarly, if `--ciphertext-file` is set to '-', the ciphertext is written
  to stdout.

  By default, the command performs integrity verification on data sent to and
  received from Cloud KMS. Use `--skip-integrity-verification` to disable
  integrity verification.

  ## EXAMPLES
  The following command reads and decrypts the file `path/to/input/ciphertext`.
  The file will be decrypted using the CryptoKey `KEYNAME` containing a raw key,
  from the KeyRing `KEYRING` in the `global` location. It uses the additional
  authenticated data file `path/to/input/aad` (only valid with the `AES-GCM`
  algorithms) and the initialization vector file `path/to/input/iv`.
  The resulting plaintext will be written to `path/to/output/plaintext`.

    $ {command} \
        --key=KEYNAME \
        --keyring=KEYRING \
        --location=global \
        --ciphertext-file=path/to/input/ciphertext \
        --additional-authenticated-data-file=path/to/input/aad \
        --initialization-vector-file=path/to/input/iv \
        --plaintext-file=path/to/output/plaintext
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyResourceFlags(parser, 'The (raw) key to use for decryption.')
    flags.AddCryptoKeyVersionFlag(parser, 'to use for decryption', True)
    flags.AddPlaintextFileFlag(parser, 'to store the decrypted data')
    flags.AddCiphertextFileFlag(parser, 'to decrypt')
    flags.AddIvFileFlag(parser, 'for decryption')
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

  def _CreateRawDecryptRequest(self, args):
    if args.ciphertext_file == '-' and args.initialization_vector_file == '-':
      raise exceptions.InvalidArgumentException(
          '--ciphertext-file and --initialization-vector-file',
          "both parameters can't be read from stdin.",
      )

    if (
        args.ciphertext_file == '-'
        and args.additional_authenticated_data_file == '-'
    ):
      raise exceptions.InvalidArgumentException(
          '--ciphertext-file and --additional-authenticated-data-file',
          "both parameters can't be read from stdin.",
      )

    if (
        args.initialization_vector_file == '-'
        and args.additional_authenticated_data_file == '-'
    ):
      raise exceptions.InvalidArgumentException(
          '--initialization-vector-file and'
          ' --additional-authenticated-data-file',
          "both parameters can't be read from stdin.",
      )

    try:
      # The Encrypt API has a limit of 64KB; the output ciphertext files will be
      # slightly larger. Check proactively (but generously) to avoid attempting
      # to buffer and send obviously oversized files to KMS.
      ciphertext = self._ReadFileOrStdin(
          args.ciphertext_file, max_bytes=2 * 65536
      )
    except files.Error as e:
      raise exceptions.BadFileException(
          'Failed to read ciphertext file [{0}]: {1}'.format(
              args.ciphertext_file, e
          )
      )

    try:
      # The RawDecrypt API limits the IV to 16B.
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

    aad = b''
    if args.additional_authenticated_data_file:
      try:
        # The RawDecrypt API limits the AAD to 64KiB.
        aad = self._ReadFileOrStdin(
            args.additional_authenticated_data_file, max_bytes=65536
        )
      except files.Error as e:
        raise exceptions.BadFileException(
            'Failed to read additional authenticated data file [{0}]: {1}'
            .format(args.additional_authenticated_data_file, e)
        )

    crypto_key_ref = flags.ParseCryptoKeyVersionName(args)
    messages = cloudkms_base.GetMessagesModule()
    request = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsRawDecryptRequest(  # pylint: disable=line-too-long
        name=crypto_key_ref.RelativeName()
    )

    # Populate request integrity fields.
    if self._PerformIntegrityVerification(args):
      ciphertext_crc32c = crc32c.Crc32c(ciphertext)
      iv_crc32c = crc32c.Crc32c(iv)
      aad_crc32c = crc32c.Crc32c(aad)
      request.rawDecryptRequest = messages.RawDecryptRequest(
          ciphertext=ciphertext,
          initializationVector=iv,
          additionalAuthenticatedData=aad,
          ciphertextCrc32c=ciphertext_crc32c,
          initializationVectorCrc32c=iv_crc32c,
          additionalAuthenticatedDataCrc32c=aad_crc32c,
      )
    else:
      request.rawDecryptRequest = messages.RawDecryptRequest(
          ciphertext=ciphertext,
          initializationVector=iv,
          additionalAuthenticatedData=aad,
      )

    return request

  def _VerifyResponseIntegrityFields(self, resp):
    """Verifies integrity fields in response."""

    # plaintext_crc32c was verified server-side.
    if not resp.verifiedCiphertextCrc32c:
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

    # Verify decrypted plaintext checksum.
    if not crc32c.Crc32cMatches(resp.plaintext, resp.plaintextCrc32c):
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetResponseFromServerCorruptedErrorMessage()
      )

  def Run(self, args):
    response = None
    request = self._CreateRawDecryptRequest(args)
    client = cloudkms_base.GetClientInstance()
    try:
      response = client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.RawDecrypt(
          request
      )  # pylint: disable=line-too-long
    # Intercept INVALID_ARGUMENT errors related to checksum verification to
    # present a user-friendly message. All other errors are surfaced as-is.
    except apitools_exceptions.HttpBadRequestError as error:
      e2e_integrity.ProcessHttpBadRequestError(error)

    if self._PerformIntegrityVerification(args):
      self._VerifyResponseIntegrityFields(response)

    try:
      if response.plaintext is None:
        with files.FileWriter(args.plaintext_file):
          # to create an empty file
          pass
        log.Print('Decrypted file is empty')
      else:
        log.WriteToFileOrStdout(
            args.plaintext_file, response.plaintext, binary=True, overwrite=True
        )
    except files.Error as e:
      raise exceptions.BadFileException(e)
