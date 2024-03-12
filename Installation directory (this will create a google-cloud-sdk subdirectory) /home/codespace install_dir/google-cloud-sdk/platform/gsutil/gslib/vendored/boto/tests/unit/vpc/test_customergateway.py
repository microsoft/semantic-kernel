from tests.compat import OrderedDict
from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.vpc import VPCConnection, CustomerGateway


class TestDescribeCustomerGateways(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DescribeCustomerGatewaysResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
              <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
              <customerGatewaySet>
                <item>
                   <customerGatewayId>cgw-b4dc3961</customerGatewayId>
                   <state>available</state>
                   <type>ipsec.1</type>
                   <ipAddress>12.1.2.3</ipAddress>
                   <bgpAsn>65534</bgpAsn>
                   <tagSet/>
                </item>
              </customerGatewaySet>
            </DescribeCustomerGatewaysResponse>
        """

    def test_get_all_customer_gateways(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.get_all_customer_gateways(
            'cgw-b4dc3961',
            filters=OrderedDict([('state', ['pending', 'available']),
                     ('ip-address', '12.1.2.3')]))
        self.assert_request_parameters({
            'Action': 'DescribeCustomerGateways',
            'CustomerGatewayId.1': 'cgw-b4dc3961',
            'Filter.1.Name': 'state',
            'Filter.1.Value.1': 'pending',
            'Filter.1.Value.2': 'available',
            'Filter.2.Name': 'ip-address',
            'Filter.2.Value.1': '12.1.2.3'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(len(api_response), 1)
        self.assertIsInstance(api_response[0], CustomerGateway)
        self.assertEqual(api_response[0].id, 'cgw-b4dc3961')


class TestCreateCustomerGateway(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateCustomerGatewayResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <customerGateway>
                  <customerGatewayId>cgw-b4dc3961</customerGatewayId>
                  <state>pending</state>
                  <type>ipsec.1</type>
                  <ipAddress>12.1.2.3</ipAddress>
                  <bgpAsn>65534</bgpAsn>
                  <tagSet/>
               </customerGateway>
            </CreateCustomerGatewayResponse>
        """

    def test_create_customer_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_customer_gateway(
            'ipsec.1', '12.1.2.3', 65534)
        self.assert_request_parameters({
            'Action': 'CreateCustomerGateway',
            'Type': 'ipsec.1',
            'IpAddress': '12.1.2.3',
            'BgpAsn': 65534},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertIsInstance(api_response, CustomerGateway)
        self.assertEquals(api_response.id, 'cgw-b4dc3961')
        self.assertEquals(api_response.state, 'pending')
        self.assertEquals(api_response.type, 'ipsec.1')
        self.assertEquals(api_response.ip_address, '12.1.2.3')
        self.assertEquals(api_response.bgp_asn, 65534)


class TestDeleteCustomerGateway(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteCustomerGatewayResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <return>true</return>
            </DeleteCustomerGatewayResponse>
        """

    def test_delete_customer_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_customer_gateway('cgw-b4dc3961')
        self.assert_request_parameters({
            'Action': 'DeleteCustomerGateway',
            'CustomerGatewayId': 'cgw-b4dc3961'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


if __name__ == '__main__':
    unittest.main()
