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
"""'vmware sddc privateclouds create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.sddc.privateclouds import PrivatecloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.vmware.sddc import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a VMware Engine private cloud. Private cloud creation is
          considered finished when the private cloud is in READY state. Check
          the progress of a private cloud using
          `gcloud alpha vmware privateclouds list`.
        """,
    'EXAMPLES':
        """
          To create a private cloud called ``my-privatecloud'' in project
          ``my-project'' and region ``us-central1'', run:

            $ {command} my-privatecloud --project=my-project --region=us-central1

          Or:

            $ {command} my-privatecloud

          In the second example, the project and region are taken from gcloud
          properties core/project and vmware/region.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a VMware Engine private cloud."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser, positional=True)
    parser.add_argument(
        '--description',
        help="""\
        Text describing the private cloud
        """)
    parser.add_argument(
        '--vpc-network',
        required=True,
        help="""\
        Name of the virtual network for this private cloud
        """)
    parser.add_argument(
        '--management-ip-range',
        required=True,
        help="""\
        IP address range available to the private cloud for management access,
        in address/mask format. For example,
        `--management-ip-range=10.0.1.0/29`.
        """)
    parser.add_argument(
        '--workload-ip-range',
        required=True,
        help="""\
        IP address range available to the private cloud in address/mask
        format. For example, `--workload-ip-range=10.0.1.0/29`.
        """)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    privatecloud = args.CONCEPTS.privatecloud.Parse()
    client = PrivatecloudsClient()
    operation = client.Create(
        privatecloud,
        vpc_network=args.vpc_network,
        management_ip_range=args.management_ip_range,
        workload_ip_range=args.workload_ip_range,
        labels=args.labels,
        description=args.description,
    )
    return client.WaitForOperation(
        operation,
        'waiting for privatecloud [{}] to be created'.format(privatecloud))


Create.detailed_help = DETAILED_HELP
