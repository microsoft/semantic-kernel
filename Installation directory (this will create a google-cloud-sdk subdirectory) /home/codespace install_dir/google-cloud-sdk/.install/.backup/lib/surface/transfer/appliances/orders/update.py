# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to update transfer appliance orders."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import uuid

from googlecloudsdk.api_lib.transfer.appliances import operations_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer.appliances import flags
from googlecloudsdk.command_lib.transfer.appliances import mapping_util
from googlecloudsdk.command_lib.transfer.appliances import resource_args
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
        *{command}* facilitates the update of Transfer Appliance Orders.
        """,
    'EXAMPLES':
        """
        To update the shipping contact of an appliance called `my-appliance`:

          $ {command} my-appliance --shipping-contact="name=Jane Doe,emails=[jane@example.com],phone=12345678910"
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Update an order for a transfer appliance."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.add_order_resource_arg(
        parser, resource_args.ResourceVerb.UPDATE)
    parser.add_argument(
        '--submit',
        action='store_true',
        help='Submits an order that is in draft.')
    flags.add_appliance_settings(parser, for_create_command=False)
    flags.add_delivery_information(parser, for_create_command=False)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.'
  )
  def Run(self, args):
    client = apis.GetClientInstance('transferappliance', 'v1alpha1')
    messages = apis.GetMessagesModule('transferappliance', 'v1alpha1')
    name = args.CONCEPTS.order.Parse().RelativeName()
    results = []
    # Get the order first to get to the appliance ID.
    order = client.projects_locations_orders.Get(
        messages.TransferapplianceProjectsLocationsOrdersGetRequest(name=name))

    if order.appliances:
      # We only use the first appliance in update operations, as the workflow
      # expects a 1:1 relationship of orders to appliances.
      appliance_name = order.appliances[0]
      if len(order.appliances) > 1:
        log.warning(
            'Only 1 appliance per order is supported. {} will be updated and'
            ' all others will be ignored.'.format(appliance_name))
      appliance = messages.Appliance()
      update_mask = mapping_util.apply_args_to_appliance(appliance, args)
      if update_mask:
        operation = client.projects_locations_appliances.Patch(
            messages.TransferapplianceProjectsLocationsAppliancesPatchRequest(
                name=appliance_name,
                appliance=appliance,
                requestId=uuid.uuid4().hex,
                updateMask=update_mask,
            )
        )
        results.append(operations_util.wait_then_yield_appliance(
            operation, 'update'))
    # Map args to the order resource, make the API call if needed.
    update_mask = mapping_util.apply_args_to_order(order, args)
    if update_mask:
      operation = client.projects_locations_orders.Patch(
          messages.TransferapplianceProjectsLocationsOrdersPatchRequest(
              name=name,
              order=order,
              requestId=uuid.uuid4().hex,
              updateMask=update_mask,
          )
      )
      results.append(operations_util.wait_then_yield_order(operation, 'update'))
    if args.submit:
      operation = client.projects_locations_orders.Submit(
          messages.TransferapplianceProjectsLocationsOrdersSubmitRequest(
              name=name))
      if update_mask:
        # We don't want to dump out the order twice, so when an order update
        # already occurred we just wait for the submit operation to complete.
        operations_util.wait_then_yield_nothing(operation, 'submit')
      else:
        # Since there's no update operation on the order we can yield an order
        # and add it to the result output.
        results.append(operations_util.wait_then_yield_order(
            operation, 'submit'))
    if not results:
      log.warning('No updates were performed.')
    return results
