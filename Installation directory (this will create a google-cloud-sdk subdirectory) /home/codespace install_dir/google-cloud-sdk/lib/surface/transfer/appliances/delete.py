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
"""Command to delete Transfer Appliances."""

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
  """Delete a transfer appliance."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Delete a specific transfer appliance.
      """,
      'EXAMPLES':
          """\

      To delete an appliance, run:

        $ {command} APPLIANCE

      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_appliance_resource_arg(
        parser, verb=resource_args.ResourceVerb.DELETE)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.'
  )
  def Run(self, args):
    client = apis.GetClientInstance('transferappliance', 'v1alpha1')
    messages = apis.GetMessagesModule('transferappliance', 'v1alpha1')
    name = args.CONCEPTS.appliance.Parse().RelativeName()
    operation = client.projects_locations_appliances.Delete(
        messages.TransferapplianceProjectsLocationsAppliancesDeleteRequest(
            name=name, requestId=uuid.uuid4().hex
        )
    )
    return operations_util.wait_then_yield_nothing(
        operation, 'delete appliance')
