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
"""Command to create transfer appliance orders."""

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
from googlecloudsdk.command_lib.transfer.appliances import regions
from googlecloudsdk.command_lib.transfer.appliances import resource_args


DETAILED_HELP = {
    'DESCRIPTION':
        """
        *{command}* facilitates the creation of Transfer Appliance orders.
        When an order is created, an appliance record is created as well.
        """,
    'EXAMPLES':
        """
        To order a rackable appliance with 40 TB of storage, named
        `my-appliance`, a Cloud Storage destination of `my-bucket` and the
        minimum amount of contact information.

          $ {command} my-appliance \
              --model=TA40_RACKABLE \
              --shipping-contact="name=Jane Doe,emails=[jane@example.com],phone=12345678910" \
              --offline-import=gs://my-bucket \
              --order-contact="name=John Doe,phone=123456578910,emails=[john@example.com]" --country=US \
              --address="lines=['1600 Amphitheatre Parkway'],locality=Mountain View,administrative-area=CA,postal-code=94043"

        To clone an appliance order with the ID `my-appliance` and location
        `us-central1`, only changing the name and Cloud Storage destination:

          $ {command} \
              my-other-appliance --country=US --clone=my-appliance \
              --clone-region=us-central1 --offline-import=my-other-bucket

        To use a flags file to create an appliance rather than provide a
        long list of flags:

          $ {command} my-appliance \
              --flags-file=FLAGS_FILE

        Example file with all possible flags set:

          --address:
            lines:
            - 1600 Amphitheatre Parkway
            locality: Mountain View
            administrative-area: California
            postal-code: 94043
          --cmek: projects/p/locations/global/keyRings/kr/cryptoKeys/ck
          --country: US
          --delivery-notes: None
          --display-name: test
          --internet-enabled:
          --model: TA40_RACKABLE
          --offline-export:
            source: gs://my-bucket/path
            manifest: gs://my-other-bucket/manifest
          --offline-import: gs://my-bucket/path
          --online-import: gs://my-bucket/path
          --order-contact:
            business: Google
            name: Jane Doe
            phone: 1234567890
            emails:
            - janedoe@example.com
          --shipping-contact:
            business: Google
            name: John Doe
            phone: 1234567890
            emails:
            - johndoe@example.com
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Create an order for a transfer appliance."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'name',
        help='Immutable ID that will uniquely identify the appliance.')
    parser.add_argument(
        '--submit',
        action='store_true',
        help=(
            'When specified the order will be submitted immediately. By '
            'default, orders are created in a draft state. Use '
            '`{parent_command} update --submit` to submit the order later.'
            )
        )
    resource_args.add_clone_resource_arg(parser)
    flags.add_appliance_settings(parser)
    flags.add_delivery_information(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.'
  )
  def Run(self, args):
    client = apis.GetClientInstance('transferappliance', 'v1alpha1')
    messages = apis.GetMessagesModule('transferappliance', 'v1alpha1')

    appliance = messages.Appliance()
    order = messages.Order()
    results = []
    region = regions.COUNTRY_TO_LOCATION_MAP[args.country]
    parent = resource_args.get_parent_string(region)

    if args.IsSpecified('clone'):
      # Clone-specific logic.
      clone_ref = args.CONCEPTS.clone.Parse()
      order = client.projects_locations_orders.Get(
          request=messages.TransferapplianceProjectsLocationsOrdersGetRequest(
              name=clone_ref.RelativeName()))
      if order.appliances:
        # We only use the first appliance in a clone operation, as the
        # workflow expects a 1:1 relationship of orders to appliances.
        appliance = client.projects_locations_appliances.Get(
            messages.TransferapplianceProjectsLocationsAppliancesGetRequest(
                name=order.appliances[0]))

    # Map args to the appliance resource and make the API call, append result.
    mapping_util.apply_args_to_appliance(appliance, args)
    operation = client.projects_locations_appliances.Create(
        messages.TransferapplianceProjectsLocationsAppliancesCreateRequest(
            appliance=appliance,
            applianceId=args.name,
            parent=parent,
            requestId=uuid.uuid4().hex))
    results.append(operations_util.wait_then_yield_appliance(
        operation, 'create'))

    # Map args to the order resource, make the API call, append result.
    appliance_name = resource_args.get_appliance_name(region, args.name)
    mapping_util.apply_args_to_order(order, args, appliance_name)
    order.skipDraft = args.submit
    operation = client.projects_locations_orders.Create(
        messages.TransferapplianceProjectsLocationsOrdersCreateRequest(
            order=order,
            orderId=args.name,
            parent=parent,
            requestId=uuid.uuid4().hex))
    results.append(operations_util.wait_then_yield_order(
        operation, 'create'))
    return results
