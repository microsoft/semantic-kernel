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
"""Revoke a certificate."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import certificate_utils
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import times


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Revoke(base.SilentCommand):
  r"""Revoke a certificate.

  Revokes the given certificate for the given reason.

  ## EXAMPLES

  To revoke the 'frontend-server-tls' certificate due to key compromise:

    $ {command} \
      --certificate=frontend-server-tls \
      --issuer-pool=my-pool --issuer-location=us-west1 \
      --reason=key_compromise

  To revoke the a certificate with the serial number
  '7dc1d9186372de2e1f4824abb1c4c9e5e43cbb40' due to a newer one being issued:

    $ {command} \
      --serial-number=7dc1d9186372de2e1f4824abb1c4c9e5e43cbb40 \
      --issuer-pool=my-pool --issuer-location=us-west1 \
      --reason=superseded
  """

  @staticmethod
  def Args(parser):
    id_group = parser.add_group(
        mutex=True, required=True, help='The certificate identifier.'
    )
    base.Argument(
        '--serial-number', help='The serial number of the certificate.'
    ).AddToParser(id_group)
    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            '--certificate',
            resource_args.CreateCertResourceSpec('certificate'),
            'The certificate to revoke.',
            flag_name_overrides={
                'issuer-pool': '',
                'issuer-location': '',
                'project': '',
            },
            group=id_group,
        ),
        presentation_specs.ResourcePresentationSpec(
            '--issuer-pool',
            resource_args.CreateCaPoolResourceSpec(
                'Issuing CA pool', 'issuer-location'
            ),
            'The issuing CA pool of the certificate to revoke.',
            required=False,
        ),
    ]).AddToParser(parser)

    flags.AddRevocationReasonFlag(parser)

  @staticmethod
  def ParseCertificateResource(args):
    """Gets the certificate resource to be revoked based on the specified args."""
    # Option 1: user specified full resource name for the certificate.
    cert_ref = args.CONCEPTS.certificate.Parse()
    if cert_ref:
      return cert_ref

    if not args.IsSpecified('issuer_pool'):
      raise exceptions.RequiredArgumentException(
          '--issuer-pool',
          (
              'The issuing CA pool is required if a full resource name is not'
              ' provided for --certificate.'
          ),
      )

    issuer_ref = args.CONCEPTS.issuer_pool.Parse()
    if not issuer_ref:
      raise exceptions.RequiredArgumentException(
          '--issuer-pool',
          (
              'The issuer flag is not fully specified. Please add the'
              " --issuer-location flag or specify the issuer's full resource"
              ' name.'
          ),
      )

    cert_collection_name = 'privateca.projects.locations.caPools.certificates'
    # Option 2: user specified certificate ID + issuer.
    if args.IsSpecified('certificate'):
      return resources.REGISTRY.Parse(
          args.certificate,
          collection=cert_collection_name,
          params={
              'projectsId': issuer_ref.projectsId,
              'locationsId': issuer_ref.locationsId,
              'caPoolsId': issuer_ref.caPoolsId,
          },
      )

    # Option 3: user specified serial number + issuer.
    if args.IsSpecified('serial_number'):
      certificate = certificate_utils.GetCertificateBySerialNum(
          issuer_ref, args.serial_number
      )
      return resources.REGISTRY.Parse(
          certificate.name, collection=cert_collection_name
      )

    raise exceptions.OneOfArgumentsRequiredException(
        ['--certificate', '--serial-number'],
        (
            'To revoke a Certificate, please provide either its resource ID or '
            'serial number.'
        ),
    )

  def Run(self, args):
    cert_ref = Revoke.ParseCertificateResource(args)

    if not console_io.PromptContinue(
        message='You are about to revoke Certificate [{}]'.format(
            cert_ref.RelativeName()
        ),
        default=True,
    ):
      log.status.Print('Aborted by user.')
      return

    reason = flags.ParseRevocationChoiceToEnum(args.reason)

    client = privateca_base.GetClientInstance(api_version='v1')
    messages = privateca_base.GetMessagesModule(api_version='v1')

    certificate = client.projects_locations_caPools_certificates.Revoke(
        messages.PrivatecaProjectsLocationsCaPoolsCertificatesRevokeRequest(
            name=cert_ref.RelativeName(),
            revokeCertificateRequest=messages.RevokeCertificateRequest(
                reason=reason, requestId=request_utils.GenerateRequestId()
            ),
        )
    )

    revoke_time = times.ParseDateTime(
        certificate.revocationDetails.revocationTime
    )
    log.status.Print(
        'Revoked certificate [{}] at {}.'.format(
            certificate.name,
            times.FormatDateTime(revoke_time, tzinfo=times.LOCAL),
        )
    )
