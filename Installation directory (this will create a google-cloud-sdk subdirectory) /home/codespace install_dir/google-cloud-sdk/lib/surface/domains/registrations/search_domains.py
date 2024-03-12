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
"""`gcloud domains registrations search-domains` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util

_FORMAT = """\
table(
    domainName:label=DOMAIN,
    availability:label=AVAILABILITY,
    yearlyPrice.price():label=YEARLY_PRICE,
    domainNotices.list():label=NOTICES
)
"""


class SearchDomains(base.DescribeCommand):
  """Search for available domains.

  Search for available domains relevant to a specified query.

  This command uses cached domain name availability information. Use the
  get-register-params command to get up-to-date availability information.

  ## EXAMPLES

  To search for domains for ``my-new-project'', run:

    $ {command} my-new-project

  To search for a specific domain, like ``example.com'', and get suggestions for
  other domain endings, run:

    $ {command} example.com
  """

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser, 'to search domains in')
    parser.display_info.AddTransforms({'price': util.TransformMoneyType})
    parser.display_info.AddFormat(_FORMAT)
    base.Argument(
        'domain_query',
        help=('Domain search query. '
              'May be a domain name or arbitrary search terms.'),
    ).AddToParser(parser)

  def Run(self, args):
    """Run the search domains command."""
    api_version = registrations.GetApiVersionFromArgs(args)
    client = registrations.RegistrationsClient(api_version)

    location_ref = args.CONCEPTS.location.Parse()

    # Sending the query direcyly to server (without normalization).
    suggestions = client.SearchDomains(location_ref, args.domain_query)
    for s in suggestions:
      try:
        s.domainName = util.PunycodeToUnicode(s.domainName)
      except UnicodeError:
        pass  # Do not change the domain name.
    if not suggestions:

      suggestions.append(client.messages.RegisterParameters())
    return suggestions
