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
"""Create a new version."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import exceptions as kms_exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create a new version.

  Creates a new version within the given key.

  ## EXAMPLES

  The following command creates a new version within the `frodo`
  key, `fellowship` keyring, and `global` location and sets it as
  the primary version:

    $ {command} --location=global \
        --keyring=fellowship \
        --key=frodo --primary

  The following command creates a new version within the `legolas`
  key, `fellowship` keyring, `us-central1` location,
  `https://example.kms/v0/some/key/path` as the address for its external key,
  and sets it as the key's primary version:

    $ {command} --location=us-central1 \
        --keyring=fellowship \
        --key=legolas \
        --external-key-uri=https://example.kms/v0/some/key/path \
        --primary

  The following command creates a new version within the `bilbo`
  key, `fellowship` keyring, `us-central1` location,
  `v0/some/key/path` as the ekm connection key path for its external key,
  and sets it as the key's primary version:

    $ {command} --location=us-central1 \
        --keyring=fellowship \
        --key=bilbo \
        --ekm-connection-key-path=v0/some/key/path \
        --primary
  """

  GOOGLE_SYMMETRIC_ENCRYPTION = (
      cloudkms_base.GetMessagesModule().CryptoKeyVersion.AlgorithmValueValuesEnum.GOOGLE_SYMMETRIC_ENCRYPTION
  )

  SYMMETRIC_NEW_PRIMARY_MESSAGE = (
      'Successfully created key version [{version}] and set it as the primary '
      'version. Future encryption requests will use [{version}] until the next '
      'key rotation. Data that was encrypted with an older key version can '
      'still be decrypted, and Cloud KMS will automatically choose the correct '
      'key for decryption based on the ciphertext.')

  @staticmethod
  def Args(parser):
    flags.AddKeyResourceFlags(parser)
    flags.AddExternalKeyUriFlag(parser)
    flags.AddEkmConnectionKeyPathFlag(parser)
    parser.add_argument(
        '--primary',
        action='store_true',
        help=(
            'If specified, immediately makes the new version primary. '
            'This should only be used with the `encryption` purpose.'
        ),
    )

  def _CreateCreateCKVRequest(self, args):
    # pylint: disable=line-too-long
    messages = cloudkms_base.GetMessagesModule()
    crypto_key_ref = flags.ParseCryptoKeyName(args)

    if args.external_key_uri and args.ekm_connection_key_path:
      raise kms_exceptions.ArgumentError(
          'Can not specify both --external-key-uri and '
          '--ekm-connection-key-path.')

    if args.external_key_uri or args.ekm_connection_key_path:
      return messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsCreateRequest(
          parent=crypto_key_ref.RelativeName(),
          cryptoKeyVersion=messages.CryptoKeyVersion(
              externalProtectionLevelOptions=messages
              .ExternalProtectionLevelOptions(
                  externalKeyUri=args.external_key_uri,
                  ekmConnectionKeyPath=args.ekm_connection_key_path)))

    return messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsCreateRequest(
        parent=crypto_key_ref.RelativeName())

  def Run(self, args):
    # pylint: disable=line-too-long
    client = cloudkms_base.GetClientInstance()
    ckv = client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    new_ckv = ckv.Create(self._CreateCreateCKVRequest(args))

    if args.primary:
      version_id = new_ckv.name.split('/')[-1]
      crypto_key_ref = flags.ParseCryptoKeyName(args)
      messages = cloudkms_base.GetMessagesModule()

      req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysUpdatePrimaryVersionRequest(
          name=crypto_key_ref.RelativeName(),
          updateCryptoKeyPrimaryVersionRequest=(
              messages.UpdateCryptoKeyPrimaryVersionRequest(
                  cryptoKeyVersionId=version_id)))
      client.projects_locations_keyRings_cryptoKeys.UpdatePrimaryVersion(req)

      if new_ckv.algorithm == self.GOOGLE_SYMMETRIC_ENCRYPTION:
        log.err.Print(
            self.SYMMETRIC_NEW_PRIMARY_MESSAGE.format(version=version_id))

    return new_ckv
