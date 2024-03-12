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
"""Update a key version."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import exceptions as kms_exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import maps


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update a key version.

  {command} can be used to update the key versions. Updates can be made to the
  the key versions's state (enabling or disabling it), to its external key
  URI (if the key version has protection level EXTERNAL), or to its ekm
  connection key path (if the key version has protection level EXTERNAL_VPC).

  ## EXAMPLES

  The following command enables the key version 8 of key `frodo`
  within keyring `fellowship` and location `us-east1`:

    $ {command} 8 --location=us-east1 \
                  --keyring=fellowship \
                  --key=frodo \
                  --state=enabled

  The following command disables the key version 8 of key `frodo`
  within keyring `fellowship` and location `us-east1`:

    $ {command} 8 --location=us-east1 \
                  --keyring=fellowship \
                  --key=frodo \
                  --state=disabled

  The following command updates the external key URI of version 8 of key `frodo`
  within keyring `fellowship` and location `us-east1`:

    $ {command} 8 --location=us-east1 \
                  --keyring=fellowship \
                  --key=frodo \
                  --external-key-uri=https://example.kms/v0/some/key/path

  The following command updates the ekm connection key path of version 8 of key
  `bilbo` within keyring `fellowship` and location `us-east1`:

    $ {command} 8 --location=us-east1 \
                  --keyring=fellowship \
                  --key=bilbo \
                  --ekm-connection-key-path=v0/some/key/path
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyVersionResourceArgument(parser, 'to describe')
    flags.AddExternalKeyUriFlag(parser)
    flags.AddEkmConnectionKeyPathFlag(parser)
    flags.AddStateFlag(parser)

  def ProcessFlags(self, args):
    fields_to_update = []

    if args.external_key_uri:
      fields_to_update.append('externalProtectionLevelOptions.externalKeyUri')
    if args.ekm_connection_key_path:
      fields_to_update.append(
          'externalProtectionLevelOptions.ekmConnectionKeyPath')
    if args.state:
      fields_to_update.append('state')

    # Raise an exception when no update field is specified.
    if not fields_to_update:
      raise kms_exceptions.UpdateError(
          'An error occurred: --external-key-uri or --ekm-connection-key-path'
          ' or --state must be specified.')

    return fields_to_update

  def CreateRequest(self, args, messages, fields_to_update):
    # pylint: disable=line-too-long
    version_ref = flags.ParseCryptoKeyVersionName(args)

    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsPatchRequest(
        name=version_ref.RelativeName(),
        cryptoKeyVersion=messages.CryptoKeyVersion(
            state=maps.CRYPTO_KEY_VERSION_STATE_MAPPER.GetEnumForChoice(
                args.state),
            externalProtectionLevelOptions=messages
            .ExternalProtectionLevelOptions(
                externalKeyUri=args.external_key_uri,
                ekmConnectionKeyPath=args.ekm_connection_key_path)))

    req.updateMask = ','.join(fields_to_update)

    return req

  def CheckKeyIsExternal(self, key_version, messages):
    if (key_version.protectionLevel !=
        messages.CryptoKeyVersion.ProtectionLevelValueValuesEnum.EXTERNAL):
      raise kms_exceptions.UpdateError(
          'External key URI updates are only available for key versions '
          'with EXTERNAL protection level')

  def CheckKeyIsExternalVpc(self, key_version, messages):
    if (key_version.protectionLevel !=
        messages.CryptoKeyVersion.ProtectionLevelValueValuesEnum.EXTERNAL_VPC):
      raise kms_exceptions.UpdateError(
          'EkmConnection key path updates are only available for key versions '
          'with EXTERNAL_VPC protection level')

  def Run(self, args):
    # pylint: disable=line-too-long
    fields_to_update = self.ProcessFlags(args)

    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    version_ref = flags.ParseCryptoKeyVersionName(args)

    # Try to get the cryptoKeyVersion and raise an exception if it doesn't exist.
    key_version = client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.Get(
        messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=version_ref.RelativeName()))

    # Check that this key version's ProtectionLevel is EXTERNAL
    if args.external_key_uri:
      self.CheckKeyIsExternal(key_version, messages)

    if args.ekm_connection_key_path:
      self.CheckKeyIsExternalVpc(key_version, messages)

    # Make update request
    update_req = self.CreateRequest(args, messages, fields_to_update)
    return client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.Patch(
        update_req)
