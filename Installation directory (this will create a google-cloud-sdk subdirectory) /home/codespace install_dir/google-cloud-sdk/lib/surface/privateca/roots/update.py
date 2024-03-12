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
"""Update a root certificate authority."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.privateca import update_utils
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update an existing root certificate authority.

  ## EXAMPLES
    To update labels on a root CA:

      $ {command} prod-root \
        --location=us-west1 \
        --pool=my-pool \
        --update-labels=foo=bar
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertAuthorityPositionalResourceArg(parser, 'to update')
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    client = privateca_base.GetClientInstance(api_version='v1')
    messages = privateca_base.GetMessagesModule(api_version='v1')

    ca_ref = args.CONCEPTS.certificate_authority.Parse()
    ca_name = ca_ref.RelativeName()

    current_ca = client.projects_locations_caPools_certificateAuthorities.Get(
        messages
        .PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesGetRequest(
            name=ca_name))

    resource_args.CheckExpectedCAType(
        messages.CertificateAuthority.TypeValueValuesEnum.SELF_SIGNED,
        current_ca,
        version='v1')

    ca_to_update, update_mask = update_utils.UpdateCAFromArgs(
        args, current_ca.labels)

    # Patch is the REST client method associated with updating a CA.
    operation = client.projects_locations_caPools_certificateAuthorities.Patch(
        messages
        .PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesPatchRequest(
            name=ca_name,
            certificateAuthority=ca_to_update,
            updateMask=','.join(update_mask),
            requestId=request_utils.GenerateRequestId()))

    return operations.Await(operation, 'Updating Root CA.', api_version='v1')
