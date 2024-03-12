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
"""`gcloud domains registrations get-register-parameters` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.core import log


class GetRegisterParameters(base.DescribeCommand):
  """Get register parameters (including availability) of a specific domain.

  Get parameters needed to register a new domain, including
  price, availability, supported privacy modes and notices.

  In contrast to the search-domains command, this command returns up-to-date
  domain name availability information.

  ## EXAMPLES

  To check if ``example.com'' is available for registration, run:

    $ {command} example.com
  """

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser)
    base.Argument(
        'domain',
        help='Domain to get register parameters for.',
    ).AddToParser(parser)

  def Run(self, args):
    """Run the get register parameters command."""
    api_version = registrations.GetApiVersionFromArgs(args)
    client = registrations.RegistrationsClient(api_version)

    location_ref = args.CONCEPTS.location.Parse()

    domain = util.NormalizeDomainName(args.domain)

    if domain != args.domain:
      log.status.Print(
          'Domain name \'{}\' has been normalized to equivalent \'{}\'.'.format(
              args.domain, domain))

    return client.RetrieveRegisterParameters(location_ref, domain)
