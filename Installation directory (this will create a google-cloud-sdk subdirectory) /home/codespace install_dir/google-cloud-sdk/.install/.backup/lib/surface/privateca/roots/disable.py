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
"""Disable a root certificate authority."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Disable(base.SilentCommand):
  r"""Disable a root certificate authority.

    Disables a root certificate authority. The root certificate authority
    will not be allowed to issue certificates once disabled. It may still revoke
    certificates and/or generate CRLs. The CA certfificate will still be
    included in the FetchCaCertificates response for the parent CA Pool.

    ## EXAMPLES

    To disable a root CA:

        $ {command} prod-root --pool=prod-root-pool --location=us-west1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertAuthorityPositionalResourceArg(parser, 'to disable')
    flags.AddIgnoreDependentResourcesFlag(parser)

  def Run(self, args):
    client = privateca_base.GetClientInstance(api_version='v1')
    messages = privateca_base.GetMessagesModule(api_version='v1')

    ca_ref = args.CONCEPTS.certificate_authority.Parse()

    if args.ignore_dependent_resources:
      prompt_message = (
          'You are about to disable Certificate Authority [{}] without '
          'checking if the CA\'s CA Pool is being used by another '
          'resource. If you proceed and this is the last enabled CA in '
          'the CA Pool, there may be unintended and '
          'unrecoverable effects on any dependent resource(s) since the '
          'CA Pool would not be able to issue certificates'
      ).format(ca_ref.RelativeName())
      if not console_io.PromptContinue(message=prompt_message, default=True):
        log.status.Print('Aborted by user.')
        return

    current_ca = client.projects_locations_caPools_certificateAuthorities.Get(
        messages
        .PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesGetRequest(
            name=ca_ref.RelativeName()))

    resource_args.CheckExpectedCAType(
        messages.CertificateAuthority.TypeValueValuesEnum.SELF_SIGNED,
        current_ca,
        version='v1')

    operation = client.projects_locations_caPools_certificateAuthorities.Disable(
        messages
        .PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesDisableRequest(
            name=ca_ref.RelativeName(),
            disableCertificateAuthorityRequest=messages
            .DisableCertificateAuthorityRequest(
                ignoreDependentResources=args.ignore_dependent_resources,
                requestId=request_utils.GenerateRequestId())))

    operations.Await(operation, 'Disabling Root CA', api_version='v1')

    log.status.Print('Disabled Root CA [{}].'.format(ca_ref.RelativeName()))
