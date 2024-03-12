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
"""Describe a version."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import exceptions as kms_exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


class Describe(base.DescribeCommand):
  r"""Get metadata for a given version.

  Returns metadata for the given version.

  The optional flag `attestation-file` specifies file to write the attestation
  object into. The attestation object enables the user to verify the integrity
  and provenance of the key. See https://cloud.google.com/kms/docs/attest-key
  for more information about attestations.

  ## EXAMPLES

  The following command returns metadata for version 2 within key `frodo`
  within the keyring `fellowship` in the location `us-east1`:

    $ {command} 2 --key=frodo --keyring=fellowship --location=us-east1

  For key versions with protection level `HSM`, use the `--attestation-file`
  flag to save the attestation to a local file.

    $ {command} 2 --key=frodo --keyring=fellowship --location=us-east1 \
        --attestation-file=path/to/attestation.dat
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyVersionResourceArgument(parser, 'to describe')
    flags.AddAttestationFileFlag(parser)

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    version_ref = flags.ParseCryptoKeyVersionName(args)
    if not version_ref.Name():
      raise exceptions.InvalidArgumentException(
          'version', 'version id must be non-empty.')
    version = client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.Get(  # pylint: disable=line-too-long
        messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=version_ref.RelativeName()))

    # Raise exception if --attestation-file is provided for software
    # key versions.
    if (args.attestation_file and version.protectionLevel !=
        messages.CryptoKeyVersion.ProtectionLevelValueValuesEnum.HSM):
      raise kms_exceptions.ArgumentError(
          'Attestations are only available for HSM key versions.')

    if (args.attestation_file and version.state ==
        messages.CryptoKeyVersion.StateValueValuesEnum.PENDING_GENERATION):
      raise kms_exceptions.ArgumentError(
          'The attestation is unavailable until the version is generated.')

    if args.attestation_file and version.attestation is not None:
      try:
        log.WriteToFileOrStdout(
            args.attestation_file,
            version.attestation.content,
            overwrite=True,
            binary=True)
      except files.Error as e:
        raise exceptions.BadFileException(e)

    if version.attestation is not None:
      # Suppress the attestation content in the printed output. Users can use
      # --attestation-file to obtain it, instead.
      version.attestation.content = None
      # Suppress the attestation content in the printed output. Users can use
      # get-certificate-chain to obtain it, instead.
      version.attestation.certChains = None

    return version
