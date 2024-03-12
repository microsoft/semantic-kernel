# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Import a provided key from file into KMS using an Import Job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import sys

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import maps
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


class Import(base.Command):
  r"""Import a version into an existing crypto key.

  Imports wrapped key material into a new version within an existing crypto key
  following the import procedure documented at
  https://cloud.google.com/kms/docs/importing-a-key.

  ## EXAMPLES

  The following command will read the files 'path/to/ephemeral/key' and
  'path/to/target/key' and use them to create a new version with algorithm
  'google-symmetric-encryption'  within the 'frodo' crypto key, 'fellowship'
  keyring, and 'us-central1' location using import job 'strider' to unwrap the
  provided key material.

    $ {command} --location=global \
         --keyring=fellowship \
         --key=frodo \
         --import-job=strider \
         --wrapped-key-file=path/to/target/key \
         --algorithm=google-symmetric-encryption
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyResourceFlags(parser, 'The containing key to import into.')
    flags.AddCryptoKeyVersionFlag(
        parser, 'to re-import into. Omit this field for first-time import')
    flags.AddRsaAesWrappedKeyFileFlag(parser, 'to import')
    flags.AddWrappedKeyFileFlag(parser, 'to import')
    flags.AddImportedVersionAlgorithmFlag(parser)
    flags.AddRequiredImportJobArgument(parser, 'to import from')
    flags.AddPublicKeyFileFlag(parser)
    flags.AddTargetKeyFileFlag(parser)

  def _ReadFile(self, path, max_bytes):
    data = files.ReadBinaryFileContents(path)
    if len(data) > max_bytes:
      raise exceptions.BadFileException(
          'The file is larger than the maximum size of {0} bytes.'.format(
              max_bytes))
    return data

  def _IsSha2ImportMethod(self, import_method, messages):
    return import_method in (
        messages.ImportJob.ImportMethodValueValuesEnum.RSA_OAEP_3072_SHA256,
        messages.ImportJob.ImportMethodValueValuesEnum.RSA_OAEP_4096_SHA256,
        messages.ImportJob.ImportMethodValueValuesEnum
        .RSA_OAEP_3072_SHA256_AES_256, messages.ImportJob
        .ImportMethodValueValuesEnum.RSA_OAEP_4096_SHA256_AES_256)

  def _IsRsaAesWrappingImportMethod(self, import_method, messages):
    return import_method in (messages.ImportJob.ImportMethodValueValuesEnum
                             .RSA_OAEP_3072_SHA1_AES_256,
                             messages.ImportJob.ImportMethodValueValuesEnum
                             .RSA_OAEP_4096_SHA1_AES_256,
                             messages.ImportJob.ImportMethodValueValuesEnum
                             .RSA_OAEP_3072_SHA256_AES_256,
                             messages.ImportJob.ImportMethodValueValuesEnum
                             .RSA_OAEP_4096_SHA256_AES_256)

  def _ReadPublicKeyBytes(self, args):
    try:
      return self._ReadFile(args.public_key_file, max_bytes=65536)
    except files.Error as e:
      raise exceptions.BadFileException(
          'Failed to read public key file [{0}]: {1}'.format(
              args.public_key_file, e))

  def _FetchImportJob(self, args, import_job_name, client, messages):
    import_job = client.projects_locations_keyRings_importJobs.Get(
        messages.CloudkmsProjectsLocationsKeyRingsImportJobsGetRequest(
            name=import_job_name))
    if import_job.state != messages.ImportJob.StateValueValuesEnum.ACTIVE:
      raise exceptions.BadArgumentException(
          'import-job', 'Import job [{0}] is not active (state is {1}).'.format(
              import_job_name, import_job.state))
    return import_job

  def _CkmRsaAesKeyWrap(self, import_method, public_key_bytes, target_key_bytes,
                        client, messages):
    try:
      # TODO(b/141249289): Move imports to the top of the file. In the
      # meantime, until we're sure that all Cloud SDK users have the
      # cryptography module available, let's not error out if we can't load the
      # module unless we're actually going down this code path.
      # pylint: disable=g-import-not-at-top
      from cryptography.hazmat.primitives import serialization
      from cryptography.hazmat.backends import default_backend
      from cryptography.hazmat.primitives import keywrap
      from cryptography.hazmat.primitives.asymmetric import padding
      from cryptography.hazmat.primitives import hashes
    except ImportError:
      log.err.Print('Cannot load the Pyca cryptography library. Either the '
                    'library is not installed, or site packages are not '
                    'enabled for the Google Cloud SDK. Please consult '
                    'https://cloud.google.com/kms/docs/crypto for further '
                    'instructions.')
      sys.exit(1)

    sha = hashes.SHA1()
    if self._IsSha2ImportMethod(import_method, messages):
      sha = hashes.SHA256()

    # RSA-OAEP import methods have a maximum target key size that's a function
    # of the RSA modulus size.
    if not self._IsRsaAesWrappingImportMethod(import_method, messages):
      if (
          import_method
          == messages.ImportJob.ImportMethodValueValuesEnum.RSA_OAEP_3072_SHA256
      ):
        modulus_byte_length = 3072 // 8
      elif (
          import_method
          == messages.ImportJob.ImportMethodValueValuesEnum.RSA_OAEP_4096_SHA256
      ):
        modulus_byte_length = 4096 // 8
      else:
        raise ValueError('unexpected import method: {0}'.format(import_method))
      # per go/rfc/8017#section-7.1.1
      max_target_key_size = modulus_byte_length - (2 * sha.digest_size) - 2
      if len(target_key_bytes) > max_target_key_size:
        raise exceptions.BadFileException(
            'target-key-file',
            "The file is larger than the import method's maximum size of {0} "
            'bytes.'.format(max_target_key_size),
        )

    aes_wrapped_key = b''
    to_be_rsa_wrapped_key = target_key_bytes
    public_key = serialization.load_pem_public_key(
        public_key_bytes, backend=default_backend())
    if self._IsRsaAesWrappingImportMethod(import_method, messages):
      to_be_rsa_wrapped_key = os.urandom(32)  # an ephemeral key
      aes_wrapped_key = keywrap.aes_key_wrap_with_padding(
          to_be_rsa_wrapped_key, target_key_bytes, default_backend())
    rsa_wrapped_key = public_key.encrypt(
        to_be_rsa_wrapped_key,
        padding.OAEP(mgf=padding.MGF1(sha), algorithm=sha, label=None))
    return rsa_wrapped_key + aes_wrapped_key

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    import_job_name = flags.ParseImportJobName(args).RelativeName()

    # set wrapped_key_file to wrapped_key_file or rsa_aes_wrapped_key_file
    wrapped_key_file = None
    if args.wrapped_key_file:
      wrapped_key_file = args.wrapped_key_file
      if args.rsa_aes_wrapped_key_file:
        raise exceptions.OneOfArgumentsRequiredException(
            ('--wrapped-key-file', '--rsa-aes-wrapped-key-file'),
            'Either wrapped-key-file or rsa-aes-wrapped-key-file should be provided.')  # pylint: disable=line-too-long
    else:
      wrapped_key_file = args.rsa_aes_wrapped_key_file

    if bool(wrapped_key_file) == bool(args.target_key_file):
      raise exceptions.OneOfArgumentsRequiredException(
          ('--target-key-file', '--wrapped-key-file/--rsa-aes-wrapped-key-file'),  # pylint: disable=line-too-long
          'Either a pre-wrapped key or a key to be wrapped must be provided.')

    wrapped_key_bytes = None
    if wrapped_key_file:
      try:
        # This should be less than 64KiB.
        wrapped_key_bytes = self._ReadFile(wrapped_key_file, max_bytes=65536)
      except files.Error as e:
        raise exceptions.BadFileException(
            'Failed to read wrapped key file [{0}]: {1}'.format(
                wrapped_key_file, e))

    import_job = self._FetchImportJob(args, import_job_name, client, messages)
    if args.target_key_file:
      target_key_bytes = None
      try:
        # This should be less than 64KiB.
        target_key_bytes = self._ReadFile(args.target_key_file, max_bytes=8192)
      except files.Error as e:
        raise exceptions.BadFileException(
            'Failed to read target key file [{0}]: {1}'.format(
                args.target_key_file, e))

      # Read the public key off disk if provided, otherwise, fetch it from KMS.
      public_key_bytes = None
      if args.public_key_file:
        public_key_bytes = self._ReadPublicKeyBytes(args)
      else:
        public_key_bytes = import_job.publicKey.pem.encode('ascii')

      wrapped_key_bytes = self._CkmRsaAesKeyWrap(import_job.importMethod,
                                                 public_key_bytes,
                                                 target_key_bytes, client,
                                                 messages)

    # Send the request to KMS.
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsImportRequest(  # pylint: disable=line-too-long
        parent=flags.ParseCryptoKeyName(args).RelativeName())
    req.importCryptoKeyVersionRequest = messages.ImportCryptoKeyVersionRequest(
        algorithm=maps.ALGORITHM_MAPPER_FOR_IMPORT.GetEnumForChoice(
            args.algorithm),
        importJob=import_job_name,
        wrappedKey=wrapped_key_bytes)

    if args.version:
      req.importCryptoKeyVersionRequest.cryptoKeyVersion = flags.ParseCryptoKeyVersionName(
          args).RelativeName()

    return client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.Import(
        req)
