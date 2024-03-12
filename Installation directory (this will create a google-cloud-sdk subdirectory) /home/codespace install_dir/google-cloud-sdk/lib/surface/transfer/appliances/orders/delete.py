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
"""Command to delete Transfer Appliance Orders."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import uuid

from googlecloudsdk.api_lib.transfer.appliances import operations_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer.appliances import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete transfer appliance orders."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Delete transfer appliance orders.
      """,
      'EXAMPLES':
          """\
      To delete an order, run:

        $ {command} ORDER

      To delete an order but keep the associated appliance records:

        $ {command} ORDER --keep-appliances
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_order_resource_arg(
        parser, verb=resource_args.ResourceVerb.DELETE)
    parser.add_argument(
        '--keep-appliances',
        action='store_true',
        help=(
            'Keep appliances associated with the order rather than deleting'
            ' them.'
        ))

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.'
  )
  def Run(self, args):
    client = apis.GetClientInstance('transferappliance', 'v1alpha1')
    messages = apis.GetMessagesModule('transferappliance', 'v1alpha1')
    order_ref = args.CONCEPTS.order.Parse()
    # Get the order first to get to the appliance names to delete.
    if not args.keep_appliances:
      request = messages.TransferapplianceProjectsLocationsOrdersGetRequest(
          name=order_ref.RelativeName())
      order = client.projects_locations_orders.Get(request=request)
      for appliance_name in order.appliances:
        operation = client.projects_locations_appliances.Delete(
            messages.TransferapplianceProjectsLocationsAppliancesDeleteRequest(
                name=appliance_name, requestId=uuid.uuid4().hex))
        operations_util.wait_then_yield_nothing(operation, 'delete appliance')
    operation = client.projects_locations_orders.Delete(
        messages.TransferapplianceProjectsLocationsOrdersDeleteRequest(
            name=order_ref.RelativeName(), requestId=uuid.uuid4().hex))
    return operations_util.wait_then_yield_nothing(operation, 'delete order')
