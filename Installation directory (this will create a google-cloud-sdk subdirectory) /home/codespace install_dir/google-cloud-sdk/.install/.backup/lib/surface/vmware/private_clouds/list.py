# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""'vmware private-clouds list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_projector

DETAILED_HELP = {
    'DESCRIPTION': """
          List VMware Engine private clouds.
        """,
    'EXAMPLES': """
          To list VMware Engine operations in the location `us-west2-a`, run:

            $ {command} --location=us-west2-a

          Or:

            $ {command}

          In the second example, the location is taken from gcloud properties compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Google Cloud VMware Engine private clouds."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLocationArgToParser(parser)
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NAME,'
        'name.segment(-5):label=PROJECT,'
        'name.segment(-3):label=LOCATION,'
        'createTime,state,vcenter.fqdn:label=VCENTER_FQDN,type,'
        'managementCluster.stretchedClusterConfig.preferredLocation.segment(-1):'
        'label=PREFERRED_ZONE,'
        'managementCluster.stretchedClusterConfig.secondaryLocation.segment(-1):'
        'label=SECONDARY_ZONE)'
    )

  def Run(self, args):
    location = args.CONCEPTS.location.Parse()

    client = PrivateCloudsClient()
    items = client.List(location)
    for item in items:
      private_cloud = resource_projector.MakeSerializable(item)
      if not private_cloud.get('type'):
        private_cloud['type'] = (
            client.messages.PrivateCloud.TypeValueValuesEnum.STANDARD
        )
      if private_cloud.get('type') == 'STRETCHED':
        # private cloud name example:
        # projects/sample-project/locations/us-west1-a/privateClouds/pc-name
        private_cloud_name = private_cloud.get('name').split('/')
        private_cloud_resource = resources.REGISTRY.Create(
            'vmwareengine.projects.locations.privateClouds',
            projectsId=private_cloud_name[-5],
            locationsId=private_cloud_name[-3],
            privateCloudsId=private_cloud_name[-1],
        )
        private_cloud['managementCluster'] = client.GetManagementCluster(
            private_cloud_resource
        )
      yield private_cloud
