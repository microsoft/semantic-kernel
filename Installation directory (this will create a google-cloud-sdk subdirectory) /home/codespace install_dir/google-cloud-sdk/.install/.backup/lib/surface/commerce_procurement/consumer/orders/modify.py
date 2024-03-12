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
"""Implementation of gcloud Procurement consumer order modify command."""

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
        To modify an order to another product plan or update parameters, you
        must specify product request. To specify parameters, you must follow the
        pattern "ParameterName=ParameterType:ParameterValue". For example:

            $ {command} --product-request line-item-id=lineItemId,line-item-change-type=UPDATE,product-external-name=productId,flavor-external-name=flavorId,region=str:us-west-1

        To cancel a product plan-based order, you must specify the product
        request. For example:

            $ {command} --product-request line-item-id=lineItemId,line-item-change-type=CANCEL

        To revert cancellation on a product plan-based order, you must specify
        the product request. For example:

            $ {command} --product-request line-item-id=lineItemId,line-item-change-type=REVERT_CANCELLATION

        To update an order to another quote, you must specify the fields that
        are related to the quote. For example:

            $ {command} --quote-change-type UPDATE --new-quote-external-name quoteId

        To cancel a quote-based order, you must specify the quote change type.
        For example:

            $ {command} --quote-change-type CANCEL

        To revert cancellation on a quote-based order, you must specify the
        quote change type. For example:

            $ {command} --quote-change-type REVERT_CANCELLATION
        """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Modify(base.Command):
  """Modifies the order resource from the Modify API."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    resource_args.AddOrderResourceArg(parser, 'Order to modify.')
    parser.add_argument(
        '--etag', help='The weak etag for validation check, if specified.')

    product_quote_group = parser.add_mutually_exclusive_group(required=True)
    product_quote_group.add_argument(
        '--product-request',
        type=arg_parsers.ArgDict(
            required_keys=['line-item-id', 'line-item-change-type']),
        metavar='KEY=VALUE',
        action='append',
        help='Request about product info to modify order against.')
    quote_request_group = product_quote_group.add_group(
        help='Quote-related modification.')
    quote_request_group.add_argument(
        '--quote-change-type',
        required=True,
        help='Change type on quote based purchase.')
    quote_request_group.add_argument(
        '--new-quote-external-name',
        help='The external name of the quote the order will use.')

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      An Order operation.
    """
    order_ref = args.CONCEPTS.order.Parse()
    return apis.Orders.Modify(order_ref.RelativeName(), args.etag,
                              args.product_request, args.quote_change_type,
                              args.new_quote_external_name)


Modify.detailed_help = DETAILED_HELP
