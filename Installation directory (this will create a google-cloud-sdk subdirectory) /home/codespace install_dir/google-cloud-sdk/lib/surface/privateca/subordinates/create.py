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
"""Create a new subordinate certificate authority."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import certificate_utils
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.privateca import create_utils
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import iam
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import p4sa
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.privateca import storage
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create a new subordinate certificate authority.

  ## EXAMPLES
  To create a subordinate CA named 'server-tls-1' whose issuer is on Private CA:

    $ {command} server-tls-1 \
        --location=us-west1 --pool=my-pool \
        --subject="CN=Example TLS CA, O=Google" \
        --issuer-pool=other-pool --issuer-location=us-west1 \
        --kms-key-version="projects/my-project-pki/locations/us-west1/keyRings/kr1/cryptoKeys/key2/cryptoKeyVersions/1"

  To create a subordinate CA named 'server-tls-1' whose issuer is located
  elsewhere:

    $ {command} server-tls-1 \
        --location=us-west1 --pool=my-pool \
        --subject="CN=Example TLS CA, O=Google" \
        --create-csr \
        --csr-output-file=./csr.pem \
        --kms-key-version="projects/my-project-pki/locations/us-west1/keyRings/kr1/cryptoKeys/key2/cryptoKeyVersions/1"

  To create a subordinate CA named 'server-tls-1' chaining up to a root CA
  named 'prod-root' based on an existing CA:

    $ {command} server-tls-1 \
        --location=us-west1 --pool=my-pool \
        --issuer-pool=other-pool --issuer-location=us-west1 \
        --from-ca=source-ca \
        --kms-key-version="projects/my-project-pki/locations/us-west1/keyRings/kr1/cryptoKeys/key2/cryptoKeyVersions/1"
  """

  def __init__(self, *args, **kwargs):
    super(Create, self).__init__(*args, **kwargs)
    self.client = privateca_base.GetClientInstance(api_version='v1')
    self.messages = privateca_base.GetMessagesModule(api_version='v1')

  @staticmethod
  def Args(parser):
    key_spec_group = parser.add_group(
        mutex=True,
        help=(
            'The key configuration used for the CA certificate. Defaults to a '
            'managed key if not specified.'
        ),
    )
    x509_config_group = parser.add_group(
        mutex=True,
        required=False,
        help='The X.509 configuration used for the CA certificate.',
    )
    issuer_configuration_group = parser.add_group(
        mutex=True,
        required=True,
        help='The issuer configuration used for this CA certificate.',
    )
    issuing_resource_group = issuer_configuration_group.add_group(
        mutex=False,
        required=False,
        help='The issuing resource used for this CA certificate.',
    )
    base.Argument(
        '--issuer-ca',
        help=(
            'The Certificate Authority ID of the CA to issue the subordinate '
            'CA certificate from. This ID is optional. If ommitted, '
            'any available ENABLED CA in the issuing CA pool will be chosen.'
        ),
        required=False,
    ).AddToParser(parser)

    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            'CERTIFICATE_AUTHORITY',
            resource_args.CreateCertAuthorityResourceSpec(
                'Certificate Authority'
            ),
            'The name of the subordinate CA to create.',
            required=True,
        ),
        presentation_specs.ResourcePresentationSpec(
            '--issuer-pool',
            resource_args.CreateCaPoolResourceSpec('Issuer'),
            'The issuing CA Pool to use, if it is on Private CA.',
            prefixes=True,
            required=False,
            flag_name_overrides={
                'location': '--issuer-location',
            },
            group=issuing_resource_group,
        ),
        presentation_specs.ResourcePresentationSpec(
            '--kms-key-version',
            resource_args.CreateKmsKeyVersionResourceSpec(),
            'The KMS key version backing this CA.',
            group=key_spec_group,
        ),
        presentation_specs.ResourcePresentationSpec(
            '--from-ca',
            resource_args.CreateCertAuthorityResourceSpec(
                'source CA',
                location_fallthroughs=[
                    deps.ArgFallthrough('--location'),
                    resource_args.LOCATION_PROPERTY_FALLTHROUGH,
                ],
                pool_id_fallthroughs=[deps.ArgFallthrough('--pool')],
            ),
            'An existing CA from which to copy configuration values for the '
            'new CA. You can still override any of those values by explicitly '
            'providing the appropriate flags. The specified existing CA must '
            'be part of the same pool as the one being created.',
            flag_name_overrides={
                'project': '',
                'location': '',
                'pool': '',
            },
            prefixes=True,
        ),
    ]).AddToParser(parser)

    flags.AddSubjectFlags(parser, subject_required=False)
    flags.AddKeyAlgorithmFlag(key_spec_group, default='rsa-pkcs1-2048-sha256')
    flags.AddUsePresetProfilesFlag(x509_config_group)
    # Subordinates should have no children by default.
    flags.AddInlineX509ParametersFlags(
        x509_config_group, is_ca_command=True, default_max_chain_length=0
    )
    flags.AddValidityFlag(
        parser,
        resource_name='CA',
        default_value='P3Y',
        default_value_text='3 years',
    )
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddBucketFlag(parser)
    flags.AddSubjectKeyIdFlag(parser)

    offline_issuer_group = issuer_configuration_group.add_group(
        help=(
            'If the issuing CA is not hosted on Private CA, you must provide '
            'these settings:'
        )
    )
    base.Argument(
        '--create-csr',
        help=(
            'Indicates that a CSR should be generated which can be signed by '
            'the issuing CA. This must be set if --issuer is not provided.'
        ),
        action='store_const',
        const=True,
        default=False,
        required=True,
    ).AddToParser(offline_issuer_group)
    base.Argument(
        '--csr-output-file',
        help=(
            'The path where the resulting PEM-encoded CSR file should be '
            'written.'
        ),
        required=True,
    ).AddToParser(offline_issuer_group)
    flags.AddAutoEnableFlag(parser)

  def _EnableCertificateAuthority(self, ca_name):
    """Enable the given CA."""
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

  def _SignCsr(self, issuer_pool_ref, csr, lifetime, issuer_ca_id):
    """Issues a certificate under the given issuer with the given settings."""
    certificate_id = 'subordinate-{}'.format(certificate_utils.GenerateCertId())
    issuer_pool_name = issuer_pool_ref.RelativeName()
    certificate_name = '{}/certificates/{}'.format(
        issuer_pool_name, certificate_id
    )
    cert_request = self.messages.PrivatecaProjectsLocationsCaPoolsCertificatesCreateRequest(
        certificateId=certificate_id,
        parent=issuer_pool_name,
        requestId=request_utils.GenerateRequestId(),
        issuingCertificateAuthorityId=issuer_ca_id,
        certificate=self.messages.Certificate(
            name=certificate_name, lifetime=lifetime, pemCsr=csr
        ),
    )

    return self.client.projects_locations_caPools_certificates.Create(
        cert_request
    )

  def _ActivateCertificateAuthority(self, ca_name, pem_cert, issuer_chain):
    """Activates the given CA using the given certificate and issuing CA chain."""
    activate_request = self.messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesActivateRequest(
        name=ca_name,
        activateCertificateAuthorityRequest=self.messages.ActivateCertificateAuthorityRequest(
            pemCaCertificate=pem_cert,
            subordinateConfig=self.messages.SubordinateConfig(
                pemIssuerChain=self.messages.SubordinateConfigChain(
                    pemCertificates=issuer_chain
                )
            ),
        ),
    )
    operation = (
        self.client.projects_locations_caPools_certificateAuthorities.Activate(
            activate_request
        )
    )
    return operations.Await(operation, 'Activating CA.', api_version='v1')

  def Run(self, args):
    new_ca, ca_ref, issuer_ref = create_utils.CreateCAFromArgs(
        args, is_subordinate=True
    )
    # Retrive the Project reference from the Parent -> Location -> Pool -> CA
    # resource structure.
    project_ref = ca_ref.Parent().Parent().Parent()
    key_version_ref = args.CONCEPTS.kms_key_version.Parse()
    kms_key_ref = key_version_ref.Parent() if key_version_ref else None
    if not args.IsSpecified('issuer_pool') and args.IsSpecified('auto_enable'):
      raise exceptions.InvalidArgumentException(
          ['--auto-enable'],
          (
              "The '--auto-enable' is only supported in the create command if"
              ' an issuer resource is specified. You can use the'
              " '--auto-enable' command in the subordinate CA activate command."
          ),
      )

    if args.issuer_pool == args.pool:
      if not console_io.PromptContinue(
          message=(
              'The new CA will be in the same CA pool as the issuer CA. All'
              ' certificate authorities within a CA pool should be'
              ' interchangeable. Do you want to continue?'
          ),
          default=True,
      ):
        log.status.Print('Aborted by user.')
        return
    iam.CheckCreateCertificateAuthorityPermissions(project_ref, kms_key_ref)
    if issuer_ref:
      iam.CheckCreateCertificatePermissions(issuer_ref)
      # Proactively look for issuing CA Pool problems to avoid downstream
      # issues.
      issuer_ca = args.issuer_ca if args.IsSpecified('issuer_ca') else None
      create_utils.ValidateIssuingPool(issuer_ref.RelativeName(), issuer_ca)

    bucket_ref = None
    if args.IsSpecified('bucket'):
      bucket_ref = storage.ValidateBucketForCertificateAuthority(args.bucket)
      new_ca.gcsBucket = bucket_ref.bucket

    p4sa_email = p4sa.GetOrCreate(project_ref)
    p4sa.AddResourceRoleBindings(p4sa_email, kms_key_ref, bucket_ref)

    operations.Await(
        self.client.projects_locations_caPools_certificateAuthorities.Create(
            self.messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesCreateRequest(
                certificateAuthority=new_ca,
                certificateAuthorityId=ca_ref.Name(),
                parent=ca_ref.Parent().RelativeName(),
                requestId=request_utils.GenerateRequestId(),
            )
        ),
        'Creating Certificate Authority.',
        api_version='v1',
    )

    csr_response = self.client.projects_locations_caPools_certificateAuthorities.Fetch(
        self.messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesFetchRequest(
            name=ca_ref.RelativeName()
        )
    )
    csr = csr_response.pemCsr

    if args.create_csr:
      files.WriteFileContents(args.csr_output_file, csr)
      log.status.Print(
          "Created Certificate Authority [{}] and saved CSR to '{}'.".format(
              ca_ref.RelativeName(), args.csr_output_file
          )
      )
      return

    if issuer_ref:
      issuer_ca = args.issuer_ca if args.IsSpecified('issuer_ca') else None
      ca_certificate = self._SignCsr(
          issuer_ref, csr, new_ca.lifetime, issuer_ca
      )
      self._ActivateCertificateAuthority(
          ca_ref.RelativeName(),
          ca_certificate.pemCertificate,
          ca_certificate.pemCertificateChain,
      )
      log.status.Print(
          'Created Certificate Authority [{}].'.format(ca_ref.RelativeName())
      )
      if self._ShouldEnableCa(args, ca_ref):
        self._EnableCertificateAuthority(ca_ref.RelativeName())
      return
