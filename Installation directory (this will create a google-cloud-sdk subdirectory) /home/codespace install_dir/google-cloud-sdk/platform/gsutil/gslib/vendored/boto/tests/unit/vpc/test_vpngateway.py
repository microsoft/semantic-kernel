# -*- coding: UTF-8 -*-
from tests.compat import OrderedDict
from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.vpc import VPCConnection, VpnGateway, Attachment


class TestDescribeVpnGateways(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DescribeVpnGatewaysResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
              <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
              <vpnGatewaySet>
                <item>
                  <vpnGatewayId>vgw-8db04f81</vpnGatewayId>
                  <state>available</state>
                  <type>ipsec.1</type>
                  <availabilityZone>us-east-1a</availabilityZone>
                  <attachments>
                    <item>
                      <vpcId>vpc-1a2b3c4d</vpcId>
                      <state>attached</state>
                    </item>
                  </attachments>
                  <tagSet/>
                </item>
              </vpnGatewaySet>
            </DescribeVpnGatewaysResponse>
        """

    def test_get_all_vpn_gateways(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.get_all_vpn_gateways(
            'vgw-8db04f81', filters=OrderedDict([('state', ['pending', 'available']),
                                     ('availability-zone', 'us-east-1a')]))
        self.assert_request_parameters({
            'Action': 'DescribeVpnGateways',
            'VpnGatewayId.1': 'vgw-8db04f81',
            'Filter.1.Name': 'state',
            'Filter.1.Value.1': 'pending',
            'Filter.1.Value.2': 'available',
            'Filter.2.Name': 'availability-zone',
            'Filter.2.Value.1': 'us-east-1a'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(len(api_response), 1)
        self.assertIsInstance(api_response[0], VpnGateway)
        self.assertEqual(api_response[0].id, 'vgw-8db04f81')


class TestCreateVpnGateway(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateVpnGatewayResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
              <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
              <vpnGateway>
                <vpnGatewayId>vgw-8db04f81</vpnGatewayId>
                <state>pending</state>
                <type>ipsec.1</type>
                <availabilityZone>us-east-1a</availabilityZone>
                <attachments/>
                <tagSet/>
              </vpnGateway>
            </CreateVpnGatewayResponse>
        """

    def test_delete_vpn_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_vpn_gateway('ipsec.1', 'us-east-1a')
        self.assert_request_parameters({
            'Action': 'CreateVpnGateway',
            'AvailabilityZone': 'us-east-1a',
            'Type': 'ipsec.1'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertIsInstance(api_response, VpnGateway)
        self.assertEquals(api_response.id, 'vgw-8db04f81')


class TestDeleteVpnGateway(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteVpnGatewayResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <return>true</return>
            </DeleteVpnGatewayResponse>
        """

    def test_delete_vpn_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_vpn_gateway('vgw-8db04f81')
        self.assert_request_parameters({
            'Action': 'DeleteVpnGateway',
            'VpnGatewayId': 'vgw-8db04f81'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(api_response, True)


class TestAttachVpnGateway(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <AttachVpnGatewayResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <attachment>
                  <vpcId>vpc-1a2b3c4d</vpcId>
                  <state>attaching</state>
               </attachment>
            </AttachVpnGatewayResponse>
        """

    def test_attach_vpn_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.attach_vpn_gateway('vgw-8db04f81', 'vpc-1a2b3c4d')
        self.assert_request_parameters({
            'Action': 'AttachVpnGateway',
            'VpnGatewayId': 'vgw-8db04f81',
            'VpcId': 'vpc-1a2b3c4d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertIsInstance(api_response, Attachment)
        self.assertEquals(api_response.vpc_id, 'vpc-1a2b3c4d')
        self.assertEquals(api_response.state, 'attaching')


class TestDetachVpnGateway(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DetachVpnGatewayResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <return>true</return>
            </DetachVpnGatewayResponse>
        """

    def test_detach_vpn_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.detach_vpn_gateway('vgw-8db04f81', 'vpc-1a2b3c4d')
        self.assert_request_parameters({
            'Action': 'DetachVpnGateway',
            'VpnGatewayId': 'vgw-8db04f81',
            'VpcId': 'vpc-1a2b3c4d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(api_response, True)


class TestDisableVgwRoutePropagation(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DisableVgwRoutePropagationResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
                <requestId>4f35a1b2-c2c3-4093-b51f-abb9d7311990</requestId>
                <return>true</return>
            </DisableVgwRoutePropagationResponse>
        """

    def test_disable_vgw_route_propagation(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.disable_vgw_route_propagation(
            'rtb-c98a35a0', 'vgw-d8e09e8a')
        self.assert_request_parameters({
            'Action': 'DisableVgwRoutePropagation',
            'GatewayId': 'vgw-d8e09e8a',
            'RouteTableId': 'rtb-c98a35a0'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(api_response, True)


class TestEnableVgwRoutePropagation(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DisableVgwRoutePropagationResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
                <requestId>4f35a1b2-c2c3-4093-b51f-abb9d7311990</requestId>
                <return>true</return>
            </DisableVgwRoutePropagationResponse>
        """

    def test_enable_vgw_route_propagation(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.enable_vgw_route_propagation(
            'rtb-c98a35a0', 'vgw-d8e09e8a')
        self.assert_request_parameters({
            'Action': 'EnableVgwRoutePropagation',
            'GatewayId': 'vgw-d8e09e8a',
            'RouteTableId': 'rtb-c98a35a0'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(api_response, True)

if __name__ == '__main__':
    unittest.main()
