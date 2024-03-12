# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""The `domains verify` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import browser_dispatcher

VERIFY_DOMAINS_URL = (
    'https://search.google.com/search-console/welcome'
    '?authuser=0&new_domain_name={domain}&pli=1'
)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Verify(base.Command):
  """Verifies a domain via an in-browser workflow."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To verify a domain for the current user, run:

            $ {command} example.com

          This will allow the domain to be used with App Engine through
          {parent_command} app domain-mappings and across Google Cloud products.
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('domain', help='The domain to be verified.')

  def Run(self, args):
    url = VERIFY_DOMAINS_URL.format(domain=args.domain)
    browser_dispatcher.OpenURL(url)
