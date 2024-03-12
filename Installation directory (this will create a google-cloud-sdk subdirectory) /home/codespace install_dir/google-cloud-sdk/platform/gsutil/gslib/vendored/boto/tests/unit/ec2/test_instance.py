#!/usr/bin/env python

import base64
from tests.compat import unittest, mock
from tests.unit import AWSMockServiceTestCase

from boto.ec2.connection import EC2Connection

DESCRIBE_INSTANCE_VPC = br"""<?xml version="1.0" encoding="UTF-8"?>
<DescribeInstancesResponse xmlns="http://ec2.amazonaws.com/doc/2012-10-01/">
    <requestId>c6132c74-b524-4884-87f5-0f4bde4a9760</requestId>
    <reservationSet>
        <item>
            <reservationId>r-72ef4a0a</reservationId>
            <ownerId>184906166255</ownerId>
            <groupSet/>
            <instancesSet>
                <item>
                    <instanceId>i-instance</instanceId>
                    <imageId>ami-1624987f</imageId>
                    <instanceState>
                        <code>16</code>
                        <name>running</name>
                    </instanceState>
                    <privateDnsName/>
                    <dnsName/>
                    <reason/>
                    <keyName>mykeypair</keyName>
                    <amiLaunchIndex>0</amiLaunchIndex>
                    <productCodes/>
                    <instanceType>m1.small</instanceType>
                    <launchTime>2012-12-14T23:48:37.000Z</launchTime>
                    <placement>
                        <availabilityZone>us-east-1d</availabilityZone>
                        <groupName/>
                        <tenancy>default</tenancy>
                    </placement>
                    <kernelId>aki-88aa75e1</kernelId>
                    <monitoring>
                        <state>disabled</state>
                    </monitoring>
                    <subnetId>subnet-0dc60667</subnetId>
                    <vpcId>vpc-id</vpcId>
                    <privateIpAddress>10.0.0.67</privateIpAddress>
                    <sourceDestCheck>true</sourceDestCheck>
                    <groupSet>
                        <item>
                            <groupId>sg-id</groupId>
                            <groupName>WebServerSG</groupName>
                        </item>
                    </groupSet>
                    <architecture>x86_64</architecture>
                    <rootDeviceType>ebs</rootDeviceType>
                    <rootDeviceName>/dev/sda1</rootDeviceName>
                    <blockDeviceMapping>
                        <item>
                            <deviceName>/dev/sda1</deviceName>
                            <ebs>
                                <volumeId>vol-id</volumeId>
                                <status>attached</status>
                                <attachTime>2012-12-14T23:48:43.000Z</attachTime>
                                <deleteOnTermination>true</deleteOnTermination>
                            </ebs>
                        </item>
                    </blockDeviceMapping>
                    <virtualizationType>paravirtual</virtualizationType>
                    <clientToken>foo</clientToken>
                    <tagSet>
                        <item>
                            <key>Name</key>
                            <value/>
                        </item>
                    </tagSet>
                    <hypervisor>xen</hypervisor>
                    <networkInterfaceSet>
                        <item>
                            <networkInterfaceId>eni-id</networkInterfaceId>
                            <subnetId>subnet-id</subnetId>
                            <vpcId>vpc-id</vpcId>
                            <description>Primary network interface</description>
                            <ownerId>ownerid</ownerId>
                            <status>in-use</status>
                            <privateIpAddress>10.0.0.67</privateIpAddress>
                            <sourceDestCheck>true</sourceDestCheck>
                            <groupSet>
                                <item>
                                    <groupId>sg-id</groupId>
                                    <groupName>WebServerSG</groupName>
                                </item>
                            </groupSet>
                            <attachment>
                                <attachmentId>eni-attach-id</attachmentId>
                                <deviceIndex>0</deviceIndex>
                                <status>attached</status>
                                <attachTime>2012-12-14T23:48:37.000Z</attachTime>
                                <deleteOnTermination>true</deleteOnTermination>
                            </attachment>
                            <privateIpAddressesSet>
                                <item>
                                    <privateIpAddress>10.0.0.67</privateIpAddress>
                                    <primary>true</primary>
                                </item>
                                <item>
                                    <privateIpAddress>10.0.0.54</privateIpAddress>
                                    <primary>false</primary>
                                </item>
                                <item>
                                    <privateIpAddress>10.0.0.55</privateIpAddress>
                                    <primary>false</primary>
                                </item>
                            </privateIpAddressesSet>
                        </item>
                    </networkInterfaceSet>
                    <ebsOptimized>false</ebsOptimized>
                </item>
            </instancesSet>
        </item>
    </reservationSet>
</DescribeInstancesResponse>
"""

RUN_INSTANCE_RESPONSE = br"""
<RunInstancesResponse xmlns="http://ec2.amazonaws.com/doc/2012-06-01/">
    <requestId>ad4b83c2-f606-4c39-90c6-5dcc5be823e1</requestId>
    <reservationId>r-c5cef7a7</reservationId>
    <ownerId>ownerid</ownerId>
    <groupSet>
        <item>
            <groupId>sg-id</groupId>
            <groupName>SSH</groupName>
        </item>
    </groupSet>
    <instancesSet>
        <item>
            <instanceId>i-ff0f1299</instanceId>
            <imageId>ami-ed65ba84</imageId>
            <instanceState>
                <code>0</code>
                <name>pending</name>
            </instanceState>
            <privateDnsName/>
            <dnsName/>
            <reason/>
            <keyName>awskeypair</keyName>
            <amiLaunchIndex>0</amiLaunchIndex>
            <productCodes/>
            <instanceType>t1.micro</instanceType>
            <launchTime>2012-05-30T19:21:18.000Z</launchTime>
            <placement>
                <availabilityZone>us-east-1a</availabilityZone>
                <groupName/>
                <tenancy>default</tenancy>
            </placement>
            <kernelId>aki-b6aa75df</kernelId>
            <monitoring>
                <state>disabled</state>
            </monitoring>
            <groupSet>
                <item>
                    <groupId>sg-99a710f1</groupId>
                    <groupName>SSH</groupName>
                </item>
            </groupSet>
            <stateReason>
                <code>pending</code>
                <message>pending</message>
            </stateReason>
            <architecture>i386</architecture>
            <rootDeviceType>ebs</rootDeviceType>
            <rootDeviceName>/dev/sda1</rootDeviceName>
            <blockDeviceMapping/>
            <virtualizationType>paravirtual</virtualizationType>
            <clientToken/>
            <hypervisor>xen</hypervisor>
            <networkInterfaceSet/>
            <iamInstanceProfile>
                <arn>arn:aws:iam::ownerid:instance-profile/myinstanceprofile</arn>
                <id>iamid</id>
            </iamInstanceProfile>
        </item>
    </instancesSet>
</RunInstancesResponse>
"""


class TestRunInstanceResponseParsing(unittest.TestCase):
    def testIAMInstanceProfileParsedCorrectly(self):
        ec2 = EC2Connection(aws_access_key_id='aws_access_key_id',
                            aws_secret_access_key='aws_secret_access_key')
        mock_response = mock.Mock()
        mock_response.read.return_value = RUN_INSTANCE_RESPONSE
        mock_response.status = 200
        ec2.make_request = mock.Mock(return_value=mock_response)
        reservation = ec2.run_instances(image_id='ami-12345')
        self.assertEqual(len(reservation.instances), 1)
        instance = reservation.instances[0]
        self.assertEqual(instance.image_id, 'ami-ed65ba84')
        # iamInstanceProfile has an ID element, so we want to make sure
        # that this does not map to instance.id (which should be the
        # id of the ec2 instance).
        self.assertEqual(instance.id, 'i-ff0f1299')
        self.assertDictEqual(
            instance.instance_profile,
            {'arn': ('arn:aws:iam::ownerid:'
                     'instance-profile/myinstanceprofile'),
             'id': 'iamid'})


class TestRunInstances(AWSMockServiceTestCase):
    connection_class = EC2Connection

    def default_body(self):
        # This is a dummy response
        return b"""
        <DescribeLaunchConfigurationsResponse>
        </DescribeLaunchConfigurationsResponse>
        """

    def test_run_instances_user_data(self):
        self.set_http_response(status_code=200)

        response = self.service_connection.run_instances(
            image_id='123456',
            instance_type='m1.large',
            security_groups=['group1', 'group2'],
            user_data='#!/bin/bash'
        )

        self.assert_request_parameters({
            'Action': 'RunInstances',
            'ImageId': '123456',
            'InstanceType': 'm1.large',
            'UserData': base64.b64encode(b'#!/bin/bash').decode('utf-8'),
            'MaxCount': 1,
            'MinCount': 1,
            'SecurityGroup.1': 'group1',
            'SecurityGroup.2': 'group2',
        }, ignore_params_values=[
            'Version', 'AWSAccessKeyId', 'SignatureMethod', 'SignatureVersion',
            'Timestamp'
        ])


class TestDescribeInstances(AWSMockServiceTestCase):
    connection_class = EC2Connection

    def default_body(self):
        return DESCRIBE_INSTANCE_VPC

    def test_multiple_private_ip_addresses(self):
        self.set_http_response(status_code=200)

        api_response = self.service_connection.get_all_reservations()
        self.assertEqual(len(api_response), 1)

        instances = api_response[0].instances
        self.assertEqual(len(instances), 1)

        instance = instances[0]
        self.assertEqual(len(instance.interfaces), 1)

        interface = instance.interfaces[0]
        self.assertEqual(len(interface.private_ip_addresses), 3)

        addresses = interface.private_ip_addresses
        self.assertEqual(addresses[0].private_ip_address, '10.0.0.67')
        self.assertTrue(addresses[0].primary)

        self.assertEqual(addresses[1].private_ip_address, '10.0.0.54')
        self.assertFalse(addresses[1].primary)

        self.assertEqual(addresses[2].private_ip_address, '10.0.0.55')
        self.assertFalse(addresses[2].primary)


if __name__ == '__main__':
    unittest.main()
