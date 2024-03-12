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
"""Undelete a subordinate certificate authority."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Undelete(base.SilentCommand):
  r"""Undelete a subordinate certificate authority.

    Restores a subordinate Certificate Authority that has been deleted. A
    Certificate Authority can be undeleted within 30 days of being deleted. Use
    this command to halt the deletion process. An undeleted CA will move to
    DISABLED state.

    ## EXAMPLES

    To undelete a subordinate CA:

        $ {command} server-tls-1 --location=us-west1 --pool=my-pool
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertAuthorityPositionalResourceArg(parser, 'to undelete')

  def Run(self, args):
    client = privateca_base.GetClientInstance(api_version='v1')
    messages = privateca_base.GetMessagesModule(api_version='v1')

    ca_ref = args.CONCEPTS.certificate_authority.Parse()

    current_ca = client.projects_locations_caPools_certificateAuthorities.Get(
        messages
        .PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesGetRequest(
            name=ca_ref.RelativeName()))

    resource_args.CheckExpectedCAType(
        messages.CertificateAuthority.TypeValueValuesEnum.SUBORDINATE,
        current_ca,
        version='v1')

    operation = client.projects_locations_caPools_certificateAuthorities.Undelete(
        messages
        .PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesUndeleteRequest(
            name=ca_ref.RelativeName(),
            undeleteCertificateAuthorityRequest=messages
            .UndeleteCertificateAuthorityRequest(
                requestId=request_utils.GenerateRequestId())))

    operations.Await(operation, 'Undeleting Subordinate CA', api_version='v1')

    log.status.Print('Undeleted Subordinate CA [{}].'.format(
        ca_ref.RelativeName()))
