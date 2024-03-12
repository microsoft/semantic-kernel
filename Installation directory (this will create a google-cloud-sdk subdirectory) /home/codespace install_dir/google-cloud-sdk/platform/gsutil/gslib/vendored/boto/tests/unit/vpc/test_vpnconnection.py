# -*- coding: UTF-8 -*-
from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.vpc import VPCConnection, VpnConnection

DESCRIBE_VPNCONNECTIONS = b'''<?xml version="1.0" encoding="UTF-8"?>
<DescribeVpnConnectionsResponse xmlns="http://ec2.amazonaws.com/doc/2013-02-01/">
    <requestId>12345678-asdf-ghjk-zxcv-0987654321nb</requestId>
    <vpnConnectionSet>
        <item>
            <vpnConnectionId>vpn-12qw34er56ty</vpnConnectionId>
            <state>available</state>
            <customerGatewayConfiguration>
                &lt;?xml version="1.0" encoding="UTF-8"?&gt;
            </customerGatewayConfiguration>
            <type>ipsec.1</type>
            <customerGatewayId>cgw-1234qwe9</customerGatewayId>
            <vpnGatewayId>vgw-lkjh1234</vpnGatewayId>
            <tagSet>
                <item>
                    <key>Name</key>
                    <value>VPN 1</value>
                </item>
            </tagSet>
            <vgwTelemetry>
                <item>
                    <outsideIpAddress>123.45.67.89</outsideIpAddress>
                    <status>DOWN</status>
                    <lastStatusChange>2013-03-19T19:20:34.000Z</lastStatusChange>
                    <statusMessage/>
                    <acceptedRouteCount>0</acceptedRouteCount>
                </item>
                <item>
                    <outsideIpAddress>123.45.67.90</outsideIpAddress>
                    <status>UP</status>
                    <lastStatusChange>2013-03-20T08:00:14.000Z</lastStatusChange>
                    <statusMessage/>
                    <acceptedRouteCount>0</acceptedRouteCount>
                </item>
            </vgwTelemetry>
            <options>
                <staticRoutesOnly>true</staticRoutesOnly>
            </options>
            <routes>
                <item>
                    <destinationCidrBlock>192.168.0.0/24</destinationCidrBlock>
                    <source>static</source>
                    <state>available</state>
                </item>
            </routes>
        </item>
        <item>
            <vpnConnectionId>vpn-qwerty12</vpnConnectionId>
            <state>pending</state>
            <customerGatewayConfiguration>
                &lt;?xml version="1.0" encoding="UTF-8"?&gt;
            </customerGatewayConfiguration>
            <type>ipsec.1</type>
            <customerGatewayId>cgw-01234567</customerGatewayId>
            <vpnGatewayId>vgw-asdfghjk</vpnGatewayId>
            <vgwTelemetry>
                <item>
                    <outsideIpAddress>134.56.78.78</outsideIpAddress>
                    <status>UP</status>
                    <lastStatusChange>2013-03-20T01:46:30.000Z</lastStatusChange>
                    <statusMessage/>
                    <acceptedRouteCount>0</acceptedRouteCount>
                </item>
                <item>
                    <outsideIpAddress>134.56.78.79</outsideIpAddress>
                    <status>UP</status>
                    <lastStatusChange>2013-03-19T19:23:59.000Z</lastStatusChange>
                    <statusMessage/>
                    <acceptedRouteCount>0</acceptedRouteCount>
                </item>
            </vgwTelemetry>
            <options>
                <staticRoutesOnly>true</staticRoutesOnly>
            </options>
            <routes>
                <item>
                    <destinationCidrBlock>10.0.0.0/16</destinationCidrBlock>
                    <source>static</source>
                    <state>pending</state>
                </item>
            </routes>
        </item>
    </vpnConnectionSet>
</DescribeVpnConnectionsResponse>'''


class TestDescribeVPNConnections(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return DESCRIBE_VPNCONNECTIONS

    def test_get_vpcs(self):
        self.set_http_response(status_code=200)

        api_response = self.service_connection.get_all_vpn_connections(
            ['vpn-12qw34er56ty', 'vpn-qwerty12'], filters=[('state', ['pending', 'available'])])
        self.assert_request_parameters({
            'Action': 'DescribeVpnConnections',
            'VpnConnectionId.1': 'vpn-12qw34er56ty',
            'VpnConnectionId.2': 'vpn-qwerty12',
            'Filter.1.Name': 'state',
            'Filter.1.Value.1': 'pending',
            'Filter.1.Value.2': 'available'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(len(api_response), 2)

        vpn0 = api_response[0]
        self.assertEqual(vpn0.type, 'ipsec.1')
        self.assertEqual(vpn0.customer_gateway_id, 'cgw-1234qwe9')
        self.assertEqual(vpn0.vpn_gateway_id, 'vgw-lkjh1234')
        self.assertEqual(len(vpn0.tunnels), 2)
        self.assertDictEqual(vpn0.tags, {'Name': 'VPN 1'})

        vpn1 = api_response[1]
        self.assertEqual(vpn1.state, 'pending')
        self.assertEqual(len(vpn1.static_routes), 1)
        self.assertTrue(vpn1.options.static_routes_only)
        self.assertEqual(vpn1.tunnels[0].status, 'UP')
        self.assertEqual(vpn1.tunnels[1].status, 'UP')
        self.assertDictEqual(vpn1.tags, {})
        self.assertEqual(vpn1.static_routes[0].source, 'static')
        self.assertEqual(vpn1.static_routes[0].state, 'pending')


class TestCreateVPNConnection(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateVpnConnectionResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
              <requestId>5cc7891f-1f3b-4fc4-a626-bdea8f63ff5a</requestId>
              <vpnConnection>
                <vpnConnectionId>vpn-83ad48ea</vpnConnectionId>
                <state>pending</state>
                <customerGatewayConfiguration>
                    &lt;?xml version="1.0" encoding="UTF-8"?&gt;
                </customerGatewayConfiguration>
                <customerGatewayId>cgw-b4dc3961</customerGatewayId>
                <vpnGatewayId>vgw-8db04f81</vpnGatewayId>
                <options>
                  <staticRoutesOnly>true</staticRoutesOnly>
                </options>
                <routes/>
              </vpnConnection>
            </CreateVpnConnectionResponse>
        """

    def test_create_vpn_connection(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_vpn_connection(
            'ipsec.1', 'cgw-b4dc3961', 'vgw-8db04f81', static_routes_only=True)
        self.assert_request_parameters({
            'Action': 'CreateVpnConnection',
            'Type': 'ipsec.1',
            'CustomerGatewayId': 'cgw-b4dc3961',
            'VpnGatewayId': 'vgw-8db04f81',
            'Options.StaticRoutesOnly': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertIsInstance(api_response, VpnConnection)
        self.assertEquals(api_response.id, 'vpn-83ad48ea')
        self.assertEquals(api_response.customer_gateway_id, 'cgw-b4dc3961')
        self.assertEquals(api_response.options.static_routes_only, True)


class TestDeleteVPNConnection(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteVpnConnectionResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <return>true</return>
            </DeleteVpnConnectionResponse>
        """

    def test_delete_vpn_connection(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_vpn_connection('vpn-44a8938f')
        self.assert_request_parameters({
            'Action': 'DeleteVpnConnection',
            'VpnConnectionId': 'vpn-44a8938f'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


class TestCreateVPNConnectionRoute(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateVpnConnectionRouteResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
                <requestId>4f35a1b2-c2c3-4093-b51f-abb9d7311990</requestId>
                <return>true</return>
            </CreateVpnConnectionRouteResponse>
        """

    def test_create_vpn_connection_route(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_vpn_connection_route(
            '11.12.0.0/16', 'vpn-83ad48ea')
        self.assert_request_parameters({
            'Action': 'CreateVpnConnectionRoute',
            'DestinationCidrBlock': '11.12.0.0/16',
            'VpnConnectionId': 'vpn-83ad48ea'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


class TestDeleteVPNConnectionRoute(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteVpnConnectionRouteResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
                <requestId>4f35a1b2-c2c3-4093-b51f-abb9d7311990</requestId>
                <return>true</return>
            </DeleteVpnConnectionRouteResponse>
        """

    def test_delete_vpn_connection_route(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_vpn_connection_route(
            '11.12.0.0/16', 'vpn-83ad48ea')
        self.assert_request_parameters({
            'Action': 'DeleteVpnConnectionRoute',
            'DestinationCidrBlock': '11.12.0.0/16',
            'VpnConnectionId': 'vpn-83ad48ea'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

if __name__ == '__main__':
    unittest.main()
