from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.vpc import VPCConnection, RouteTable


class TestDescribeRouteTables(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DescribeRouteTablesResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>6f570b0b-9c18-4b07-bdec-73740dcf861a</requestId>
               <routeTableSet>
                  <item>
                     <routeTableId>rtb-13ad487a</routeTableId>
                     <vpcId>vpc-11ad4878</vpcId>
                     <routeSet>
                        <item>
                           <destinationCidrBlock>10.0.0.0/22</destinationCidrBlock>
                           <gatewayId>local</gatewayId>
                           <state>active</state>
                           <origin>CreateRouteTable</origin>
                        </item>
                     </routeSet>
                     <associationSet>
                         <item>
                            <routeTableAssociationId>rtbassoc-12ad487b</routeTableAssociationId>
                            <routeTableId>rtb-13ad487a</routeTableId>
                            <main>true</main>
                         </item>
                     </associationSet>
                     <tagSet/>
                  </item>
                  <item>
                     <routeTableId>rtb-f9ad4890</routeTableId>
                     <vpcId>vpc-11ad4878</vpcId>
                     <routeSet>
                        <item>
                           <destinationCidrBlock>10.0.0.0/22</destinationCidrBlock>
                           <gatewayId>local</gatewayId>
                           <state>active</state>
                           <origin>CreateRouteTable</origin>
                        </item>
                        <item>
                           <destinationCidrBlock>0.0.0.0/0</destinationCidrBlock>
                           <gatewayId>igw-eaad4883</gatewayId>
                           <state>active</state>
                            <origin>CreateRoute</origin>
                        </item>
                        <item>
                            <destinationCidrBlock>10.0.0.0/21</destinationCidrBlock>
                            <networkInterfaceId>eni-884ec1d1</networkInterfaceId>
                            <state>blackhole</state>
                            <origin>CreateRoute</origin>
                        </item>
                        <item>
                            <destinationCidrBlock>11.0.0.0/22</destinationCidrBlock>
                            <vpcPeeringConnectionId>pcx-efc52b86</vpcPeeringConnectionId>
                            <state>blackhole</state>
                            <origin>CreateRoute</origin>
                        </item>
                     </routeSet>
                     <associationSet>
                        <item>
                            <routeTableAssociationId>rtbassoc-faad4893</routeTableAssociationId>
                            <routeTableId>rtb-f9ad4890</routeTableId>
                            <subnetId>subnet-15ad487c</subnetId>
                        </item>
                     </associationSet>
                     <tagSet/>
                  </item>
               </routeTableSet>
            </DescribeRouteTablesResponse>
        """

    def test_get_all_route_tables(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.get_all_route_tables(
            ['rtb-13ad487a', 'rtb-f9ad4890'], filters=[('route.state', 'active')])
        self.assert_request_parameters({
            'Action': 'DescribeRouteTables',
            'RouteTableId.1': 'rtb-13ad487a',
            'RouteTableId.2': 'rtb-f9ad4890',
            'Filter.1.Name': 'route.state',
            'Filter.1.Value.1': 'active'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(len(api_response), 2)
        self.assertIsInstance(api_response[0], RouteTable)
        self.assertEquals(api_response[0].id, 'rtb-13ad487a')
        self.assertEquals(len(api_response[0].routes), 1)
        self.assertEquals(api_response[0].routes[0].destination_cidr_block, '10.0.0.0/22')
        self.assertEquals(api_response[0].routes[0].gateway_id, 'local')
        self.assertEquals(api_response[0].routes[0].state, 'active')
        self.assertEquals(api_response[0].routes[0].origin, 'CreateRouteTable')
        self.assertEquals(len(api_response[0].associations), 1)
        self.assertEquals(api_response[0].associations[0].id, 'rtbassoc-12ad487b')
        self.assertEquals(api_response[0].associations[0].route_table_id, 'rtb-13ad487a')
        self.assertIsNone(api_response[0].associations[0].subnet_id)
        self.assertEquals(api_response[0].associations[0].main, True)
        self.assertEquals(api_response[1].id, 'rtb-f9ad4890')
        self.assertEquals(len(api_response[1].routes), 4)
        self.assertEquals(api_response[1].routes[0].destination_cidr_block, '10.0.0.0/22')
        self.assertEquals(api_response[1].routes[0].gateway_id, 'local')
        self.assertEquals(api_response[1].routes[0].state, 'active')
        self.assertEquals(api_response[1].routes[0].origin, 'CreateRouteTable')
        self.assertEquals(api_response[1].routes[1].destination_cidr_block, '0.0.0.0/0')
        self.assertEquals(api_response[1].routes[1].gateway_id, 'igw-eaad4883')
        self.assertEquals(api_response[1].routes[1].state, 'active')
        self.assertEquals(api_response[1].routes[1].origin, 'CreateRoute')
        self.assertEquals(api_response[1].routes[2].destination_cidr_block, '10.0.0.0/21')
        self.assertEquals(api_response[1].routes[2].interface_id, 'eni-884ec1d1')
        self.assertEquals(api_response[1].routes[2].state, 'blackhole')
        self.assertEquals(api_response[1].routes[2].origin, 'CreateRoute')
        self.assertEquals(api_response[1].routes[3].destination_cidr_block, '11.0.0.0/22')
        self.assertEquals(api_response[1].routes[3].vpc_peering_connection_id, 'pcx-efc52b86')
        self.assertEquals(api_response[1].routes[3].state, 'blackhole')
        self.assertEquals(api_response[1].routes[3].origin, 'CreateRoute')
        self.assertEquals(len(api_response[1].associations), 1)
        self.assertEquals(api_response[1].associations[0].id, 'rtbassoc-faad4893')
        self.assertEquals(api_response[1].associations[0].route_table_id, 'rtb-f9ad4890')
        self.assertEquals(api_response[1].associations[0].subnet_id, 'subnet-15ad487c')
        self.assertEquals(api_response[1].associations[0].main, False)


class TestAssociateRouteTable(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <AssociateRouteTableResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <associationId>rtbassoc-f8ad4891</associationId>
            </AssociateRouteTableResponse>
        """

    def test_associate_route_table(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.associate_route_table(
            'rtb-e4ad488d', 'subnet-15ad487c')
        self.assert_request_parameters({
            'Action': 'AssociateRouteTable',
            'RouteTableId': 'rtb-e4ad488d',
            'SubnetId': 'subnet-15ad487c'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, 'rtbassoc-f8ad4891')


class TestDisassociateRouteTable(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DisassociateRouteTableResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </DisassociateRouteTableResponse>
        """

    def test_disassociate_route_table(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.disassociate_route_table('rtbassoc-fdad4894')
        self.assert_request_parameters({
            'Action': 'DisassociateRouteTable',
            'AssociationId': 'rtbassoc-fdad4894'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


class TestCreateRouteTable(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateRouteTableResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <routeTable>
                  <routeTableId>rtb-f9ad4890</routeTableId>
                  <vpcId>vpc-11ad4878</vpcId>
                  <routeSet>
                     <item>
                        <destinationCidrBlock>10.0.0.0/22</destinationCidrBlock>
                        <gatewayId>local</gatewayId>
                        <state>active</state>
                     </item>
                  </routeSet>
                  <associationSet/>
                  <tagSet/>
               </routeTable>
            </CreateRouteTableResponse>
        """

    def test_create_route_table(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_route_table('vpc-11ad4878')
        self.assert_request_parameters({
            'Action': 'CreateRouteTable',
            'VpcId': 'vpc-11ad4878'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertIsInstance(api_response, RouteTable)
        self.assertEquals(api_response.id, 'rtb-f9ad4890')
        self.assertEquals(len(api_response.routes), 1)
        self.assertEquals(api_response.routes[0].destination_cidr_block, '10.0.0.0/22')
        self.assertEquals(api_response.routes[0].gateway_id, 'local')
        self.assertEquals(api_response.routes[0].state, 'active')


class TestDeleteRouteTable(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteRouteTableResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </DeleteRouteTableResponse>
        """

    def test_delete_route_table(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_route_table('rtb-e4ad488d')
        self.assert_request_parameters({
            'Action': 'DeleteRouteTable',
            'RouteTableId': 'rtb-e4ad488d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


class TestReplaceRouteTableAssociation(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <ReplaceRouteTableAssociationResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <newAssociationId>rtbassoc-faad4893</newAssociationId>
            </ReplaceRouteTableAssociationResponse>
        """

    def test_replace_route_table_assocation(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.replace_route_table_assocation(
            'rtbassoc-faad4893', 'rtb-f9ad4890')
        self.assert_request_parameters({
            'Action': 'ReplaceRouteTableAssociation',
            'AssociationId': 'rtbassoc-faad4893',
            'RouteTableId': 'rtb-f9ad4890'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

    def test_replace_route_table_association_with_assoc(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.replace_route_table_association_with_assoc(
            'rtbassoc-faad4893', 'rtb-f9ad4890')
        self.assert_request_parameters({
            'Action': 'ReplaceRouteTableAssociation',
            'AssociationId': 'rtbassoc-faad4893',
            'RouteTableId': 'rtb-f9ad4890'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, 'rtbassoc-faad4893')


class TestCreateRoute(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateRouteResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </CreateRouteResponse>
        """

    def test_create_route_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_route(
            'rtb-e4ad488d', '0.0.0.0/0', gateway_id='igw-eaad4883')
        self.assert_request_parameters({
            'Action': 'CreateRoute',
            'RouteTableId': 'rtb-e4ad488d',
            'DestinationCidrBlock': '0.0.0.0/0',
            'GatewayId': 'igw-eaad4883'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

    def test_create_route_instance(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_route(
            'rtb-g8ff4ea2', '0.0.0.0/0', instance_id='i-1a2b3c4d')
        self.assert_request_parameters({
            'Action': 'CreateRoute',
            'RouteTableId': 'rtb-g8ff4ea2',
            'DestinationCidrBlock': '0.0.0.0/0',
            'InstanceId': 'i-1a2b3c4d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

    def test_create_route_interface(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_route(
            'rtb-g8ff4ea2', '0.0.0.0/0', interface_id='eni-1a2b3c4d')
        self.assert_request_parameters({
            'Action': 'CreateRoute',
            'RouteTableId': 'rtb-g8ff4ea2',
            'DestinationCidrBlock': '0.0.0.0/0',
            'NetworkInterfaceId': 'eni-1a2b3c4d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

    def test_create_route_vpc_peering_connection(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_route(
            'rtb-g8ff4ea2', '0.0.0.0/0', vpc_peering_connection_id='pcx-1a2b3c4d')
        self.assert_request_parameters({
            'Action': 'CreateRoute',
            'RouteTableId': 'rtb-g8ff4ea2',
            'DestinationCidrBlock': '0.0.0.0/0',
            'VpcPeeringConnectionId': 'pcx-1a2b3c4d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


class TestReplaceRoute(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateRouteResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </CreateRouteResponse>
        """

    def test_replace_route_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.replace_route(
            'rtb-e4ad488d', '0.0.0.0/0', gateway_id='igw-eaad4883')
        self.assert_request_parameters({
            'Action': 'ReplaceRoute',
            'RouteTableId': 'rtb-e4ad488d',
            'DestinationCidrBlock': '0.0.0.0/0',
            'GatewayId': 'igw-eaad4883'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

    def test_replace_route_instance(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.replace_route(
            'rtb-g8ff4ea2', '0.0.0.0/0', instance_id='i-1a2b3c4d')
        self.assert_request_parameters({
            'Action': 'ReplaceRoute',
            'RouteTableId': 'rtb-g8ff4ea2',
            'DestinationCidrBlock': '0.0.0.0/0',
            'InstanceId': 'i-1a2b3c4d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

    def test_replace_route_interface(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.replace_route(
            'rtb-g8ff4ea2', '0.0.0.0/0', interface_id='eni-1a2b3c4d')
        self.assert_request_parameters({
            'Action': 'ReplaceRoute',
            'RouteTableId': 'rtb-g8ff4ea2',
            'DestinationCidrBlock': '0.0.0.0/0',
            'NetworkInterfaceId': 'eni-1a2b3c4d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

    def test_replace_route_vpc_peering_connection(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.replace_route(
            'rtb-g8ff4ea2', '0.0.0.0/0', vpc_peering_connection_id='pcx-1a2b3c4d')
        self.assert_request_parameters({
            'Action': 'ReplaceRoute',
            'RouteTableId': 'rtb-g8ff4ea2',
            'DestinationCidrBlock': '0.0.0.0/0',
            'VpcPeeringConnectionId': 'pcx-1a2b3c4d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


class TestDeleteRoute(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteRouteTableResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </DeleteRouteTableResponse>
        """

    def test_delete_route(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_route('rtb-e4ad488d', '172.16.1.0/24')
        self.assert_request_parameters({
            'Action': 'DeleteRoute',
            'RouteTableId': 'rtb-e4ad488d',
            'DestinationCidrBlock': '172.16.1.0/24'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

if __name__ == '__main__':
    unittest.main()
