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
"""Encrypt a plaintext file using a key."""

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


class Encrypt(base.Command):
  r"""Encrypt a plaintext file using a key.

  Encrypts the given plaintext file using the given CryptoKey and writes the
  result to the named ciphertext file. The plaintext file must not be larger
  than 64KiB.

  If an additional authenticated data file is provided, its contents must also
  be provided during decryption. The file must not be larger than 64KiB.

  The flag `--version` indicates the version of the key to use for
  encryption. By default, the primary version is used.

  If `--plaintext-file` or `--additional-authenticated-data-file` is set to '-',
  that file is read from stdin. Similarly, if `--ciphertext-file` is set to '-',
  the ciphertext is written to stdout.

  By default, the command performs integrity verification on data sent to and
  received from Cloud KMS. Use `--skip-integrity-verification` to disable
  integrity verification.

  ## EXAMPLES
  The following command will read the file 'path/to/plaintext', encrypt it using
  the CryptoKey `frodo` with the KeyRing `fellowship` and Location `global`, and
  write the ciphertext to 'path/to/ciphertext'.

    $ {command} \
        --key=frodo \
        --keyring=fellowship \
        --location=global \
        --plaintext-file=path/to/input/plaintext \
        --ciphertext-file=path/to/output/ciphertext
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyResourceFlags(parser, 'The key to use for encryption.')
    flags.AddCryptoKeyVersionFlag(parser, 'to use for encryption')
    flags.AddPlaintextFileFlag(parser, 'to encrypt')
    flags.AddCiphertextFileFlag(parser, 'to output')
    flags.AddAadFileFlag(parser)
    flags.AddSkipIntegrityVerification(parser)

  def _ReadFileOrStdin(self, path, max_bytes):
    data = console_io.ReadFromFileOrStdin(path, binary=True)
    if len(data) > max_bytes:
      raise exceptions.BadFileException(
          'The file [{0}] is larger than the maximum size of {1} bytes.'.format(
              path, max_bytes))
    return data

  def _PerformIntegrityVerification(self, args):
    return not args.skip_integrity_verification

  def _MaybeStripResourceVersion(self, req_name, resp_name):
    """Strips the trailing '/cryptoKeyVersions/xx' from Response's resource name.

    If request's resource name is a key and not a version, returns response's
    resource name with the trailing '/cryptoKeyVersions/xx' suffix stripped.
    Args:
      req_name: String.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysEncryptRequest.name.
      resp_name: String. EncryptResponse.name.

    Returns:
      resp_resource_name with '/cryptoKeyVersions/xx' suffix stripped.
    """
    if req_name.find('/cryptoKeyVersions/') == -1:
      return resp_name.partition('/cryptoKeyVersions/')[0]
    else:
      return resp_name

  def _CreateEncryptRequest(self, args):
    if (args.plaintext_file == '-' and
        args.additional_authenticated_data_file == '-'):
      raise exceptions.InvalidArgumentException(
          '--plaintext-file',
          '--plaintext-file and --additional-authenticated-data-file cannot '
          'both read from stdin.')

    try:
      # The Encrypt API limits the plaintext to 64KiB.
      plaintext = self._ReadFileOrStdin(args.plaintext_file, max_bytes=65536)
    except files.Error as e:
      raise exceptions.BadFileException(
          'Failed to read plaintext file [{0}]: {1}'.format(
              args.plaintext_file, e))

    aad = None
    if args.additional_authenticated_data_file:
      try:
        # The Encrypt API limits the AAD to 64KiB.
        aad = self._ReadFileOrStdin(
            args.additional_authenticated_data_file, max_bytes=65536)

      except files.Error as e:
        raise exceptions.BadFileException(
            'Failed to read additional authenticated data file [{0}]: {1}'
            .format(args.additional_authenticated_data_file, e))

    if args.version:
      crypto_key_ref = flags.ParseCryptoKeyVersionName(args)
    else:
      crypto_key_ref = flags.ParseCryptoKeyName(args)

    messages = cloudkms_base.GetMessagesModule()

    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysEncryptRequest(
        name=crypto_key_ref.RelativeName())

    # Populate request integrity fields.
    if self._PerformIntegrityVerification(args):
      plaintext_crc32c = crc32c.Crc32c(plaintext)
      # Set checksum if AAD is not provided for simpler response verification.
      aad_crc32c = crc32c.Crc32c(aad) if aad is not None else crc32c.Crc32c(b'')
      req.encryptRequest = messages.EncryptRequest(
          plaintext=plaintext,
          additionalAuthenticatedData=aad,
          plaintextCrc32c=plaintext_crc32c,
          additionalAuthenticatedDataCrc32c=aad_crc32c)
    else:
      req.encryptRequest = messages.EncryptRequest(
          plaintext=plaintext, additionalAuthenticatedData=aad)

    return req

  def _VerifyResponseIntegrityFields(self, req, resp):
    """Verifies integrity fields in EncryptResponse.

    Note: This methods assumes that self._PerformIntegrityVerification() is True
    and that all request CRC32C fields were pupolated.
    Args:
      req: messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysEncryptRequest()
        object
      resp: messages.EncryptResponse() object.

    Returns:
      Void.
    Raises:
      e2e_integrity.ServerSideIntegrityVerificationError if the server reports
      request integrity verification error.
      e2e_integrity.ClientSideIntegrityVerificationError if response integrity
      verification fails.
    """

    # Verify resource name.
    # Strip version from resp.name if --key was provided.
    resp_name = self._MaybeStripResourceVersion(req.name, resp.name)
    if req.name != resp_name:
      raise e2e_integrity.ResourceNameVerificationError(
          e2e_integrity.GetResourceNameMismatchErrorMessage(
              req.name, resp_name))

    # plaintext_crc32c was verified server-side.
    if not resp.verifiedPlaintextCrc32c:
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetRequestToServerCorruptedErrorMessage())

    # additional_authenticated_data_crc32c was verified server-side.
    if not resp.verifiedAdditionalAuthenticatedDataCrc32c:
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetRequestToServerCorruptedErrorMessage())

    # Verify ciphertext checksum.
    if not crc32c.Crc32cMatches(resp.ciphertext, resp.ciphertextCrc32c):
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetResponseFromServerCorruptedErrorMessage())

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    req = self._CreateEncryptRequest(args)
    try:
      resp = client.projects_locations_keyRings_cryptoKeys.Encrypt(req)
    # Intercept INVALID_ARGUMENT errors related to checksum verification, to
    # present a user-friendly message. All other errors are surfaced as-is.
    except apitools_exceptions.HttpBadRequestError as error:
      e2e_integrity.ProcessHttpBadRequestError(error)

    if self._PerformIntegrityVerification(args):
      self._VerifyResponseIntegrityFields(req, resp)

    try:
      log.WriteToFileOrStdout(
          args.ciphertext_file, resp.ciphertext, binary=True, overwrite=True)
    except files.Error as e:
      raise exceptions.BadFileException(e)
