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
"""Export a pem-encoded certificate to a file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import pem_utils
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


_DETAILED_HELP = {
    'EXAMPLES':
        """\
        To export a single pem-encoded certificate to a file, run the following:

          $ {command} my-cert --issuer=my-ca --issuer-location=us-west1 --output-file=cert.pem

        To export a pem-encoded certificate along with its issuing chain in the
        same file, run the following:

          $ {command} my-cert --issuer=my-ca --issuer-location=us-west1 --include-chain --output-file=chain.pem

        You can omit the --issuer-location flag in both of the above examples if
        you've already set the privateca/location property. For example:

          $ {top_command} config set privateca/location us-west1

          # The following is equivalent to the first example above.
          $ {command} my-cert --issuer=my-ca --output-file=cert.pem

          # The following is equivalent to the second example above.
          $ {command} my-cert --issuer=my-ca --include-chain --output-file=chain.pem
        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Export(base.SilentCommand):
  r"""Export a pem-encoded certificate to a file.

  ## EXAMPLES

  To export a single pem-encoded certificate to a file, run the following:

    $ {command} my-cert --issuer-pool=my-pool --issuer-location=us-west1 \
      --output-file=cert.pem

  To export a pem-encoded certificate along with its issuing chain in the
  same file, run the following:

  $ {command} my-cert --issuer-pool=my-pool --issuer-location=us-west1 \
    --include-chain \
    --output-file=chain.pem

  You can omit the --issuer-location flag in both of the above examples if
  you've already set the privateca/location property. For example:

  $ {top_command} config set privateca/location us-west1

  # The following is equivalent to the first example above.
  $ {command} my-cert --issuer-pool=my-pool --output-file=cert.pem

  # The following is equivalent to the second example above.
  $ {command} my-cert --issuer-pool=my-pool --include-chain \
    --output-file=chain.pem
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertPositionalResourceArg(parser, 'to export')
    base.Argument(
        '--output-file',
        help='The path where the resulting PEM-encoded certificate will be '
             'written.',
        required=True).AddToParser(parser)
    base.Argument(
        '--include-chain',
        help="Whether to include the certificate's issuer chain in the "
             "exported file. If this is set, the resulting file will contain "
             "the pem-encoded certificate and its issuing chain, ordered from "
             "leaf to root.",
        action='store_true',
        default=False,
        required=False).AddToParser(parser)

  def Run(self, args):
    client = privateca_base.GetClientInstance(api_version='v1')
    messages = privateca_base.GetMessagesModule(api_version='v1')

    certificate_ref = args.CONCEPTS.certificate.Parse()
    certificate = client.projects_locations_caPools_certificates.Get(
        messages
        .PrivatecaProjectsLocationsCaPoolsCertificatesGetRequest(
            name=certificate_ref.RelativeName()))

    pem_chain = [certificate.pemCertificate]
    if args.include_chain:
      pem_chain += certificate.pemCertificateChain

    files.WriteFileContents(args.output_file,
                            pem_utils.PemChainForOutput(pem_chain))
    log.status.write('Exported certificate [{}] to [{}].'.format(
        certificate_ref.RelativeName(), args.output_file))
