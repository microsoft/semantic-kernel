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
"""Create a certificate."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import cryptokeyversions
from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import certificate_utils
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import key_generation
from googlecloudsdk.command_lib.privateca import pem_utils
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files
import six

_KEY_OUTPUT_HELP = """The path where the generated private key file should be written (in PEM format).

Note: possession of this key file could allow anybody to act as this certificate's
subject. Please make sure that you store this key file in a secure location at all
times, and ensure that only authorized users have access to it."""


def _ReadCsr(csr_file):
  try:
    return files.ReadFileContents(csr_file)
  except (files.Error, OSError, IOError):
    raise exceptions.BadFileException(
        "Could not read provided CSR file '{}'.".format(csr_file)
    )


def _WritePemChain(pem_cert, issuing_chain, cert_file):
  try:
    pem_chain = [pem_cert] + issuing_chain
    files.WriteFileContents(cert_file, pem_utils.PemChainForOutput(pem_chain))
  except (files.Error, OSError, IOError):
    raise exceptions.BadFileException(
        "Could not write certificate to '{}'.".format(cert_file)
    )


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create a new certificate.

  ## EXAMPLES

  To create a certificate using a CSR:

      $ {command} frontend-server-tls \
        --issuer-pool=my-pool --issuer-location=us-west1 \
        --csr=./csr.pem \
        --cert-output-file=./cert.pem \
        --validity=P30D

    To create a certificate using a client-generated key:

      $ {command} frontend-server-tls \
        --issuer-pool=my-pool --issuer-location=us-west1 \
        --generate-key \
        --key-output-file=./key \
        --cert-output-file=./cert.pem \
        --dns-san=www.example.com \
        --use-preset-profile=leaf_server_tls
  """

  @staticmethod
  def Args(parser):
    persistence_group = parser.add_group(
        mutex=True, required=True, help='Certificate persistence options.'
    )
    base.Argument(
        '--cert-output-file',
        help=(
            'The path where the resulting PEM-encoded certificate chain file'
            ' should be written (ordered from leaf to root).'
        ),
        required=False,
    ).AddToParser(persistence_group)
    base.Argument(
        '--validate-only',
        help=(
            'If this flag is set, the certificate resource will not be'
            ' persisted and the returned certificate will not contain the'
            ' pem_certificate field.'
        ),
        action='store_true',
        default=False,
        required=False,
    ).AddToParser(persistence_group)

    flags.AddValidityFlag(parser, 'certificate', 'P30D', '30 days')
    labels_util.AddCreateLabelsFlags(parser)

    cert_generation_group = parser.add_group(
        mutex=True, required=True, help='Certificate generation method.'
    )
    base.Argument(
        '--csr', help='A PEM-encoded certificate signing request file path.'
    ).AddToParser(cert_generation_group)

    non_csr_group = cert_generation_group.add_group(
        help='Alternatively, you may describe the certificate and key to use.'
    )
    key_group = non_csr_group.add_group(
        mutex=True,
        required=True,
        help=(
            'To describe the key that will be used for this certificate, use '
            'one of the following options.'
        ),
    )
    key_generation_group = key_group.add_group(
        help='To generate a new key pair, use the following:'
    )
    base.Argument(
        '--generate-key',
        help=(
            'Use this flag to have a new RSA-2048 private key securely'
            ' generated on your machine.'
        ),
        action='store_const',
        const=True,
        default=False,
        required=True,
    ).AddToParser(key_generation_group)
    base.Argument(
        '--key-output-file', help=_KEY_OUTPUT_HELP, required=True
    ).AddToParser(key_generation_group)
    base.Argument(
        '--ca',
        help=(
            'The name of an existing certificate authority to use for issuing'
            ' the certificate. If omitted, a certificate authority will be will'
            ' be chosen from the CA pool by the service on your behalf.'
        ),
        required=False,
    ).AddToParser(parser)
    subject_group = non_csr_group.add_group(
        help='The subject names for the certificate.', required=True
    )
    flags.AddSubjectFlags(subject_group)
    x509_parameters_group = non_csr_group.add_group(
        mutex=True, help='The x509 configuration used for this certificate.'
    )
    flags.AddInlineX509ParametersFlags(
        x509_parameters_group, is_ca_command=False, default_max_chain_length=0
    )
    flags.AddUsePresetProfilesFlag(x509_parameters_group)
    flags.AddSubjectKeyIdFlag(parser)

    cert_arg = 'CERTIFICATE'
    concept_parsers.ConceptParser(
        [
            presentation_specs.ResourcePresentationSpec(
                cert_arg,
                resource_args.CreateCertResourceSpec(
                    cert_arg, [Create._GenerateCertificateIdFallthrough()]
                ),
                'The name of the certificate to issue. If the certificate ID '
                'is omitted, a random identifier will be generated according '
                'to the following format: {YYYYMMDD}-{3 random alphanumeric '
                'characters}-{3 random alphanumeric characters}. The '
                'certificate ID is not required when the issuing CA pool is in '
                'the DevOps tier.',
                required=True,
            ),
            presentation_specs.ResourcePresentationSpec(
                '--template',
                resource_args.CreateCertificateTemplateResourceSpec(
                    'certificate_template'
                ),
                'The name of a certificate template to use for issuing this '
                'certificate, if desired. A template may overwrite parts of '
                'the certificate request, and the use of certificate templates '
                "may be required and/or regulated by the issuing CA Pool's CA "
                'Manager. The specified template must be in the same location '
                'as the issuing CA Pool.',
                required=False,
                prefixes=True,
            ),
            presentation_specs.ResourcePresentationSpec(
                '--kms-key-version',
                resource_args.CreateKmsKeyVersionResourceSpec(),
                'An existing KMS key version backing this certificate.',
                group=key_group,
            ),
        ],
        command_level_fallthroughs={
            '--template.location': ['CERTIFICATE.issuer-location']
        },
    ).AddToParser(parser)

    # The only time a resource is returned is when args.validate_only is set.
    parser.display_info.AddFormat('yaml(certificateDescription)')

  @classmethod
  def _GenerateCertificateIdFallthrough(cls):
    cls.id_fallthrough_was_used = False

    def FallthroughFn():
      cls.id_fallthrough_was_used = True
      return certificate_utils.GenerateCertId()

    return deps.Fallthrough(
        function=FallthroughFn,
        hint='certificate id will default to an automatically generated id',
        active=False,
        plural=False,
    )

  def _ValidateArgs(self, args):
    """Validates the command-line args."""
    if args.IsSpecified('use_preset_profile') and args.IsSpecified('template'):
      raise exceptions.OneOfArgumentsRequiredException(
          ['--use-preset-profile', '--template'],
          (
              'To create a certificate, please specify either a preset profile '
              'or a certificate template.'
          ),
      )

    resource_args.ValidateResourceIsCompleteIfSpecified(args, 'kms_key_version')

  @classmethod
  def _PrintWarningsForUnpersistedCert(cls, args):
    """Prints warnings if certain command-line args are used for an unpersisted cert."""
    unused_args = []
    if not cls.id_fallthrough_was_used:
      unused_args.append('certificate ID')
    if args.IsSpecified('labels'):
      unused_args.append('labels')

    if unused_args:
      names = ', '.join(unused_args)
      verb = 'was' if len(unused_args) == 1 else 'were'
      log.warning(
          '{names} {verb} specified but will not be used since the '
          'issuing CA pool is in the DevOps tier, which does not expose '
          'certificate lifecycle.'.format(names=names, verb=verb)
      )

  def _GetPublicKey(self, args):
    """Fetches the public key associated with a non-CSR certificate request, as UTF-8 encoded bytes."""
    kms_key_version = args.CONCEPTS.kms_key_version.Parse()
    if args.generate_key:
      private_key, public_key = key_generation.RSAKeyGen(2048)
      key_generation.ExportPrivateKey(args.key_output_file, private_key)
      return public_key
    elif kms_key_version:
      public_key_response = cryptokeyversions.GetPublicKey(kms_key_version)
      # bytes(..) requires an explicit encoding in PY3.
      return (
          bytes(public_key_response.pem)
          if six.PY2
          else bytes(public_key_response.pem, 'utf-8')
      )
    else:
      # This should not happen because of the required arg group, but protects
      # in case of future additions.
      raise exceptions.OneOfArgumentsRequiredException(
          ['--csr', '--generate-key', '--kms-key-version'],
          (
              'To create a certificate, please specify either a CSR, the'
              ' --generate-key flag to create a new key, or the'
              ' --kms-key-version flag to use an existing KMS key.'
          ),
      )

  def _GenerateCertificateConfig(self, request, args):
    public_key = self._GetPublicKey(args)

    config = self.messages.CertificateConfig()
    config.publicKey = self.messages.PublicKey()
    config.publicKey.key = public_key
    config.publicKey.format = self.messages.PublicKey.FormatValueValuesEnum.PEM
    config.subjectConfig = flags.ParseSubjectFlags(args, is_ca=args.is_ca_cert)
    config.x509Config = flags.ParseX509Parameters(args, is_ca_command=False)
    config.subjectKeyId = flags.ParseSubjectKeyId(args, self.messages)
    return config

  def Run(self, args):
    self.client = privateca_base.GetClientInstance(api_version='v1')
    self.messages = privateca_base.GetMessagesModule(api_version='v1')

    self._ValidateArgs(args)

    cert_ref = args.CONCEPTS.certificate.Parse()
    labels = labels_util.ParseCreateArgs(
        args, self.messages.Certificate.LabelsValue
    )

    request = (
        self.messages.PrivatecaProjectsLocationsCaPoolsCertificatesCreateRequest()
    )
    request.certificate = self.messages.Certificate()
    request.certificateId = cert_ref.Name()
    request.certificate.lifetime = flags.ParseValidityFlag(args)
    request.certificate.labels = labels
    request.parent = cert_ref.Parent().RelativeName()
    request.requestId = request_utils.GenerateRequestId()
    request.validateOnly = args.validate_only
    if args.IsSpecified('ca'):
      request.issuingCertificateAuthorityId = args.ca

    template_ref = args.CONCEPTS.template.Parse()
    if template_ref:
      if template_ref.locationsId != cert_ref.locationsId:
        raise exceptions.InvalidArgumentException(
            '--template',
            'The certificate template must be in the same location as the '
            'issuing CA Pool.',
        )
      request.certificate.certificateTemplate = template_ref.RelativeName()

    if args.csr:
      request.certificate.pemCsr = _ReadCsr(args.csr)
    else:
      request.certificate.config = self._GenerateCertificateConfig(
          request, args
      )

    certificate = self.client.projects_locations_caPools_certificates.Create(
        request
    )

    # Validate-only certs don't have a resource name or pem certificate.
    if args.validate_only:
      return certificate

    status_message = 'Created Certificate'

    if certificate.name:
      status_message += ' [{}]'.format(certificate.name)
    else:
      Create._PrintWarningsForUnpersistedCert(args)

    if certificate.pemCertificate:
      status_message += ' and saved it to [{}]'.format(args.cert_output_file)
      _WritePemChain(
          certificate.pemCertificate,
          certificate.pemCertificateChain,
          args.cert_output_file,
      )

    status_message += '.'
    log.status.Print(status_message)
