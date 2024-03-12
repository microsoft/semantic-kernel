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
"""Authenticate clusters using the Anthos client."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos import anthoscli_backend
from googlecloudsdk.command_lib.anthos import flags


@base.Hidden
class Token(base.BinaryBackedCommand):
  """Creates a token for authentication."""

  @staticmethod
  def Args(parser):
    flags.GetTypeFlag().AddToParser(parser)
    flags.GetAwsStsRegionFlag().AddToParser(parser)
    flags.GetTokenClusterFlag().AddToParser(parser)
    flags.GetIdTokenFlag().AddToParser(parser)
    flags.GetAccessTokenFlag().AddToParser(parser)
    flags.GetAccessTokenExpiryFlag().AddToParser(parser)
    flags.GetRefreshTokenFlag().AddToParser(parser)
    flags.GetClientIdFlag().AddToParser(parser)
    flags.GetClientSecretFlag().AddToParser(parser)
    flags.GetIdpCertificateAuthorityDataFlag().AddToParser(parser)
    flags.GetIdpIssuerUrlFlag().AddToParser(parser)
    flags.GetKubeconfigPathFlag().AddToParser(parser)
    flags.GetTokenUserFlag().AddToParser(parser)

  def Run(self, args):
    command_executor = anthoscli_backend.AnthosAuthWrapper()

    # Log and execute binary command with flags.
    response = command_executor(
        command="token",
        token_type=args.type,
        cluster=args.cluster,
        aws_sts_region=args.aws_sts_region,
        id_token=args.id_token,
        access_token=args.access_token,
        access_token_expiry=args.access_token_expiry,
        refresh_token=args.refresh_token,
        client_id=args.client_id,
        client_secret=args.client_secret,
        idp_certificate_authority_data=args.idp_certificate_authority_data,
        idp_issuer_url=args.idp_issuer_url,
        kubeconfig_path=args.kubeconfig_path,
        user=args.user,
        env=anthoscli_backend.GetEnvArgsForCommand())
    return self._DefaultOperationResponseHandler(response)
