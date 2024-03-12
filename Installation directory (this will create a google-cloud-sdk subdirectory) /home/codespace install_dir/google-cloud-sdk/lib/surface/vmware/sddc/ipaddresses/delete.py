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
"""'vmware sddc clusters delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.sddc.ipaddresses import IPAddressesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.sddc import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Delete external ip address in a VMware Engine private cloud.
        """,
    'EXAMPLES':
        """
          To delete external ip called ``first-ip'' in private cloud
          ``my-privatecloud'' and region ``us-central1'', run:

            $ {command} first-ip --privatecloud=my-privatecloud --region=us-central1 --project=my-project

          Or:

            $ {command} first-ip --privatecloud=my-privatecloud

          In the second example, the project and region are taken from gcloud properties core/project and vmware/region.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete external ip address in a VMware Engine private cloud."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddIPArgToParser(parser)

  def Run(self, args):
    resource = args.CONCEPTS.name.Parse()
    client = IPAddressesClient()
    operation = client.Delete(resource)
    resource_path = client.GetResourcePath(
        resource, resource_path=resource, encoded_cluster_groups_id=True)
    return client.WaitForOperation(
        operation, 'waiting for external ip address [{}] to be deleted'.format(
            resource_path), is_delete=True)


Delete.detailed_help = DETAILED_HELP
