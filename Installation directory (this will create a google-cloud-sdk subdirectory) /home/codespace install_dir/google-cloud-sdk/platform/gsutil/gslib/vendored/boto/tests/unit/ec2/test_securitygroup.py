#!/usr/bin/env python

from tests.compat import unittest
from tests.unit import AWSMockServiceTestCase

from boto.ec2.connection import EC2Connection
from boto.ec2.securitygroup import SecurityGroup


DESCRIBE_SECURITY_GROUP = br"""<?xml version="1.0" encoding="UTF-8"?>
<DescribeSecurityGroupsResponse xmlns="http://ec2.amazonaws.com/doc/2013-06-15/">
   <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
   <securityGroupInfo>
      <item>
         <ownerId>111122223333</ownerId>
         <groupId>sg-1a2b3c4d</groupId>
         <groupName>WebServers</groupName>
         <groupDescription>Web Servers</groupDescription>
         <vpcId/>
         <ipPermissions>
            <item>
               <ipProtocol>tcp</ipProtocol>
               <fromPort>80</fromPort>
               <toPort>80</toPort>
               <groups/>
               <ipRanges>
                  <item>
                     <cidrIp>0.0.0.0/0</cidrIp>
                  </item>
               </ipRanges>
            </item>
         </ipPermissions>
         <ipPermissionsEgress/>
      </item>
      <item>
         <ownerId>111122223333</ownerId>
         <groupId>sg-2a2b3c4d</groupId>
         <groupName>RangedPortsBySource</groupName>
         <groupDescription>Group A</groupDescription>
         <ipPermissions>
            <item>
               <ipProtocol>tcp</ipProtocol>
               <fromPort>6000</fromPort>
               <toPort>7000</toPort>
               <groups>
                  <item>
                     <userId>111122223333</userId>
                     <groupId>sg-3a2b3c4d</groupId>
                     <groupName>Group B</groupName>
                  </item>
               </groups>
               <ipRanges/>
            </item>
         </ipPermissions>
         <ipPermissionsEgress/>
      </item>
   </securityGroupInfo>
</DescribeSecurityGroupsResponse>"""

DESCRIBE_INSTANCES = br"""<?xml version="1.0" encoding="UTF-8"?>
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
                            <groupId>sg-1a2b3c4d</groupId>
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


class TestDescribeSecurityGroups(AWSMockServiceTestCase):
    connection_class = EC2Connection

    def test_get_instances(self):
        self.set_http_response(status_code=200, body=DESCRIBE_SECURITY_GROUP)
        groups = self.service_connection.get_all_security_groups()

        self.set_http_response(status_code=200, body=DESCRIBE_INSTANCES)
        instances = groups[0].instances()

        self.assertEqual(1, len(instances))
        self.assertEqual(groups[0].id, instances[0].groups[0].id)


class SecurityGroupTest(unittest.TestCase):
    def test_add_rule(self):
        sg = SecurityGroup()
        self.assertEqual(len(sg.rules), 0)

        # Regression: ``dry_run`` was being passed (but unhandled) before.
        sg.add_rule(
            ip_protocol='http',
            from_port='80',
            to_port='8080',
            src_group_name='groupy',
            src_group_owner_id='12345',
            cidr_ip='10.0.0.1',
            src_group_group_id='54321',
            dry_run=False
        )
        self.assertEqual(len(sg.rules), 1)

    def test_remove_rule_on_empty_group(self):
        # Remove a rule from a group with no rules
        sg = SecurityGroup()

        with self.assertRaises(ValueError):
            sg.remove_rule('ip', 80, 80, None, None, None, None)
