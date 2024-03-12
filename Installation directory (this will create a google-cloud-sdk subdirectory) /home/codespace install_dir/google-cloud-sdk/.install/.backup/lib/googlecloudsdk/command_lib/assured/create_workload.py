# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Base class used to create a new Assured Workloads environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import message_util
from googlecloudsdk.api_lib.assured import workloads as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION':
        'Create a new Assured Workloads environment',
    'EXAMPLES':
        """ \
    The following example command creates a new Assured Workloads environment with these properties:

    * belonging to an organization with ID 123
    * located in the `us-central1` region
    * display name `Test-Workload`
    * compliance regime `FEDRAMP_MODERATE`
    * billing account `billingAccounts/456`
    * first key rotation set for 10:15am on the December 30, 2020
    * key rotation interval set for every 48 hours
    * with the label: key = 'LabelKey1', value = 'LabelValue1'
    * with the label: key = 'LabelKey2', value = 'LabelValue2'
    * provisioned resources parent 'folders/789'
    * with custom project id 'my-custom-id' for consumer project

      $ {command} --organization=123 --location=us-central1 --display-name=Test-Workload --compliance-regime=FEDRAMP_MODERATE --billing-account=billingAccounts/456 --next-rotation-time=2020-12-30T10:15:00.00Z --rotation-period=172800s --labels=LabelKey1=LabelValue1,LabelKey2=LabelValue2 --provisioned-resources-parent=folders/789 --resource-settings=consumer-project-id=my-custom-id

    """,
}


class CreateWorkload(base.CreateCommand):
  """Create a new Assured Workloads environment."""

  detailed_help = _DETAILED_HELP

  def Run(self, args):
    """Run the create command."""
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=args.location):
      parent = message_util.CreateAssuredParent(
          organization_id=args.organization, location=args.location)
      workload = message_util.CreateAssuredWorkload(
          display_name=args.display_name,
          compliance_regime=args.compliance_regime,
          partner=args.partner,
          partner_permissions=args.partner_permissions,
          billing_account=args.billing_account,
          next_rotation_time=args.next_rotation_time,
          rotation_period=args.rotation_period,
          labels=args.labels,
          provisioned_resources_parent=args.provisioned_resources_parent,
          resource_settings=args.resource_settings,
          enable_sovereign_controls=args.enable_sovereign_controls,
          release_track=self.ReleaseTrack())
      client = apis.WorkloadsClient(release_track=self.ReleaseTrack())
      self.created_resource = client.Create(
          external_id=args.external_identifier,
          parent=parent,
          workload=workload)
      return self.created_resource

  def Epilog(self, resources_were_displayed):
    log.CreatedResource(
        self.created_resource.name, kind='Assured Workloads environment')
