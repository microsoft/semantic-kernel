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
"""`gcloud domains registrations get-transfer-parameters` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.core import log


@base.Deprecate(
    is_removed=True,
    warning=(
        'This command is deprecated. See'
        ' https://cloud.google.com/domains/docs/deprecations/feature-deprecations.'
    ),
    error=(
        'This command has been removed. See'
        ' https://cloud.google.com/domains/docs/deprecations/feature-deprecations.'
    ),
)
class GetTransferParameters(base.DescribeCommand):
  """Get transfer parameters of a specific domain.

  Get parameters needed to transfer an existing domain from a different
  registrar. The parameters include the current registrar, name servers,
  transfer lock state, price, and supported privacy modes.

  ## EXAMPLES

  To check if ``example.com'' is available for transfer, run:

    $ {command} example.com
  """

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser)
    base.Argument(
        'domain',
        help='Domain to get transfer parameters for.',
    ).AddToParser(parser)

  def Run(self, args):
    """Run the get transfer parameters command."""
    api_version = registrations.GetApiVersionFromArgs(args)
    client = registrations.RegistrationsClient(api_version)

    location_ref = args.CONCEPTS.location.Parse()

    domain = util.NormalizeDomainName(args.domain)

    if domain != args.domain:
      log.status.Print(
          'Domain name \'{}\' has been normalized to equivalent \'{}\'.'.format(
              args.domain, domain))

    return client.RetrieveTransferParameters(location_ref, domain)
