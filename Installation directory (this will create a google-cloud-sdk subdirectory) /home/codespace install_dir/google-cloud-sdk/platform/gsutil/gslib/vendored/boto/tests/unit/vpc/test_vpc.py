# -*- coding: UTF-8 -*-
from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.vpc import VPCConnection, VPC
from boto.ec2.securitygroup import SecurityGroup


DESCRIBE_VPCS = b'''<?xml version="1.0" encoding="UTF-8"?>
<DescribeVpcsResponse xmlns="http://ec2.amazonaws.com/doc/2013-02-01/">
    <requestId>623040d1-b51c-40bc-8080-93486f38d03d</requestId>
    <vpcSet>
        <item>
            <vpcId>vpc-12345678</vpcId>
            <state>available</state>
            <cidrBlock>172.16.0.0/16</cidrBlock>
            <dhcpOptionsId>dopt-12345678</dhcpOptionsId>
            <instanceTenancy>default</instanceTenancy>
            <isDefault>false</isDefault>
        </item>
    </vpcSet>
</DescribeVpcsResponse>'''


class TestDescribeVPCs(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return DESCRIBE_VPCS

    def test_get_vpcs(self):
        self.set_http_response(status_code=200)

        api_response = self.service_connection.get_all_vpcs()
        self.assertEqual(len(api_response), 1)

        vpc = api_response[0]
        self.assertFalse(vpc.is_default)
        self.assertEqual(vpc.instance_tenancy, 'default')


class TestCreateVpc(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateVpcResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <vpc>
                  <vpcId>vpc-1a2b3c4d</vpcId>
                  <state>pending</state>
                  <cidrBlock>10.0.0.0/16</cidrBlock>
                  <dhcpOptionsId>dopt-1a2b3c4d2</dhcpOptionsId>
                  <instanceTenancy>default</instanceTenancy>
                  <tagSet/>
               </vpc>
            </CreateVpcResponse>
        """

    def test_create_vpc(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_vpc('10.0.0.0/16', 'default')
        self.assert_request_parameters({
            'Action': 'CreateVpc',
            'InstanceTenancy': 'default',
            'CidrBlock': '10.0.0.0/16'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertIsInstance(api_response, VPC)
        self.assertEquals(api_response.id, 'vpc-1a2b3c4d')
        self.assertEquals(api_response.state, 'pending')
        self.assertEquals(api_response.cidr_block, '10.0.0.0/16')
        self.assertEquals(api_response.dhcp_options_id, 'dopt-1a2b3c4d2')
        self.assertEquals(api_response.instance_tenancy, 'default')


class TestDeleteVpc(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteVpcResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <return>true</return>
            </DeleteVpcResponse>
        """

    def test_delete_vpc(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_vpc('vpc-1a2b3c4d')
        self.assert_request_parameters({
            'Action': 'DeleteVpc',
            'VpcId': 'vpc-1a2b3c4d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


class TestModifyVpcAttribute(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <ModifyVpcAttributeResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <return>true</return>
            </ModifyVpcAttributeResponse>
        """

    def test_modify_vpc_attribute_dns_support(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.modify_vpc_attribute(
            'vpc-1a2b3c4d', enable_dns_support=True)
        self.assert_request_parameters({
            'Action': 'ModifyVpcAttribute',
            'VpcId': 'vpc-1a2b3c4d',
            'EnableDnsSupport.Value': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

    def test_modify_vpc_attribute_dns_hostnames(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.modify_vpc_attribute(
            'vpc-1a2b3c4d', enable_dns_hostnames=True)
        self.assert_request_parameters({
            'Action': 'ModifyVpcAttribute',
            'VpcId': 'vpc-1a2b3c4d',
            'EnableDnsHostnames.Value': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


class TestGetAllClassicLinkVpc(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DescribeVpcClassicLinkResponse xmlns="http://ec2.amazonaws.com/doc/2014-09-01/">
                <requestId>2484655d-d669-4950-bf55-7ba559805d36</requestId>
                <vpcSet>
                    <item>
                        <vpcId>vpc-6226ab07</vpcId>
                        <classicLinkEnabled>false</classicLinkEnabled>
                        <tagSet>
                            <item>
                                <key>Name</key>
                                <value>hello</value>[
                            </item>
                        </tagSet>
                    </item>
                    <item>
                        <vpcId>vpc-9d24f8f8</vpcId>
                        <classicLinkEnabled>true</classicLinkEnabled>
                        <tagSet/>
                    </item>
                </vpcSet>
            </DescribeVpcClassicLinkResponse>
        """

    def test_get_all_classic_link_vpcs(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_all_classic_link_vpcs()
        self.assertEqual(len(response), 2)
        vpc = response[0]
        self.assertEqual(vpc.id, 'vpc-6226ab07')
        self.assertEqual(vpc.classic_link_enabled, 'false')
        self.assertEqual(vpc.tags, {'Name': 'hello'})

    def test_get_all_classic_link_vpcs_params(self):
        self.set_http_response(status_code=200)
        self.service_connection.get_all_classic_link_vpcs(
            vpc_ids=['id1', 'id2'],
            filters={'GroupId': 'sg-9b4343fe'},
            dry_run=True,
        )
        self.assert_request_parameters({
            'Action': 'DescribeVpcClassicLink',
            'VpcId.1': 'id1',
            'VpcId.2': 'id2',
            'Filter.1.Name': 'GroupId',
            'Filter.1.Value.1': 'sg-9b4343fe',
            'DryRun': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])


class TestVpcClassicLink(AWSMockServiceTestCase):
    connection_class = VPCConnection

    def setUp(self):
        super(TestVpcClassicLink, self).setUp()
        self.vpc = VPC(self.service_connection)
        self.vpc_id = 'myid'
        self.vpc.id = self.vpc_id


class TestAttachClassicLinkVpc(TestVpcClassicLink):
    def default_body(self):
        return b"""
            <AttachClassicLinkVpcResponse xmlns="http://ec2.amazonaws.com/doc/2014-09-01/">
                <requestId>88673bdf-cd16-40bf-87a1-6132fec47257</requestId>
                <return>true</return>
            </AttachClassicLinkVpcResponse>
        """

    def test_attach_classic_link_instance_string_groups(self):
        groups = ['sg-foo', 'sg-bar']

        self.set_http_response(status_code=200)
        response = self.vpc.attach_classic_instance(
            instance_id='my_instance_id',
            groups=groups,
            dry_run=True
        )
        self.assertTrue(response)
        self.assert_request_parameters({
            'Action': 'AttachClassicLinkVpc',
            'VpcId': self.vpc_id,
            'InstanceId': 'my_instance_id',
            'SecurityGroupId.1': 'sg-foo',
            'SecurityGroupId.2': 'sg-bar',
            'DryRun': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])

    def test_attach_classic_link_instance_object_groups(self):
        sec_group_1 = SecurityGroup()
        sec_group_1.id = 'sg-foo'

        sec_group_2 = SecurityGroup()
        sec_group_2.id = 'sg-bar'

        groups = [sec_group_1, sec_group_2]

        self.set_http_response(status_code=200)
        response = self.vpc.attach_classic_instance(
            instance_id='my_instance_id',
            groups=groups,
            dry_run=True
        )
        self.assertTrue(response)
        self.assert_request_parameters({
            'Action': 'AttachClassicLinkVpc',
            'VpcId': self.vpc_id,
            'InstanceId': 'my_instance_id',
            'SecurityGroupId.1': 'sg-foo',
            'SecurityGroupId.2': 'sg-bar',
            'DryRun': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])


class TestDetachClassicLinkVpc(TestVpcClassicLink):
    def default_body(self):
        return b"""
            <DetachClassicLinkVpcResponse xmlns="http://ec2.amazonaws.com/doc/2014-09-01/">
                <requestId>5565033d-1321-4eef-b121-6aa46f152ed7</requestId>
                <return>true</return>
            </DetachClassicLinkVpcResponse>
        """

    def test_detach_classic_link_instance(self):
        self.set_http_response(status_code=200)
        response = self.vpc.detach_classic_instance(
            instance_id='my_instance_id',
            dry_run=True
        )
        self.assertTrue(response)
        self.assert_request_parameters({
            'Action': 'DetachClassicLinkVpc',
            'VpcId': self.vpc_id,
            'InstanceId': 'my_instance_id',
            'DryRun': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])


class TestEnableClassicLinkVpc(TestVpcClassicLink):
    def default_body(self):
        return b"""
            <EnableVpcClassicLinkResponse xmlns="http://ec2.amazonaws.com/doc/2014-09-01/"> 
                <requestId>4ab2b2b3-a267-4366-a070-bab853b5927d</requestId>
                <return>true</return>
            </EnableVpcClassicLinkResponse>
        """

    def test_enable_classic_link(self):
        self.set_http_response(status_code=200)
        response = self.vpc.enable_classic_link(
            dry_run=True
        )
        self.assertTrue(response)
        self.assert_request_parameters({
            'Action': 'EnableVpcClassicLink',
            'VpcId': self.vpc_id,
            'DryRun': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])


class TestDisableClassicLinkVpc(TestVpcClassicLink):
    def default_body(self):
        return b"""
            <DisableVpcClassicLinkResponse xmlns="http://ec2.amazonaws.com/doc/2014-09-01/">
                <requestId>4ab2b2b3-a267-4366-a070-bab853b5927d</requestId>
                <return>true</return>
            </DisableVpcClassicLinkResponse>
        """

    def test_enable_classic_link(self):
        self.set_http_response(status_code=200)
        response = self.vpc.disable_classic_link(
            dry_run=True
        )
        self.assertTrue(response)
        self.assert_request_parameters({
            'Action': 'DisableVpcClassicLink',
            'VpcId': self.vpc_id,
            'DryRun': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])


class TestUpdateClassicLinkVpc(TestVpcClassicLink):
    def default_body(self):
        return b"""
            <DescribeVpcClassicLinkResponse xmlns="http://ec2.amazonaws.com/doc/2014-09-01/">
                <requestId>2484655d-d669-4950-bf55-7ba559805d36</requestId>
                <vpcSet>
                    <item>
                        <vpcId>myid</vpcId>
                        <classicLinkEnabled>true</classicLinkEnabled>
                         <tagSet/>
                    </item>
                </vpcSet>
            </DescribeVpcClassicLinkResponse>
        """

    def test_vpc_update_classic_link_enabled(self):
        self.vpc.classic_link_enabled = False
        self.set_http_response(status_code=200)
        self.vpc.update_classic_link_enabled(
            dry_run=True,
            validate=True
        )
        self.assert_request_parameters({
            'Action': 'DescribeVpcClassicLink',
            'VpcId.1': self.vpc_id,
            'DryRun': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])
        self.assertEqual(self.vpc.classic_link_enabled, 'true')


if __name__ == '__main__':
    unittest.main()
