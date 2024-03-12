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
"""Get a PEM-format certificate chain for a given version."""
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

DETAILED_HELP = {
    'EXAMPLES':
        """\
        The following command saves the Cavium certificate chain for
        CryptoKey ``frodo'' Version 2 to ``/tmp/my/cavium.pem'':

          $ {command} 2 --key=frodo --keyring=fellowship --location=us-east1 --certificate-chain-type=cavium --output-file=/tmp/my/cavium.pem
        """,
}


def _GetCertificateChainPem(chains, chain_type):
  """Returns the specified certificate chain(s) from a CertChains object.

  Args:
    chains: a KeyOperationAttestation.CertChains object.
    chain_type: a string specifying the chain(s) to retrieve.

  Returns:
    A string containing the PEM-encoded certificate chain(s).

  Raises:
    exceptions.InvalidArgumentException if chain_type is not a valid chain type.
  """
  if chain_type == 'cavium':
    return ''.join(chains.caviumCerts)
  elif chain_type == 'google-card':
    return ''.join(chains.googleCardCerts)
  elif chain_type == 'google-partition':
    return ''.join(chains.googlePartitionCerts)
  elif chain_type == 'all':
    return ''.join(chains.caviumCerts + chains.googlePartitionCerts +
                   chains.googleCardCerts)
  raise exceptions.InvalidArgumentException(
      '{} is not a valid chain type.'.format(chain_type))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class GetCertificateChain(base.DescribeCommand):
  r"""Get a certificate chain for a given version.

  Returns the PEM-format certificate chain for the specified key version.
  The optional flag `output-file` indicates the path to store the PEM. If not
  specified, the PEM will be printed to stdout.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddKeyVersionResourceArgument(
        parser, 'from which to get the certificate chain')
    flags.AddCertificateChainFlag(parser)
    flags.AddOutputFileFlag(parser, 'to store PEM')

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    version_ref = flags.ParseCryptoKeyVersionName(args)
    if not version_ref.Name():
      raise exceptions.InvalidArgumentException(
          'version', 'version id must be non-empty.')
    versions = client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    version = versions.Get(
        messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=version_ref.RelativeName()))
    if (version.protectionLevel !=
        messages.CryptoKeyVersion.ProtectionLevelValueValuesEnum.HSM):
      raise kms_exceptions.ArgumentError(
          'Certificate chains are only available for HSM key versions.')
    if (version.state ==
        messages.CryptoKeyVersion.StateValueValuesEnum.PENDING_GENERATION):
      raise kms_exceptions.ArgumentError(
          'Certificate chains are unavailable until the version is generated.')
    try:
      log.WriteToFileOrStdout(
          args.output_file if args.output_file else '-',
          _GetCertificateChainPem(version.attestation.certChains,
                                  args.certificate_chain_type),
          overwrite=True,
          binary=False)
    except files.Error as e:
      raise exceptions.BadFileException(e)
