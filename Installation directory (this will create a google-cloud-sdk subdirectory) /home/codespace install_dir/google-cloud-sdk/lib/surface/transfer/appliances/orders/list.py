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
"""Command to list Transfer Appliances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer.appliances import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Transfer Appliance orders."""

  detailed_help = {
      'DESCRIPTION':
          """\
      List Transfer Appliances in a given project to show their state and
      corresponding orders.
      """,
      'EXAMPLES':
          """\
      To list all appliances in your current project, run:

        $ {command}

      To list all information about all jobs formatted as JSON, run:

        $ {command} --format=json

      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_list_resource_args(parser, listing_orders=True)
    parser.display_info.AddFormat(
        """
        yaml(name,appliances,state,submit_time.date(),update_time.date())
        """)

  def Run(self, args):
    """Command execution logic."""
    client = apis.GetClientInstance('transferappliance', 'v1alpha1')
    messages = apis.GetMessagesModule('transferappliance', 'v1alpha1')
    return list_pager.YieldFromList(
        client.projects_locations_orders,
        messages.TransferapplianceProjectsLocationsOrdersListRequest(
            filter=resource_args.parse_list_resource_args_as_filter_string(
                args, listing_orders=True),
            orderBy='name asc',
            parent=resource_args.get_parent_string(args.region)),
        batch_size_attribute='pageSize',
        field='orders')
