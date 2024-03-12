# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#

import boto
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.directconnect import exceptions
from boto.compat import json


class DirectConnectConnection(AWSQueryConnection):
    """
    AWS Direct Connect makes it easy to establish a dedicated network
    connection from your premises to Amazon Web Services (AWS). Using
    AWS Direct Connect, you can establish private connectivity between
    AWS and your data center, office, or colocation environment, which
    in many cases can reduce your network costs, increase bandwidth
    throughput, and provide a more consistent network experience than
    Internet-based connections.

    The AWS Direct Connect API Reference provides descriptions,
    syntax, and usage examples for each of the actions and data types
    for AWS Direct Connect. Use the following links to get started
    using the AWS Direct Connect API Reference :


    + `Actions`_: An alphabetical list of all AWS Direct Connect
      actions.
    + `Data Types`_: An alphabetical list of all AWS Direct Connect
      data types.
    + `Common Query Parameters`_: Parameters that all Query actions
      can use.
    + `Common Errors`_: Client and server errors that all actions can
      return.
    """
    APIVersion = "2012-10-25"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "directconnect.us-east-1.amazonaws.com"
    ServiceName = "DirectConnect"
    TargetPrefix = "OvertureService"
    ResponseError = JSONResponseError

    _faults = {
        "DirectConnectClientException": exceptions.DirectConnectClientException,
        "DirectConnectServerException": exceptions.DirectConnectServerException,
    }

    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs:
            kwargs['host'] = region.endpoint

        super(DirectConnectConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def allocate_connection_on_interconnect(self, bandwidth, connection_name,
                                            owner_account, interconnect_id,
                                            vlan):
        """
        Creates a hosted connection on an interconnect.

        Allocates a VLAN number and a specified amount of bandwidth
        for use by a hosted connection on the given interconnect.

        :type bandwidth: string
        :param bandwidth: Bandwidth of the connection.
        Example: " 500Mbps "

        Default: None

        :type connection_name: string
        :param connection_name: Name of the provisioned connection.
        Example: " 500M Connection to AWS "

        Default: None

        :type owner_account: string
        :param owner_account: Numeric account Id of the customer for whom the
            connection will be provisioned.
        Example: 123443215678

        Default: None

        :type interconnect_id: string
        :param interconnect_id: ID of the interconnect on which the connection
            will be provisioned.
        Example: dxcon-456abc78

        Default: None

        :type vlan: integer
        :param vlan: The dedicated VLAN provisioned to the connection.
        Example: 101

        Default: None

        """
        params = {
            'bandwidth': bandwidth,
            'connectionName': connection_name,
            'ownerAccount': owner_account,
            'interconnectId': interconnect_id,
            'vlan': vlan,
        }
        return self.make_request(action='AllocateConnectionOnInterconnect',
                                 body=json.dumps(params))

    def allocate_private_virtual_interface(self, connection_id,
                                           owner_account,
                                           new_private_virtual_interface_allocation):
        """
        Provisions a private virtual interface to be owned by a
        different customer.

        The owner of a connection calls this function to provision a
        private virtual interface which will be owned by another AWS
        customer.

        Virtual interfaces created using this function must be
        confirmed by the virtual interface owner by calling
        ConfirmPrivateVirtualInterface. Until this step has been
        completed, the virtual interface will be in 'Confirming'
        state, and will not be available for handling traffic.

        :type connection_id: string
        :param connection_id: The connection ID on which the private virtual
            interface is provisioned.
        Default: None

        :type owner_account: string
        :param owner_account: The AWS account that will own the new private
            virtual interface.
        Default: None

        :type new_private_virtual_interface_allocation: dict
        :param new_private_virtual_interface_allocation: Detailed information
            for the private virtual interface to be provisioned.
        Default: None

        """
        params = {
            'connectionId': connection_id,
            'ownerAccount': owner_account,
            'newPrivateVirtualInterfaceAllocation': new_private_virtual_interface_allocation,
        }
        return self.make_request(action='AllocatePrivateVirtualInterface',
                                 body=json.dumps(params))

    def allocate_public_virtual_interface(self, connection_id, owner_account,
                                          new_public_virtual_interface_allocation):
        """
        Provisions a public virtual interface to be owned by a
        different customer.

        The owner of a connection calls this function to provision a
        public virtual interface which will be owned by another AWS
        customer.

        Virtual interfaces created using this function must be
        confirmed by the virtual interface owner by calling
        ConfirmPublicVirtualInterface. Until this step has been
        completed, the virtual interface will be in 'Confirming'
        state, and will not be available for handling traffic.

        :type connection_id: string
        :param connection_id: The connection ID on which the public virtual
            interface is provisioned.
        Default: None

        :type owner_account: string
        :param owner_account: The AWS account that will own the new public
            virtual interface.
        Default: None

        :type new_public_virtual_interface_allocation: dict
        :param new_public_virtual_interface_allocation: Detailed information
            for the public virtual interface to be provisioned.
        Default: None

        """
        params = {
            'connectionId': connection_id,
            'ownerAccount': owner_account,
            'newPublicVirtualInterfaceAllocation': new_public_virtual_interface_allocation,
        }
        return self.make_request(action='AllocatePublicVirtualInterface',
                                 body=json.dumps(params))

    def confirm_connection(self, connection_id):
        """
        Confirm the creation of a hosted connection on an
        interconnect.

        Upon creation, the hosted connection is initially in the
        'Ordering' state, and will remain in this state until the
        owner calls ConfirmConnection to confirm creation of the
        hosted connection.

        :type connection_id: string
        :param connection_id: ID of the connection.
        Example: dxcon-fg5678gh

        Default: None

        """
        params = {'connectionId': connection_id, }
        return self.make_request(action='ConfirmConnection',
                                 body=json.dumps(params))

    def confirm_private_virtual_interface(self, virtual_interface_id,
                                          virtual_gateway_id):
        """
        Accept ownership of a private virtual interface created by
        another customer.

        After the virtual interface owner calls this function, the
        virtual interface will be created and attached to the given
        virtual private gateway, and will be available for handling
        traffic.

        :type virtual_interface_id: string
        :param virtual_interface_id: ID of the virtual interface.
        Example: dxvif-123dfg56

        Default: None

        :type virtual_gateway_id: string
        :param virtual_gateway_id: ID of the virtual private gateway that will
            be attached to the virtual interface.
        A virtual private gateway can be managed via the Amazon Virtual Private
            Cloud (VPC) console or the `EC2 CreateVpnGateway`_ action.

        Default: None

        """
        params = {
            'virtualInterfaceId': virtual_interface_id,
            'virtualGatewayId': virtual_gateway_id,
        }
        return self.make_request(action='ConfirmPrivateVirtualInterface',
                                 body=json.dumps(params))

    def confirm_public_virtual_interface(self, virtual_interface_id):
        """
        Accept ownership of a public virtual interface created by
        another customer.

        After the virtual interface owner calls this function, the
        specified virtual interface will be created and made available
        for handling traffic.

        :type virtual_interface_id: string
        :param virtual_interface_id: ID of the virtual interface.
        Example: dxvif-123dfg56

        Default: None

        """
        params = {'virtualInterfaceId': virtual_interface_id, }
        return self.make_request(action='ConfirmPublicVirtualInterface',
                                 body=json.dumps(params))

    def create_connection(self, location, bandwidth, connection_name):
        """
        Creates a new connection between the customer network and a
        specific AWS Direct Connect location.

        A connection links your internal network to an AWS Direct
        Connect location over a standard 1 gigabit or 10 gigabit
        Ethernet fiber-optic cable. One end of the cable is connected
        to your router, the other to an AWS Direct Connect router. An
        AWS Direct Connect location provides access to Amazon Web
        Services in the region it is associated with. You can
        establish connections with AWS Direct Connect locations in
        multiple regions, but a connection in one region does not
        provide connectivity to other regions.

        :type location: string
        :param location: Where the connection is located.
        Example: EqSV5

        Default: None

        :type bandwidth: string
        :param bandwidth: Bandwidth of the connection.
        Example: 1Gbps

        Default: None

        :type connection_name: string
        :param connection_name: The name of the connection.
        Example: " My Connection to AWS "

        Default: None

        """
        params = {
            'location': location,
            'bandwidth': bandwidth,
            'connectionName': connection_name,
        }
        return self.make_request(action='CreateConnection',
                                 body=json.dumps(params))

    def create_interconnect(self, interconnect_name, bandwidth, location):
        """
        Creates a new interconnect between a AWS Direct Connect
        partner's network and a specific AWS Direct Connect location.

        An interconnect is a connection which is capable of hosting
        other connections. The AWS Direct Connect partner can use an
        interconnect to provide sub-1Gbps AWS Direct Connect service
        to tier 2 customers who do not have their own connections.
        Like a standard connection, an interconnect links the AWS
        Direct Connect partner's network to an AWS Direct Connect
        location over a standard 1 Gbps or 10 Gbps Ethernet fiber-
        optic cable. One end is connected to the partner's router, the
        other to an AWS Direct Connect router.

        For each end customer, the AWS Direct Connect partner
        provisions a connection on their interconnect by calling
        AllocateConnectionOnInterconnect. The end customer can then
        connect to AWS resources by creating a virtual interface on
        their connection, using the VLAN assigned to them by the AWS
        Direct Connect partner.

        :type interconnect_name: string
        :param interconnect_name: The name of the interconnect.
        Example: " 1G Interconnect to AWS "

        Default: None

        :type bandwidth: string
        :param bandwidth: The port bandwidth
        Example: 1Gbps

        Default: None

        Available values: 1Gbps,10Gbps

        :type location: string
        :param location: Where the interconnect is located
        Example: EqSV5

        Default: None

        """
        params = {
            'interconnectName': interconnect_name,
            'bandwidth': bandwidth,
            'location': location,
        }
        return self.make_request(action='CreateInterconnect',
                                 body=json.dumps(params))

    def create_private_virtual_interface(self, connection_id,
                                         new_private_virtual_interface):
        """
        Creates a new private virtual interface. A virtual interface
        is the VLAN that transports AWS Direct Connect traffic. A
        private virtual interface supports sending traffic to a single
        virtual private cloud (VPC).

        :type connection_id: string
        :param connection_id: ID of the connection.
        Example: dxcon-fg5678gh

        Default: None

        :type new_private_virtual_interface: dict
        :param new_private_virtual_interface: Detailed information for the
            private virtual interface to be created.
        Default: None

        """
        params = {
            'connectionId': connection_id,
            'newPrivateVirtualInterface': new_private_virtual_interface,
        }
        return self.make_request(action='CreatePrivateVirtualInterface',
                                 body=json.dumps(params))

    def create_public_virtual_interface(self, connection_id,
                                        new_public_virtual_interface):
        """
        Creates a new public virtual interface. A virtual interface is
        the VLAN that transports AWS Direct Connect traffic. A public
        virtual interface supports sending traffic to public services
        of AWS such as Amazon Simple Storage Service (Amazon S3).

        :type connection_id: string
        :param connection_id: ID of the connection.
        Example: dxcon-fg5678gh

        Default: None

        :type new_public_virtual_interface: dict
        :param new_public_virtual_interface: Detailed information for the
            public virtual interface to be created.
        Default: None

        """
        params = {
            'connectionId': connection_id,
            'newPublicVirtualInterface': new_public_virtual_interface,
        }
        return self.make_request(action='CreatePublicVirtualInterface',
                                 body=json.dumps(params))

    def delete_connection(self, connection_id):
        """
        Deletes the connection.

        Deleting a connection only stops the AWS Direct Connect port
        hour and data transfer charges. You need to cancel separately
        with the providers any services or charges for cross-connects
        or network circuits that connect you to the AWS Direct Connect
        location.

        :type connection_id: string
        :param connection_id: ID of the connection.
        Example: dxcon-fg5678gh

        Default: None

        """
        params = {'connectionId': connection_id, }
        return self.make_request(action='DeleteConnection',
                                 body=json.dumps(params))

    def delete_interconnect(self, interconnect_id):
        """
        Deletes the specified interconnect.

        :type interconnect_id: string
        :param interconnect_id: The ID of the interconnect.
        Example: dxcon-abc123

        """
        params = {'interconnectId': interconnect_id, }
        return self.make_request(action='DeleteInterconnect',
                                 body=json.dumps(params))

    def delete_virtual_interface(self, virtual_interface_id):
        """
        Deletes a virtual interface.

        :type virtual_interface_id: string
        :param virtual_interface_id: ID of the virtual interface.
        Example: dxvif-123dfg56

        Default: None

        """
        params = {'virtualInterfaceId': virtual_interface_id, }
        return self.make_request(action='DeleteVirtualInterface',
                                 body=json.dumps(params))

    def describe_connections(self, connection_id=None):
        """
        Displays all connections in this region.

        If a connection ID is provided, the call returns only that
        particular connection.

        :type connection_id: string
        :param connection_id: ID of the connection.
        Example: dxcon-fg5678gh

        Default: None

        """
        params = {}
        if connection_id is not None:
            params['connectionId'] = connection_id
        return self.make_request(action='DescribeConnections',
                                 body=json.dumps(params))

    def describe_connections_on_interconnect(self, interconnect_id):
        """
        Return a list of connections that have been provisioned on the
        given interconnect.

        :type interconnect_id: string
        :param interconnect_id: ID of the interconnect on which a list of
            connection is provisioned.
        Example: dxcon-abc123

        Default: None

        """
        params = {'interconnectId': interconnect_id, }
        return self.make_request(action='DescribeConnectionsOnInterconnect',
                                 body=json.dumps(params))

    def describe_interconnects(self, interconnect_id=None):
        """
        Returns a list of interconnects owned by the AWS account.

        If an interconnect ID is provided, it will only return this
        particular interconnect.

        :type interconnect_id: string
        :param interconnect_id: The ID of the interconnect.
        Example: dxcon-abc123

        """
        params = {}
        if interconnect_id is not None:
            params['interconnectId'] = interconnect_id
        return self.make_request(action='DescribeInterconnects',
                                 body=json.dumps(params))

    def describe_locations(self):
        """
        Returns the list of AWS Direct Connect locations in the
        current AWS region. These are the locations that may be
        selected when calling CreateConnection or CreateInterconnect.
        """
        params = {}
        return self.make_request(action='DescribeLocations',
                                 body=json.dumps(params))

    def describe_virtual_gateways(self):
        """
        Returns a list of virtual private gateways owned by the AWS
        account.

        You can create one or more AWS Direct Connect private virtual
        interfaces linking to a virtual private gateway. A virtual
        private gateway can be managed via Amazon Virtual Private
        Cloud (VPC) console or the `EC2 CreateVpnGateway`_ action.
        """
        params = {}
        return self.make_request(action='DescribeVirtualGateways',
                                 body=json.dumps(params))

    def describe_virtual_interfaces(self, connection_id=None,
                                    virtual_interface_id=None):
        """
        Displays all virtual interfaces for an AWS account. Virtual
        interfaces deleted fewer than 15 minutes before
        DescribeVirtualInterfaces is called are also returned. If a
        connection ID is included then only virtual interfaces
        associated with this connection will be returned. If a virtual
        interface ID is included then only a single virtual interface
        will be returned.

        A virtual interface (VLAN) transmits the traffic between the
        AWS Direct Connect location and the customer.

        If a connection ID is provided, only virtual interfaces
        provisioned on the specified connection will be returned. If a
        virtual interface ID is provided, only this particular virtual
        interface will be returned.

        :type connection_id: string
        :param connection_id: ID of the connection.
        Example: dxcon-fg5678gh

        Default: None

        :type virtual_interface_id: string
        :param virtual_interface_id: ID of the virtual interface.
        Example: dxvif-123dfg56

        Default: None

        """
        params = {}
        if connection_id is not None:
            params['connectionId'] = connection_id
        if virtual_interface_id is not None:
            params['virtualInterfaceId'] = virtual_interface_id
        return self.make_request(action='DescribeVirtualInterfaces',
                                 body=json.dumps(params))

    def make_request(self, action, body):
        headers = {
            'X-Amz-Target': '%s.%s' % (self.TargetPrefix, action),
            'Host': self.region.endpoint,
            'Content-Type': 'application/x-amz-json-1.1',
            'Content-Length': str(len(body)),
        }
        http_request = self.build_base_http_request(
            method='POST', path='/', auth_path='/', params={},
            headers=headers, data=body)
        response = self._mexe(http_request, sender=None,
                              override_num_retries=10)
        response_body = response.read().decode('utf-8')
        boto.log.debug(response_body)
        if response.status == 200:
            if response_body:
                return json.loads(response_body)
        else:
            json_body = json.loads(response_body)
            fault_name = json_body.get('__type', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)
