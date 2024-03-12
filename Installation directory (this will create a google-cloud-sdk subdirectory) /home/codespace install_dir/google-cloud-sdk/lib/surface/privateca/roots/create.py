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
"""Create a new root certificate authority."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
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


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  # pylint: disable=line-too-long
  r"""Create a new root certificate authority.

  TIP: Consider setting a [project lien](https://cloud.google.com/resource-manager/docs/project-liens) on the project to prevent it from accidental deletion.

  ## EXAMPLES

  To create a root CA that supports one layer of subordinates:

      $ {command} prod-root \
          --location=us-west1 --pool=my-pool \
          --kms-key-version="projects/my-project-pki/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1" \
          --subject="CN=Example Production Root CA, O=Google" \
          --max-chain-length=1

  To create a root CA that is based on an existing CA:

      $ {command} prod-root \
          --location=us-west1 --pool=my-pool \
          --kms-key-version="projects/my-project-pki/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1" \
          --from-ca=source-root
  """

  def __init__(self, *args, **kwargs):
    super(Create, self).__init__(*args, **kwargs)
    self.client = privateca_base.GetClientInstance(api_version='v1')
    self.messages = privateca_base.GetMessagesModule(api_version='v1')

  @staticmethod
  def Args(parser):
    key_spec_group = parser.add_group(
        mutex=True,
        help='The key configuration used for the CA certificate. Defaults to a '
        'managed key if not specified.')
    x509_config_group = parser.add_group(
        mutex=True,
        required=False,
        help='The X.509 configuration used for the CA certificate.')

    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            'CERTIFICATE_AUTHORITY',
            resource_args.CreateCertAuthorityResourceSpec(
                'Certificate Authority'),
            'The name of the root CA to create.',
            required=True),
        presentation_specs.ResourcePresentationSpec(
            '--kms-key-version',
            resource_args.CreateKmsKeyVersionResourceSpec(),
            'An existing KMS key version to back this CA.',
            group=key_spec_group),
        presentation_specs.ResourcePresentationSpec(
            '--from-ca',
            resource_args.CreateCertAuthorityResourceSpec(
                'source CA',
                location_fallthroughs=[
                    deps.ArgFallthrough('--location'),
                    resource_args.LOCATION_PROPERTY_FALLTHROUGH
                ],
                pool_id_fallthroughs=[deps.ArgFallthrough('--pool')]),
            'An existing CA from which to copy configuration values for the new CA. '
            'You can still override any of those values by explicitly providing '
            'the appropriate flags. The specified existing CA must be part of '
            'the same pool as the one being created.',
            flag_name_overrides={
                'project': '',
                'location': '',
                'pool': '',
            },
            prefixes=True)
    ]).AddToParser(parser)
    flags.AddSubjectFlags(parser, subject_required=False)
    flags.AddKeyAlgorithmFlag(
        key_spec_group, default='rsa-pkcs1-4096-sha256')
    flags.AddValidityFlag(
        parser,
        resource_name='CA',
        default_value='P10Y',
        default_value_text='10 years')
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddBucketFlag(parser)
    flags.AddUsePresetProfilesFlag(x509_config_group)
    # If max_chain_len is unspecified, no max length will be provided to the
    # server on create, this allowing any number of subordinates.
    flags.AddInlineX509ParametersFlags(
        x509_config_group, is_ca_command=True, default_max_chain_length=None)
    flags.AddAutoEnableFlag(parser)
    flags.AddSubjectKeyIdFlag(parser)

  def _EnableCertificateAuthority(self, ca_name):
    """Enables the given CA."""
    enable_request = self.messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesEnableRequest(
        name=ca_name,
        enableCertificateAuthorityRequest=self.messages
        .EnableCertificateAuthorityRequest(
            requestId=request_utils.GenerateRequestId()))
    operation = self.client.projects_locations_caPools_certificateAuthorities.Enable(
        enable_request)
    return operations.Await(operation, 'Enabling CA.', api_version='v1')

  def _ShouldEnableCa(self, args, ca_ref):
    """Determines whether the CA should be enabled or not."""
    if args.auto_enable:
      return True

    # Return false if there already is an enabled CA in the pool.
    ca_pool_name = ca_ref.Parent().RelativeName()
    list_response = self.client.projects_locations_caPools_certificateAuthorities.List(
        self.messages
        .PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesListRequest(
            parent=ca_pool_name))
    if create_utils.HasEnabledCa(
        list_response.certificateAuthorities, self.messages):
      return False

    # Prompt the user if they would like to enable a CA in the pool.
    return console_io.PromptContinue(
        message='The CaPool [{}] has no enabled CAs and cannot issue any '
        'certificates until at least one CA is enabled. Would you like to '
        'also enable this CA?'.format(ca_ref.Parent().Name()), default=False)

  def Run(self, args):
    new_ca, ca_ref, _ = create_utils.CreateCAFromArgs(
        args, is_subordinate=False)
    pool_ref = ca_ref.Parent()
    project_ref = pool_ref.Parent().Parent()
    key_version_ref = args.CONCEPTS.kms_key_version.Parse()
    kms_key_ref = key_version_ref.Parent() if key_version_ref else None

    iam.CheckCreateCertificateAuthorityPermissions(project_ref, kms_key_ref)

    bucket_ref = None
    if args.IsSpecified('bucket'):
      bucket_ref = storage.ValidateBucketForCertificateAuthority(args.bucket)
      new_ca.gcsBucket = bucket_ref.bucket

    # P4SA is needed only if user specifies any resource.
    if bucket_ref or kms_key_ref:
      p4sa.AddResourceRoleBindings(
          p4sa.GetOrCreate(project_ref), kms_key_ref, bucket_ref)

    operation = self.client.projects_locations_caPools_certificateAuthorities.Create(
        self.messages
        .PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesCreateRequest(
            certificateAuthority=new_ca,
            certificateAuthorityId=ca_ref.Name(),
            parent=pool_ref.RelativeName(),
            requestId=request_utils.GenerateRequestId()))

    ca_response = operations.Await(operation, 'Creating Certificate Authority.', api_version='v1')
    ca = operations.GetMessageFromResponse(ca_response,
                                           self.messages.CertificateAuthority)

    log.status.Print('Created Certificate Authority [{}].'.format(ca.name))
    log.status.Print(
        'TIP: To avoid accidental deletion, '
        'please consider adding a project lien on this project. To find out '
        'more, see the following doc: '
        'https://cloud.google.com/resource-manager/docs/project-liens.'
    )

    if self._ShouldEnableCa(args, ca_ref):
      self._EnableCertificateAuthority(ca_ref.RelativeName())
