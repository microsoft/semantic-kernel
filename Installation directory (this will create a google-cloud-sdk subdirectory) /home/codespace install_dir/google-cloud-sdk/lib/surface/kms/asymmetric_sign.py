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
"""Sign a user input file using an asymmetric-signing key."""

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
from googlecloudsdk.command_lib.kms import get_digest
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


class AsymmetricSign(base.Command):
  r"""Sign a user input file using an asymmetric-signing key version.

  Creates a digital signature of the input file using the provided
  asymmetric-signing key version and saves the base64 encoded signature.

  The required flag `signature-file` indicates the path to store signature.

  By default, the command performs integrity verification on data sent to and
  received from Cloud KMS. Use `--skip-integrity-verification` to disable
  integrity verification.

  ## EXAMPLES
  The following command will read the file '/tmp/my/file.to.sign', digest it
  with the digest algorithm 'sha256' and sign it using the asymmetric CryptoKey
  `dont-panic` Version 3, and save the signature in base64 format to
  '/tmp/my/signature'.

    $ {command} \
    --location=us-central1 \
    --keyring=hitchhiker \
    --key=dont-panic \
    --version=3 \
    --digest-algorithm=sha256 \
    --input-file=/tmp/my/file.to.sign \
    --signature-file=/tmp/my/signature

  """

  @staticmethod
  def Args(parser):
    flags.AddKeyResourceFlags(parser, 'to use for signing.')
    flags.AddCryptoKeyVersionFlag(parser, 'to use for signing')
    flags.AddDigestAlgorithmFlag(parser, 'The algorithm to digest the input.')
    flags.AddInputFileFlag(parser, 'to sign')
    flags.AddSignatureFileFlag(parser, 'to output')
    flags.AddSkipIntegrityVerification(parser)

  def _PerformIntegrityVerification(self, args):
    return not args.skip_integrity_verification

  def _SignOnDigest(self, args):
    return args.digest_algorithm is not None

  def _ReadBinaryFile(self, path, max_bytes):
    data = files.ReadBinaryFileContents(path)
    if len(data) > max_bytes:
      raise exceptions.BadFileException(
          'The file [{0}] is larger than the maximum size of {1} bytes.'.format(
              path, max_bytes))
    return data

  def _CreateAsymmetricSignRequestOnDigest(self, args):
    try:
      digest = get_digest.GetDigest(args.digest_algorithm, args.input_file)
    except EnvironmentError as e:
      raise exceptions.BadFileException(
          'Failed to read input file [{0}]: {1}'.format(args.input_file, e))

    messages = cloudkms_base.GetMessagesModule()
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsAsymmetricSignRequest(  # pylint: disable=line-too-long
        name=flags.ParseCryptoKeyVersionName(args).RelativeName())

    if self._PerformIntegrityVerification(args):
      # args.digest_algorithm has been verified in get_digest.GetDigest()
      digest_crc32c = crc32c.Crc32c(getattr(digest, args.digest_algorithm))
      req.asymmetricSignRequest = messages.AsymmetricSignRequest(
          digest=digest, digestCrc32c=digest_crc32c)
    else:
      req.asymmetricSignRequest = messages.AsymmetricSignRequest(digest=digest)

    return req

  def _CreateAsymmetricSignRequestOnData(self, args):
    """Returns an AsymmetricSignRequest for use with a data input.

    Populates an AsymmetricSignRequest with its data field populated by data
    read from args.input_file. dataCrc32c is populated if integrity verification
    is not skipped.

    Args:
      args: Input arguments.

    Returns:
      An AsymmetricSignRequest with data populated and dataCrc32c populated if
      integrity verification is not skipped.

    Raises:
      exceptions.BadFileException: An error occurred reading the input file.
      This can occur if the file can't be read or if the file is larger than
      64 KiB.
    """
    try:
      # The Asymmetric Sign API limits the data input to 64KiB.
      data = self._ReadBinaryFile(args.input_file, max_bytes=65536)
    except files.Error as e:
      raise exceptions.BadFileException(
          'Failed to read input file [{0}]: {1}'.format(args.input_file, e))

    messages = cloudkms_base.GetMessagesModule()
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsAsymmetricSignRequest(  # pylint: disable=line-too-long
        name=flags.ParseCryptoKeyVersionName(args).RelativeName())

    if self._PerformIntegrityVerification(args):
      data_crc32c = crc32c.Crc32c(data)
      req.asymmetricSignRequest = messages.AsymmetricSignRequest(
          data=data, dataCrc32c=data_crc32c)
    else:
      req.asymmetricSignRequest = messages.AsymmetricSignRequest(data=data)

    return req

  def _CreateAsymmetricSignRequest(self, args):
    if self._SignOnDigest(args):
      return self._CreateAsymmetricSignRequestOnDigest(args)
    else:
      return self._CreateAsymmetricSignRequestOnData(args)

  def _VerifyResponseIntegrityFields(self, req, resp, use_digest=True):
    """Verifies integrity fields in AsymmetricSignResponse."""

    # Verify resource name.
    if req.name != resp.name:
      raise e2e_integrity.ResourceNameVerificationError(
          e2e_integrity.GetResourceNameMismatchErrorMessage(
              req.name, resp.name))

    if use_digest:
      # digest_crc32c was verified server-side.
      if not resp.verifiedDigestCrc32c:
        raise e2e_integrity.ClientSideIntegrityVerificationError(
            e2e_integrity.GetRequestToServerCorruptedErrorMessage())
    else:
      # data_crc32c was verified server-side.
      if not resp.verifiedDataCrc32c:
        raise e2e_integrity.ClientSideIntegrityVerificationError(
            e2e_integrity.GetRequestToServerCorruptedErrorMessage())

    # Verify signature checksum.
    if not crc32c.Crc32cMatches(resp.signature, resp.signatureCrc32c):
      raise e2e_integrity.ClientSideIntegrityVerificationError(
          e2e_integrity.GetResponseFromServerCorruptedErrorMessage())

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    req = self._CreateAsymmetricSignRequest(args)
    try:
      resp = (
          client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
          .AsymmetricSign(req))
    # Intercept INVALID_ARGUMENT errors related to checksum verification, to
    # present a user-friendly message. All other errors are surfaced as-is.
    except apitools_exceptions.HttpBadRequestError as error:
      e2e_integrity.ProcessHttpBadRequestError(error)

    if self._PerformIntegrityVerification(args):
      self._VerifyResponseIntegrityFields(
          req, resp, use_digest=self._SignOnDigest(args))

    try:
      log.WriteToFileOrStdout(
          args.signature_file,
          resp.signature,
          overwrite=True,
          binary=True,
          private=True)
    except files.Error as e:
      raise exceptions.BadFileException(e)
