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
"""'vmware private-clouds management-dns-zone-bindings delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.managementdnszonebinding import ManagementDNSZoneBindingClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Delete a management DNS zone binding.
        """,
    'EXAMPLES':
        """
          To delete a management DNS zone binding called `my-mgmt-dns-zone-binding` in private cloud
          `my-private-cloud`, in location `us-east2-b`, run:

            $ {command} my-mgmt-dns-zone-binding --project=my-project --private-cloud=my-private-cloud --location=us-east2-b

          Or:

            $ {command} my-mgmt-dns-zone-binding --private-cloud=my-private-cloud

          In the second example, the project and location are taken from gcloud properties `core/project` and `compute/zone` respectively.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a management DNS zone binding."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddManagementDnsZoneBindingArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    mdzb = args.CONCEPTS.management_dns_zone_binding.Parse()
    client = ManagementDNSZoneBindingClient()
    is_async = args.async_
    operation = client.Delete(mdzb)
    if is_async:
      log.DeletedResource(
          operation.name, kind='management DNS zone binding', is_async=True)
      return operation

    client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=('waiting for management DNS zone binding [{}] ' +
                 'to be deleted').format(mdzb.RelativeName()), has_result=False)

    log.DeletedResource(
        mdzb.RelativeName(),
        kind='management DNS zone binding',
        is_async=False)
    return operation
