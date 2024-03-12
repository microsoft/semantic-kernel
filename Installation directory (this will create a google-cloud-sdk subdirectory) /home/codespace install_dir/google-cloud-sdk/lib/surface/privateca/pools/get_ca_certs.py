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
"""Get the root CA certs for all active CAs in a CA Pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import pem_utils
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.GA)
class GetCaCerts(base.Command):
  r"""Get the root CA certs for all active CAs in the CA pool.

  ## EXAMPLES

    To get the root CA certs for all active CAs in the CA pool:

      $ {command} my-pool --output-file=ca-certificates.pem \
          --location=us-west1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCaPoolPositionalResourceArg(
        parser, 'whose CA certificates should be fetched')
    base.Argument(
        '--output-file',
        help='The path where the concatenated PEM certificates will be '
             'written. This will include the root CA certificate for each '
             'active CA in the CA pool. ',
        required=True).AddToParser(parser)

  def _GetRootCerts(self, ca_pool_ref):
    """Returns the root CA certs for all active CAs in the CA pool."""
    client = privateca_base.GetClientInstance('v1')
    messages = privateca_base.GetMessagesModule('v1')

    fetch_ca_certs_response = client.projects_locations_caPools.FetchCaCerts(
        messages.PrivatecaProjectsLocationsCaPoolsFetchCaCertsRequest(
            caPool=ca_pool_ref.RelativeName(),
            fetchCaCertsRequest=messages.FetchCaCertsRequest(
                requestId=request_utils.GenerateRequestId())))
    root_certs = [
        chain.certificates[-1] for chain in fetch_ca_certs_response.caCerts
    ]
    return ''.join(pem_utils.PemChainForOutput(root_certs))

  def Run(self, args):
    ca_pool_ref = args.CONCEPTS.ca_pool.Parse()
    pem_bag = self._GetRootCerts(ca_pool_ref)
    files.WriteFileContents(args.output_file, pem_bag)
    log.status.write('Exported the CA certificates to [{}].'.format(
        args.output_file))
