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
"""Implementation of gcloud Procurement consumer order place command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.commerce_procurement import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.commerce_procurement import resource_args

DETAILED_HELP = {
    'EXAMPLES':
        """
        To purchase a product-based order, you must specify product request. For
        example:

            $ {command} --product-request product-external-name=productId,flavor-external-name=flavorId

        To specify parameters, you must follow the pattern
        "ParameterName=ParameterType:ParameterValue". For example:

            $ {command} --product-request product-external-name=productId,flavor-external-name=flavorId,region=str:us-west-1

        To purchase a quote-based order, you must specify quote external name.
        For example:

            $ {command} --quote-external-name quoteId
        """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Creates the order resource from the Place API."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    resource_args.AddBillingAccountResourceArg(
        parser, 'Parent Cloud Billing account to place order under.')
    parser.add_argument(
        '--display-name', required=True, help='Display name of the order.')
    parser.add_argument(
        '--provider-id',
        required=True,
        help='ID of the provider for which the order is created.')
    parser.add_argument(
        '--request-id', help='ID of the request for idempotency purposes.')

    product_quote_group = parser.add_mutually_exclusive_group(required=True)
    product_quote_group.add_argument(
        '--product-request',
        type=arg_parsers.ArgDict(
            required_keys=['product-external-name', 'flavor-external-name']),
        metavar='KEY=VALUE',
        action='append',
        help='Request for information about the product in the order.')
    product_quote_group.add_argument(
        '--quote-external-name',
        help='External name of the quote for the order.')

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      An Order operation.
    """
    billing_account_ref = args.CONCEPTS.billing_account.Parse()
    return apis.Orders.Place(billing_account_ref.RelativeName(),
                             args.display_name, args.provider_id,
                             args.request_id, args.product_request,
                             args.quote_external_name)


Create.detailed_help = DETAILED_HELP
