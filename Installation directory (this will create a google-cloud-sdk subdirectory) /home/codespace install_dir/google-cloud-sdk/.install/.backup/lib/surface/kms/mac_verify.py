# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Verify a user signature file using a MAC signing key."""

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


class MacVerify(base.Command):
  r"""Verify a user signature file using a MAC key version.

  Verifies a digital signature using the provided MAC signing key version.

  By default, the command performs integrity verification on data sent to and
  received from Cloud KMS. Use --skip-integrity-verification to disable
  integrity verification.

  ## EXAMPLES
  The following command will read the file '/tmp/my/file.to.verify', and verify
  it using the symmetric MAC CryptoKey `dont-panic` Version 3 and the file
  used previously to generate the MAC tag ('/tmp/my/original.data.file').

    $ {command} \
    --location=us-central1 \
    --keyring=hitchhiker \
    --key=dont-panic \
    --version=3 \
    --input-file=/tmp/my/original.data.file \
    --signature-file=/tmp/my/file.to.verify

  """

  @staticmethod
  def Args(parser):
    flags.AddKeyResourceFlags(parser, 'to use for signing.')
    flags.AddCryptoKeyVersionFlag(parser, 'to use for signing')
    flags.AddInputFileFlag(parser, 'to use for verification')
    flags.AddSignatureFileFlag(parser, 'to be verified')
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

  def _CreateMacVerifyRequest(self, args):
    try:
      # The MacVerify API limits the input data to 64KiB.
      data = self._ReadFileOrStdin(args.input_file, max_bytes=65536)
    except EnvironmentError as e:
      raise exceptions.BadFileException(
          'Failed to read input file [{0}]: {1}'.format(args.input_file, e))
    try:
      # We currently only support signatures up to SHA512 length (64 bytes).
      mac = self._ReadFileOrStdin(args.signature_file, max_bytes=64)
    except EnvironmentError as e:
      raise exceptions.BadFileException(
          'Failed to read input file [{0}]: {1}'.format(args.input_file, e))

    messages = cloudkms_base.GetMessagesModule()
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsMacVerifyRequest(  # pylint: disable=line-too-long
        name=flags.ParseCryptoKeyVersionName(args).RelativeName())

    if self._PerformIntegrityVerification(args):
      data_crc32c = crc32c.Crc32c(data)
      mac_crc32c = crc32c.Crc32c(mac)
      req.macVerifyRequest = messages.MacVerifyRequest(
          data=data, mac=mac, dataCrc32c=data_crc32c, macCrc32c=mac_crc32c)
    else:
      req.macVerifyRequest = messages.MacVerifyRequest(data=data, mac=mac)

    return req

  def _VerifyResponseIntegrityFields(self, req, resp):
    """Verifies integrity fields in MacVerifyResponse."""

    # Verify resource name.
    if req.name != resp.name:
      raise e2e_integrity.ResourceNameVerificationError(
          e2e_integrity.GetResourceNameMismatchErrorMessage(
              req.name, resp.name))

    # data_crc32c was verified server-side.
    if not resp.verifiedDataCrc32c:
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetRequestToServerCorruptedErrorMessage())

    # mac_crc32c was verified server-side.
    if not resp.verifiedMacCrc32c:
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetRequestToServerCorruptedErrorMessage())

    # Verify mac integrity field.
    if resp.success != resp.verifiedSuccessIntegrity:
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetResponseFromServerCorruptedErrorMessage())

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    req = self._CreateMacVerifyRequest(args)
    try:
      resp = (
          client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
          .MacVerify(req))
    # Intercept INVALID_ARGUMENT errors related to checksum verification, to
    # present a user-friendly message. All other errors are surfaced as-is.
    except apitools_exceptions.HttpBadRequestError as error:
      e2e_integrity.ProcessHttpBadRequestError(error)

    if self._PerformIntegrityVerification(args):
      self._VerifyResponseIntegrityFields(req, resp)

    log.WriteToFileOrStdout(
        '-',  # Write to stdout.
        resp.success,
        binary=False)
