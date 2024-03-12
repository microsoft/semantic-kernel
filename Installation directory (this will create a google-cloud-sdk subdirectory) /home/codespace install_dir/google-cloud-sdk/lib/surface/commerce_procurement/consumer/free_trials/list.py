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
"""Implementation of gcloud Procurement consumer free trials list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.commerce_procurement import apis
from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'EXAMPLES':
        """
        The filter is a query string that can match a selected set of attributes
        with string values. For example:

            $ {command} --filter "product_external_name=1234-5678-ABCD-EFG"

        Supported query attributes are the following:

            * `product_external_name`
            * `provider` (in the naming format of "provider/{provider-id}")

        If the query contains some special characters other than letters,
        underscore, or digits, the phrase must be quoted with double quotes. For
        example, where the product name needs to be quoted because it contains
        the special character colon:

            $ {command} --filter "product_external_name=\\"foo:bar\\""

        Queries can be combined with AND, OR, and NOT to form more complex
        queries. They can also be grouped to force a desired evaluation order.
        For example:

            $ {command} --filter "provider=providers/E-1234 OR provider=providers/5678 AND NOT (product_external_name=foo-product)"

        Connective AND can be omitted between two predicates. For example:

            $ {command} --filter "provider=providers/E-1234 product_external_name=foo"

        is equivalent to:

            $ {command} --filter "provider=providers/E-1234 AND product_external_name=foo"

        """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.Command):
  """Returns the List of Free Trial objects resulting from the List API."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    parser.add_argument(
        '--page-size', type=int, help=('Maximum number of resources per page.'))
    parser.add_argument(
        '--page-token',
        help=('Token that specifies the next page in the list.'))
    parser.add_argument(
        '--filter', help=('Filter that limits the list request.'))

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      List of free trials and next token if applicable.
    """
    result = apis.FreeTrials.List(args.page_size, args.page_token, args.filter)

    # Clear the filter on args so the built-in functionality will not overwrite
    # already filtered result.
    args.filter = ''
    return result


List.detailed_help = DETAILED_HELP
