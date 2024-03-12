# Copyright (c) 2014 Skytap http://skytap.com/
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

from tests.unit import mock, unittest
from tests.unit import AWSMockServiceTestCase

from boto.vpc import VpcPeeringConnection, VPCConnection, Subnet


class TestDescribeVpcPeeringConnections(AWSMockServiceTestCase):
    DESCRIBE_VPC_PEERING_CONNECTIONS= b"""<?xml version="1.0" encoding="UTF-8"?>
<DescribeVpcPeeringConnectionsResponse xmlns="http://ec2.amazonaws.com/doc/2014-05-01/">
   <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
    <vpcPeeringConnectionSet>
        <item>
           <vpcPeeringConnectionId>pcx-111aaa22</vpcPeeringConnectionId>
            <requesterVpcInfo>
               <ownerId>777788889999</ownerId>
                <vpcId>vpc-1a2b3c4d</vpcId>
              <cidrBlock>172.31.0.0/16</cidrBlock>
           </requesterVpcInfo>
           <accepterVpcInfo>
                <ownerId>111122223333</ownerId>
               <vpcId>vpc-aa22cc33</vpcId>
           </accepterVpcInfo>
            <status>
                <code>pending-acceptance</code>
               <message>Pending Acceptance by 111122223333</message>
            </status>
           <expirationTime>2014-02-17T16:00:50.000Z</expirationTime>
        </item>
        <item>
           <vpcPeeringConnectionId>pcx-444bbb88</vpcPeeringConnectionId>
            <requesterVpcInfo>
               <ownerId>1237897234</ownerId>
                <vpcId>vpc-2398abcd</vpcId>
              <cidrBlock>172.30.0.0/16</cidrBlock>
           </requesterVpcInfo>
           <accepterVpcInfo>
                <ownerId>98654313</ownerId>
               <vpcId>vpc-0983bcda</vpcId>
           </accepterVpcInfo>
            <status>
                <code>pending-acceptance</code>
               <message>Pending Acceptance by 98654313</message>
            </status>
           <expirationTime>2015-02-17T16:00:50.000Z</expirationTime>
        </item>
    </vpcPeeringConnectionSet>
</DescribeVpcPeeringConnectionsResponse>"""
    
    connection_class = VPCConnection

    def default_body(self):
        return self.DESCRIBE_VPC_PEERING_CONNECTIONS

    def test_get_vpc_peering_connections(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.get_all_vpc_peering_connections(
            ['pcx-111aaa22', 'pcx-444bbb88'], filters=[('status-code', ['pending-acceptance'])])

        self.assertEqual(len(api_response), 2)

        for vpc_peering_connection in api_response:
            if vpc_peering_connection.id == 'pcx-111aaa22':
                self.assertEqual(vpc_peering_connection.id, 'pcx-111aaa22')
                self.assertEqual(vpc_peering_connection.status_code, 'pending-acceptance')
                self.assertEqual(vpc_peering_connection.status_message, 'Pending Acceptance by 111122223333')
                self.assertEqual(vpc_peering_connection.requester_vpc_info.owner_id, '777788889999')
                self.assertEqual(vpc_peering_connection.requester_vpc_info.vpc_id, 'vpc-1a2b3c4d')
                self.assertEqual(vpc_peering_connection.requester_vpc_info.cidr_block, '172.31.0.0/16')
                self.assertEqual(vpc_peering_connection.accepter_vpc_info.owner_id, '111122223333')
                self.assertEqual(vpc_peering_connection.accepter_vpc_info.vpc_id, 'vpc-aa22cc33')
                self.assertEqual(vpc_peering_connection.expiration_time, '2014-02-17T16:00:50.000Z')
            else:
                self.assertEqual(vpc_peering_connection.id, 'pcx-444bbb88')
                self.assertEqual(vpc_peering_connection.status_code, 'pending-acceptance')
                self.assertEqual(vpc_peering_connection.status_message, 'Pending Acceptance by 98654313')
                self.assertEqual(vpc_peering_connection.requester_vpc_info.owner_id, '1237897234')
                self.assertEqual(vpc_peering_connection.requester_vpc_info.vpc_id, 'vpc-2398abcd')
                self.assertEqual(vpc_peering_connection.requester_vpc_info.cidr_block, '172.30.0.0/16')
                self.assertEqual(vpc_peering_connection.accepter_vpc_info.owner_id, '98654313')
                self.assertEqual(vpc_peering_connection.accepter_vpc_info.vpc_id, 'vpc-0983bcda')
                self.assertEqual(vpc_peering_connection.expiration_time, '2015-02-17T16:00:50.000Z')


class TestCreateVpcPeeringConnection(AWSMockServiceTestCase):
    CREATE_VPC_PEERING_CONNECTION= b"""<CreateVpcPeeringConnectionResponse xmlns="http://ec2.amazonaws.com/doc/2014-05-01/">
  <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
  <vpcPeeringConnection>
        <vpcPeeringConnectionId>pcx-73a5401a</vpcPeeringConnectionId>
        <requesterVpcInfo>
            <ownerId>777788889999</ownerId>
            <vpcId>vpc-1a2b3c4d</vpcId>
            <cidrBlock>10.0.0.0/28</cidrBlock>
        </requesterVpcInfo>
        <accepterVpcInfo>
            <ownerId>123456789012</ownerId>
            <vpcId>vpc-a1b2c3d4</vpcId>
        </accepterVpcInfo>
        <status>
            <code>initiating-request</code>
            <message>Initiating Request to 123456789012</message>
        </status>
        <expirationTime>2014-02-18T14:37:25.000Z</expirationTime>
        <tagSet/>
    </vpcPeeringConnection>
</CreateVpcPeeringConnectionResponse>"""
    
    connection_class = VPCConnection

    def default_body(self):
        return self.CREATE_VPC_PEERING_CONNECTION

    def test_create_vpc_peering_connection(self):
        self.set_http_response(status_code=200)
        vpc_peering_connection = self.service_connection.create_vpc_peering_connection('vpc-1a2b3c4d', 'vpc-a1b2c3d4', '123456789012')

        self.assertEqual(vpc_peering_connection.id, 'pcx-73a5401a')
        self.assertEqual(vpc_peering_connection.status_code, 'initiating-request')
        self.assertEqual(vpc_peering_connection.status_message, 'Initiating Request to 123456789012')
        self.assertEqual(vpc_peering_connection.requester_vpc_info.owner_id, '777788889999')
        self.assertEqual(vpc_peering_connection.requester_vpc_info.vpc_id, 'vpc-1a2b3c4d')
        self.assertEqual(vpc_peering_connection.requester_vpc_info.cidr_block, '10.0.0.0/28')
        self.assertEqual(vpc_peering_connection.accepter_vpc_info.owner_id, '123456789012')
        self.assertEqual(vpc_peering_connection.accepter_vpc_info.vpc_id, 'vpc-a1b2c3d4')
        self.assertEqual(vpc_peering_connection.expiration_time, '2014-02-18T14:37:25.000Z')

class TestDeleteVpcPeeringConnection(AWSMockServiceTestCase):
    DELETE_VPC_PEERING_CONNECTION= b"""<DeleteVpcPeeringConnectionResponse xmlns="http://ec2.amazonaws.com/doc/2014-05-01/">
  <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
  <return>true</return>
</DeleteVpcPeeringConnectionResponse>"""
    
    connection_class = VPCConnection

    def default_body(self):
        return self.DELETE_VPC_PEERING_CONNECTION

    def test_delete_vpc_peering_connection(self):
        self.set_http_response(status_code=200)
        self.assertEquals(self.service_connection.delete_vpc_peering_connection('pcx-12345678'), True)

class TestDeleteVpcPeeringConnectionShortForm(unittest.TestCase):
    DESCRIBE_VPC_PEERING_CONNECTIONS= b"""<?xml version="1.0" encoding="UTF-8"?>
<DescribeVpcPeeringConnectionsResponse xmlns="http://ec2.amazonaws.com/doc/2014-05-01/">
   <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
   <vpcPeeringConnectionSet>
      <item>
         <vpcPeeringConnectionId>pcx-111aaa22</vpcPeeringConnectionId>
         <requesterVpcInfo>
            <ownerId>777788889999</ownerId>
            <vpcId>vpc-1a2b3c4d</vpcId>
            <cidrBlock>172.31.0.0/16</cidrBlock>
         </requesterVpcInfo>
         <accepterVpcInfo>
            <ownerId>111122223333</ownerId>
            <vpcId>vpc-aa22cc33</vpcId>
         </accepterVpcInfo>
         <status>
            <code>pending-acceptance</code>
            <message>Pending Acceptance by 111122223333</message>
         </status>
         <expirationTime>2014-02-17T16:00:50.000Z</expirationTime>
      </item>
   </vpcPeeringConnectionSet>
</DescribeVpcPeeringConnectionsResponse>"""

    DELETE_VPC_PEERING_CONNECTION= b"""<DeleteVpcPeeringConnectionResponse xmlns="http://ec2.amazonaws.com/doc/2014-05-01/">
  <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
  <return>true</return>
</DeleteVpcPeeringConnectionResponse>"""

    def test_delete_vpc_peering_connection(self):
        vpc_conn = VPCConnection(aws_access_key_id='aws_access_key_id',
                                 aws_secret_access_key='aws_secret_access_key')

        mock_response = mock.Mock()
        mock_response.read.return_value = self.DESCRIBE_VPC_PEERING_CONNECTIONS
        mock_response.status = 200
        vpc_conn.make_request = mock.Mock(return_value=mock_response)
        vpc_peering_connections = vpc_conn.get_all_vpc_peering_connections()

        self.assertEquals(1, len(vpc_peering_connections))
        vpc_peering_connection = vpc_peering_connections[0]

        mock_response = mock.Mock()
        mock_response.read.return_value = self.DELETE_VPC_PEERING_CONNECTION
        mock_response.status = 200
        vpc_conn.make_request = mock.Mock(return_value=mock_response)
        self.assertEquals(True, vpc_peering_connection.delete())

        self.assertIn('DeleteVpcPeeringConnection', vpc_conn.make_request.call_args_list[0][0])
        self.assertNotIn('DeleteVpc', vpc_conn.make_request.call_args_list[0][0])

class TestRejectVpcPeeringConnection(AWSMockServiceTestCase):
    REJECT_VPC_PEERING_CONNECTION= b"""<RejectVpcPeeringConnectionResponse xmlns="http://ec2.amazonaws.com/doc/2014-05-01/">
  <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
  <return>true</return>
</RejectVpcPeeringConnectionResponse>"""
    
    connection_class = VPCConnection

    def default_body(self):
        return self.REJECT_VPC_PEERING_CONNECTION

    def test_reject_vpc_peering_connection(self):
        self.set_http_response(status_code=200)
        self.assertEquals(self.service_connection.reject_vpc_peering_connection('pcx-12345678'), True)


class TestAcceptVpcPeeringConnection(AWSMockServiceTestCase):
    ACCEPT_VPC_PEERING_CONNECTION= b"""<AcceptVpcPeeringConnectionResponse xmlns="http://ec2.amazonaws.com/doc/2014-05-01/">
  <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
  <vpcPeeringConnection>
        <vpcPeeringConnectionId>pcx-1a2b3c4d</vpcPeeringConnectionId>
       <requesterVpcInfo>
            <ownerId>123456789012</ownerId>
            <vpcId>vpc-1a2b3c4d</vpcId>
            <cidrBlock>10.0.0.0/28</cidrBlock>
        </requesterVpcInfo>
        <accepterVpcInfo>
            <ownerId>777788889999</ownerId>
            <vpcId>vpc-111aaa22</vpcId>
            <cidrBlock>10.0.1.0/28</cidrBlock>
        </accepterVpcInfo>
        <status>
            <code>active</code>
            <message>Active</message>
        </status>
        <tagSet/>
    </vpcPeeringConnection>
</AcceptVpcPeeringConnectionResponse>"""
    
    connection_class = VPCConnection

    def default_body(self):
        return self.ACCEPT_VPC_PEERING_CONNECTION

    def test_accept_vpc_peering_connection(self):
        self.set_http_response(status_code=200)
        vpc_peering_connection = self.service_connection.accept_vpc_peering_connection('pcx-1a2b3c4d')

        self.assertEqual(vpc_peering_connection.id, 'pcx-1a2b3c4d')
        self.assertEqual(vpc_peering_connection.status_code, 'active')
        self.assertEqual(vpc_peering_connection.status_message, 'Active')
        self.assertEqual(vpc_peering_connection.requester_vpc_info.owner_id, '123456789012')
        self.assertEqual(vpc_peering_connection.requester_vpc_info.vpc_id, 'vpc-1a2b3c4d')
        self.assertEqual(vpc_peering_connection.requester_vpc_info.cidr_block, '10.0.0.0/28')
        self.assertEqual(vpc_peering_connection.accepter_vpc_info.owner_id, '777788889999')
        self.assertEqual(vpc_peering_connection.accepter_vpc_info.vpc_id, 'vpc-111aaa22')
        self.assertEqual(vpc_peering_connection.accepter_vpc_info.cidr_block, '10.0.1.0/28')



if __name__ == '__main__':
    unittest.main()
