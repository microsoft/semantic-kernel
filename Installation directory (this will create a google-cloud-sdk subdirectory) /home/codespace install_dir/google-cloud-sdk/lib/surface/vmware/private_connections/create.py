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
"""'vmware private-connections create' command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateconnections import PrivateConnectionsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Creates a new private connection to connect VMware Engine Network to the specified VPC network. This establishes private IP connectivity between the VPC network and all the VMware Private Clouds attached to the VMware Engine Network. Private connection creation is considered finished when the connection is in ACTIVE state. Check the progress of the private connection using `{parent_command} list`.
        """,
    'EXAMPLES':
        """
        To create a Private Connection of type PRIVATE_SERVICE_ACCESS, first obtain the service-project by listing vpc-peerings, run:

          $ gcloud compute networks peerings list --network=my-vpc --project=my-project

        where my-vpc is the VPC on which a private service access connection is created and project is the one in which the private connection will be created.

        The response will be of this format:

        NAME                              NETWORK  PEER_PROJECT           \n
        servicenetworking-googleapis-com  my-vpc   td096d594ece09650-tp

        The PEER_PROJECT field in the output of the command will provide the value for the service-project required for creating the private connection.

        To create a Private Connection called `my-private-connection` of type `PRIVATE_SERVICE_ACCESS` in project `my-project` and region `us-west1` with routing_mode `REGIONAL` to connect service networking VPC from project `td096d594ece09650-tp` to legacy VMware Engine Network `us-west1-default`, run:

          $ {command} my-private-connection --location=us-west1 --project=my-project --vmware-engine-network=us-west1-default --description="A short description for the new private connection" --routing-mode=REGIONAL --service-project=td096d594ece09650-tp --type=PRIVATE_SERVICE_ACCESS

        Or:

          $ {command} my-private-connection --vmware-engine-network=us-west1-default --description="A short description for the new private connection" --routing-mode=REGIONAL --service-project=td096d594ece09650-tp --type=PRIVATE_SERVICE_ACCESS

          In the second example, the project and location are taken from gcloud properties core/project and compute/region, respectively.

        To create a Private Connection called `my-private-connection` of type `THIRD_PARTY_SERVICE` in project `my-project` and region `us-west1` to connect VPC `my-service-network` from project `td096d594ece09650-tp` to legacy VMware Engine Network `us-west1-default`, run:

          $ {command} my-private-connection --location=us-west1 --project=my-project --vmware-engine-network=us-west1-default --description="A short description for the new private connection" --service-network=my-service-network --service-project=td096d594ece09650-tp --type=THIRD_PARTY_SERVICE

        Or:

          $ {command} my-private-connection --vmware-engine-network=us-west1-default --description="A short description for the new private connection" --service-network=my-service-network --service-project=td096d594ece09650-tp --type=THIRD_PARTY_SERVICE

          In the above example, the project and location are taken from gcloud properties core/project and compute/region, respectively.

        If you try to create a private connection of type=THIRD_PARTY_SERVICE, and do not provide the service-network field, an error will be thrown with the message:

        Missing required argument [--service-network]: For private connection of type THIRD_PARTY_SERVICE, service-network field is required
        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Google Cloud Private Connection."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivateConnectionToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--description',
        help="""\
        Text describing the private connection.
        """)
    parser.add_argument(
        '--routing-mode',
        choices=['GLOBAL', 'REGIONAL'],
        help="""\
        Type of the routing mode. Default value is set to GLOBAL. For type=PRIVATE_SERVICE_ACCESS, this field can be set to GLOBAL or REGIONAL, for other types only GLOBAL is supported.
        """)
    parser.add_argument(
        '--type',
        required=True,
        choices={
            'PRIVATE_SERVICE_ACCESS':
                'Peering connection used for establishing [private services access](https://cloud.google.com/vpc/docs/private-services-access).',
            'NETAPP_CLOUD_VOLUMES':
                'Peering connection used for connecting to NetApp Cloud Volumes.',
            'DELL_POWERSCALE':
                'Peering connection used for connecting to Dell PowerScale.',
            'THIRD_PARTY_SERVICE':
                'Peering connection used for connecting to third-party services. Most third-party services require manual setup of reverse peering on the VPC network associated with the third-party service.'
        },
        help="""\
        Type of private connection.
        """)
    parser.add_argument(
        '--service-network',
        help="""\
        Resource ID of the service network to connect with the VMware Engine network to create a private connection.
        * For type=PRIVATE_SERVICE_ACCESS, this field represents service networking VPC. In this case the field value will be automatically set to `servicenetworking` and cannot be changed.
        * For type=NETAPP_CLOUD_VOLUME, this field represents NetApp service VPC. In this case the field value will be automatically set to `netapp-tenant-vpc` and cannot be changed.
        * For type=DELL_POWERSCALE, this field represents Dell service VPC. In this case the field value will be automatically set to `dell-tenant-vpc` and cannot be changed.
        * For type=THIRD_PARTY_SERVICE, this field could represent a consumer VPC or any other producer VPC to which the VMware Engine Network needs to be connected. service-network field is required for this type.
        """)
    parser.add_argument(
        '--service-project',
        required=True,
        help="""\
        Project ID or project number of the service network.
        """)
    parser.add_argument(
        '--vmware-engine-network',
        required=True,
        help="""\
        Resource ID of the legacy VMware Engine network. Provide the {vmware_engine_network_id}, which will be in the form of {location}-default. The {location} is the same as the location specified in the private connection resource.
        """)

  def Run(self, args):
    if args.type == 'THIRD_PARTY_SERVICE' and not args.service_network:
      raise exceptions.RequiredArgumentException(
          '--service-network',
          'For private connection of type THIRD_PARTY_SERVICE, service-network field is required.'
      )
    private_connection = args.CONCEPTS.private_connection.Parse()
    client = PrivateConnectionsClient()
    is_async = args.async_
    operation = client.Create(
        private_connection,
        vmware_engine_network=args.vmware_engine_network,
        service_project=args.service_project,
        private_connection_type=args.type,
        routing_mode=args.routing_mode,
        description=args.description,
        service_network=args.service_network,
    )
    if is_async:
      log.CreatedResource(
          operation.name, kind='Private Connection', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for private connection [{}] to be created'.format(
            private_connection.RelativeName()
        ),
    )
    log.CreatedResource(
        private_connection.RelativeName(), kind='Private Connection'
    )
    return resource
