from tests.compat import OrderedDict
from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.vpc import VPCConnection, Subnet


class TestDescribeSubnets(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DescribeSubnetsResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
              <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
              <subnetSet>
                <item>
                  <subnetId>subnet-9d4a7b6c</subnetId>
                  <state>available</state>
                  <vpcId>vpc-1a2b3c4d</vpcId>
                  <cidrBlock>10.0.1.0/24</cidrBlock>
                  <availableIpAddressCount>251</availableIpAddressCount>
                  <availabilityZone>us-east-1a</availabilityZone>
                  <defaultForAz>false</defaultForAz>
                  <mapPublicIpOnLaunch>false</mapPublicIpOnLaunch>
                  <tagSet/>
                </item>
                <item>
                  <subnetId>subnet-6e7f829e</subnetId>
                  <state>available</state>
                  <vpcId>vpc-1a2b3c4d</vpcId>
                  <cidrBlock>10.0.0.0/24</cidrBlock>
                  <availableIpAddressCount>251</availableIpAddressCount>
                  <availabilityZone>us-east-1a</availabilityZone>
                  <defaultForAz>false</defaultForAz>
                  <mapPublicIpOnLaunch>false</mapPublicIpOnLaunch>
                  <tagSet/>
                </item>
              </subnetSet>
            </DescribeSubnetsResponse>
        """

    def test_get_all_subnets(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.get_all_subnets(
            ['subnet-9d4a7b6c', 'subnet-6e7f829e'],
            filters=OrderedDict([('state', 'available'),
                     ('vpc-id', ['subnet-9d4a7b6c', 'subnet-6e7f829e'])]))
        self.assert_request_parameters({
            'Action': 'DescribeSubnets',
            'SubnetId.1': 'subnet-9d4a7b6c',
            'SubnetId.2': 'subnet-6e7f829e',
            'Filter.1.Name': 'state',
            'Filter.1.Value.1': 'available',
            'Filter.2.Name': 'vpc-id',
            'Filter.2.Value.1': 'subnet-9d4a7b6c',
            'Filter.2.Value.2': 'subnet-6e7f829e'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(len(api_response), 2)
        self.assertIsInstance(api_response[0], Subnet)
        self.assertEqual(api_response[0].id, 'subnet-9d4a7b6c')
        self.assertEqual(api_response[1].id, 'subnet-6e7f829e')


class TestCreateSubnet(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateSubnetResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
              <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
              <subnet>
                <subnetId>subnet-9d4a7b6c</subnetId>
                <state>pending</state>
                <vpcId>vpc-1a2b3c4d</vpcId>
                <cidrBlock>10.0.1.0/24</cidrBlock>
                <availableIpAddressCount>251</availableIpAddressCount>
                <availabilityZone>us-east-1a</availabilityZone>
                <tagSet/>
              </subnet>
            </CreateSubnetResponse>
        """

    def test_create_subnet(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_subnet(
            'vpc-1a2b3c4d', '10.0.1.0/24', 'us-east-1a')
        self.assert_request_parameters({
            'Action': 'CreateSubnet',
            'VpcId': 'vpc-1a2b3c4d',
            'CidrBlock': '10.0.1.0/24',
            'AvailabilityZone': 'us-east-1a'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertIsInstance(api_response, Subnet)
        self.assertEquals(api_response.id, 'subnet-9d4a7b6c')
        self.assertEquals(api_response.state, 'pending')
        self.assertEquals(api_response.vpc_id, 'vpc-1a2b3c4d')
        self.assertEquals(api_response.cidr_block, '10.0.1.0/24')
        self.assertEquals(api_response.available_ip_address_count, 251)
        self.assertEquals(api_response.availability_zone, 'us-east-1a')


class TestDeleteSubnet(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteSubnetResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <return>true</return>
            </DeleteSubnetResponse>
        """

    def test_delete_subnet(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_subnet('subnet-9d4a7b6c')
        self.assert_request_parameters({
            'Action': 'DeleteSubnet',
            'SubnetId': 'subnet-9d4a7b6c'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


if __name__ == '__main__':
    unittest.main()
