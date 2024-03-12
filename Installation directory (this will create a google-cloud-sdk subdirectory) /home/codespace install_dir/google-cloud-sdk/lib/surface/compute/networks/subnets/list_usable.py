# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for list subnetworks which the current user has permission to use."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListUsableSubnets(base.ListCommand):
  """List subnetworks which the current user has permission to use."""

  enable_service_project = False

  @staticmethod
  def _EnableComputeApi():
    return properties.VALUES.compute.use_new_list_usable_subnets_api.GetBool()

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat("""\
        table(
          subnetwork.segment(-5):label=PROJECT,
          subnetwork.segment(-3):label=REGION,
          network.segment(-1):label=NETWORK,
          subnetwork.segment(-1):label=SUBNET,
          ipCidrRange:label=RANGE,
          secondaryIpRanges.map().format("{0} {1}", rangeName, ipCidrRange).list(separator="\n"):label=SECONDARY_RANGES,
          purpose,
          role,
          stackType,
          ipv6AccessType,
          internalIpv6Prefix,
          externalIpv6Prefix
        )""")

    if cls.enable_service_project:
      parser.add_argument(
          '--service-project',
          required=False,
          help="""\
          The project id or project number in which the subnetwork is intended to be
          used. Only applied for Shared VPC.
          See [Shared VPC documentation](https://cloud.google.com/vpc/docs/shared-vpc/).
          """)

  def Collection(self):
    return 'compute.subnetworks'

  def GetUriFunc(self):
    def _GetUri(search_result):
      return ''.join([
          p.value.string_value
          for p
          in search_result.resource.additionalProperties
          if p.key == 'selfLink'])
    return _GetUri

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages
    request = messages.ComputeSubnetworksListUsableRequest(
        project=properties.VALUES.core.project.Get(required=True))

    if self.enable_service_project and args.service_project:
      request.serviceProject = args.service_project

    return list_pager.YieldFromList(
        client.apitools_client.subnetworks,
        request,
        method='ListUsable',
        batch_size_attribute='maxResults',
        batch_size=500,
        field='items')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListUsableSubnetsAlphaBeta(ListUsableSubnets):
  """List subnetworks which the current user has permission to use."""

  enable_service_project = True


ListUsableSubnets.detailed_help = {
    'brief':
        """\
        List Compute Engine subnetworks permitted for use.
        """,
    'DESCRIPTION':
        """\
        *{command}* is used to list Compute Engine subnetworks in a
        project that the user has permission to use.

        By default, usable subnetworks are listed for the default Google Cloud
        project and user account. These values can be overridden by
        setting the global flags: `--project=PROJECT_ID` and/or
        `--account=ACCOUNT`.
        """,
    'EXAMPLES':
        """\
          To list all subnetworks in the default project that are usable by the
          default user:

            $ {command}

          To list all subnetworks in the project ``PROJECT_ID'' that are usable
          by the user ``ACCOUNT'':

            $ {command} --project=PROJECT_ID --account=ACCOUNT
        """,
}

ListUsableSubnetsAlphaBeta.detailed_help = {
    'brief':
        """\
        List Compute Engine subnetworks permitted for use.
        """,
    'DESCRIPTION':
        """\
        *{command}* is used to list Compute Engine subnetworks in a
        project that the user has permission to use.

        By default, usable subnetworks are listed for the default Google Cloud
        project and user account. These values can be overridden by
        setting the global flags: `--project=PROJECT_ID` and/or
        `--account=ACCOUNT`.
        """,
    'EXAMPLES':
        """\
          To list all subnetworks in the default project that are usable by the
          default user:

            $ {command}

          To list all subnetworks in the host project ``HOST_PROJECT_ID'' of
          Shared VPC that are usable in the service project ``SERVICE_PROJECT_ID''
          (see [Shared VPC documentation](https://cloud.google.com/vpc/docs/shared-vpc/))
          by the default user:

            $ {command} --project=HOST_PROJECT_ID --service-project=SERVICE_PROJECT_ID

          To list all subnetworks in the project ``PROJECT_ID'' that are usable
          by the user ``ACCOUNT'':

            $ {command} --project=PROJECT_ID --account=ACCOUNT
        """,
}
