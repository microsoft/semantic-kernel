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
"""Command to describe Transfer Appliance Orders."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer.appliances import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Get information about Transfer Appliance orders."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Get information about transfer appliance orders.
      """,
      'EXAMPLES':
          """\
      To describe an order by name, including its prefix, run:

        $ {command} ORDER --region=REGION
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_order_resource_arg(
        parser, resource_args.ResourceVerb.DESCRIBE)

  def Run(self, args):
    client = apis.GetClientInstance('transferappliance', 'v1alpha1')
    messages = apis.GetMessagesModule('transferappliance', 'v1alpha1')
    order_ref = args.CONCEPTS.order.Parse()
    request = messages.TransferapplianceProjectsLocationsOrdersGetRequest(
        name=order_ref.RelativeName())
    return client.projects_locations_orders.Get(request=request)
