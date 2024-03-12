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
  """Get configuration details about a Transfer Appliance."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Get configuration details about a specific transfer appliance.
      """,
      'EXAMPLES':
          """\
      To describe an appliance, run:

        $ {command} APPLIANCE

      To view details of the order associated with an appliance, first obtain
      the ORDER identifier, then use it to look up the order:

        $ {command} APPLIANCE --format="value(order)"

        $ {command} orders describe ORDER
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_appliance_resource_arg(
        parser, resource_args.ResourceVerb.DESCRIBE)

  def Run(self, args):
    client = apis.GetClientInstance('transferappliance', 'v1alpha1')
    messages = apis.GetMessagesModule('transferappliance', 'v1alpha1')
    appliance_ref = args.CONCEPTS.appliance.Parse()
    request = messages.TransferapplianceProjectsLocationsAppliancesGetRequest(
        name=appliance_ref.RelativeName())
    return client.projects_locations_appliances.Get(request=request)
