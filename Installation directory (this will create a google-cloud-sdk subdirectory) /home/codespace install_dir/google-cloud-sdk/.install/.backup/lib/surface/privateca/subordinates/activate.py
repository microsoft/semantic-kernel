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
"""Activate a pending certificate authority."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import create_utils
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import pem_utils
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Activate(base.SilentCommand):
  r"""Activate a subordinate certificate authority awaiting user activation.

  ## EXAMPLES

  To activate a subordinate CA named 'server-tls-1' in the location 'us-west1'

  and CA Pool 'server-tls-pool' using a PEM certificate chain in 'chain.crt':

    $ {command} server-tls-1 \
      --location=us-west1 \
      --pool=server-tls-pool \
      --pem-chain=./chain.crt
  """

  def __init__(self, *args, **kwargs):
    super(Activate, self).__init__(*args, **kwargs)
    self.client = privateca_base.GetClientInstance(api_version='v1')
    self.messages = privateca_base.GetMessagesModule(api_version='v1')

  @staticmethod
  def Args(parser):
    resource_args.AddCertAuthorityPositionalResourceArg(parser, 'to activate')
    base.Argument(
        '--pem-chain',
        required=True,
        help=(
            'A file containing a list of PEM-encoded certificates, starting '
            'with the current CA certificate and ending with the root CA '
            'certificate.'
        ),
    ).AddToParser(parser)
    flags.AddAutoEnableFlag(parser)

  def _ParsePemChainFromFile(self, pem_chain_file):
    """Parses a pem chain from a file, splitting the leaf cert and chain.

    Args:
      pem_chain_file: file containing the pem_chain.

    Raises:
      exceptions.InvalidArgumentException if not enough certificates are
      included.

    Returns:
      A tuple with (leaf_cert, rest_of_chain)
    """
    try:
      pem_chain_input = files.ReadFileContents(pem_chain_file)
    except (files.Error, OSError, IOError):
      raise exceptions.BadFileException(
          "Could not read provided PEM chain file '{}'.".format(pem_chain_file)
      )

    certs = pem_utils.ValidateAndParsePemChain(pem_chain_input)
    if len(certs) < 2:
      raise exceptions.InvalidArgumentException(
          'pem-chain',
          'The pem_chain must include at least two certificates - the'
          ' subordinate CA certificate and an issuer certificate.',
      )

    return certs[0], certs[1:]

  def _EnableCertificateAuthority(self, ca_name):
    """Enables the given CA."""
    enable_request = self.messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesEnableRequest(
        name=ca_name,
        enableCertificateAuthorityRequest=self.messages.EnableCertificateAuthorityRequest(
            requestId=request_utils.GenerateRequestId()
        ),
    )
    operation = (
        self.client.projects_locations_caPools_certificateAuthorities.Enable(
            enable_request
        )
    )
    return operations.Await(operation, 'Enabling CA.', api_version='v1')

  def _ShouldEnableCa(self, args, ca_ref):
    """Determines whether the CA should be enabled or not."""
    if args.auto_enable:
      return True

    # Return false if there already is an enabled CA in the pool.
    ca_pool_name = ca_ref.Parent().RelativeName()
    list_response = self.client.projects_locations_caPools_certificateAuthorities.List(
        self.messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesListRequest(
            parent=ca_pool_name
        )
    )
    if create_utils.HasEnabledCa(
        list_response.certificateAuthorities, self.messages
    ):
      return False

    # Prompt the user if they would like to enable a CA in the pool.
    return console_io.PromptContinue(
        message=(
            'The CaPool [{}] has no enabled CAs and cannot issue any '
            'certificates until at least one CA is enabled. Would you like to '
            'also enable this CA?'.format(ca_ref.Parent().Name())
        ),
        default=False,
    )

  def Run(self, args):
    client = privateca_base.GetClientInstance(api_version='v1')
    messages = privateca_base.GetMessagesModule(api_version='v1')
    ca_ref = args.CONCEPTS.certificate_authority.Parse()

    pem_cert, pem_chain = self._ParsePemChainFromFile(args.pem_chain)

    operation = client.projects_locations_caPools_certificateAuthorities.Activate(
        messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesActivateRequest(
            name=ca_ref.RelativeName(),
            activateCertificateAuthorityRequest=messages.ActivateCertificateAuthorityRequest(
                pemCaCertificate=pem_cert,
                subordinateConfig=messages.SubordinateConfig(
                    pemIssuerChain=messages.SubordinateConfigChain(
                        pemCertificates=pem_chain
                    )
                ),
            ),
        )
    )

    operations.Await(
        operation, 'Activating Certificate Authority.', api_version='v1'
    )
    log.status.Print(
        'Activated Certificate Authority [{}].'.format(ca_ref.Name())
    )
    if self._ShouldEnableCa(args, ca_ref):
      self._EnableCertificateAuthority(ca_ref.RelativeName())
