#!/usr/bin/env python
from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

import boto.ec2

from boto.ec2.connection import EC2Connection


class TestEC2ConnectionBase(AWSMockServiceTestCase):
    connection_class = EC2Connection

    def setUp(self):
        super(TestEC2ConnectionBase, self).setUp()
        self.ec2 = self.service_connection


class TestReservedInstanceOfferings(TestEC2ConnectionBase):

    def default_body(self):
        return b"""
            <DescribeInstanceTypesResponseType xmlns="http://ec2.amazonaws.com/doc/2013-02-01/">
                <VmTypeMessage/>
                <instanceTypeDetails>
                    <item>
                        <name>m1.small</name><cpu>1</cpu><disk>5</disk><memory>256</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>t1.micro</name><cpu>1</cpu><disk>5</disk><memory>256</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>m1.medium</name><cpu>1</cpu><disk>10</disk><memory>512</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>c1.medium</name><cpu>2</cpu><disk>10</disk><memory>512</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>m1.large</name><cpu>2</cpu><disk>10</disk><memory>512</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>m1.xlarge</name><cpu>2</cpu><disk>10</disk><memory>1024</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>c1.xlarge</name><cpu>2</cpu><disk>10</disk><memory>2048</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>m2.xlarge</name><cpu>2</cpu><disk>10</disk><memory>2048</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>m3.xlarge</name><cpu>4</cpu><disk>15</disk><memory>2048</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>m2.2xlarge</name><cpu>2</cpu><disk>30</disk><memory>4096</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>m3.2xlarge</name><cpu>4</cpu><disk>30</disk><memory>4096</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>cc1.4xlarge</name><cpu>8</cpu><disk>60</disk><memory>3072</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>m2.4xlarge</name><cpu>8</cpu><disk>60</disk><memory>4096</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>hi1.4xlarge</name><cpu>8</cpu><disk>120</disk><memory>6144</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>cc2.8xlarge</name><cpu>16</cpu><disk>120</disk><memory>6144</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>cg1.4xlarge</name><cpu>16</cpu><disk>200</disk><memory>12288</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>cr1.8xlarge</name><cpu>16</cpu><disk>240</disk><memory>16384</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                    <item>
                        <name>hs1.8xlarge</name><cpu>48</cpu><disk>24000</disk><memory>119808</memory>
                        <availability/><ephemeralDisk/>
                    </item>
                </instanceTypeDetails>
            </DescribeInstanceTypesResponseType>
        """

    def test_get_instance_types(self):
        self.set_http_response(status_code=200)
        response = self.ec2.get_all_instance_types()
        self.assertEqual(len(response), 18)
        instance_type = response[0]
        self.assertEqual(instance_type.name, 'm1.small')
        self.assertEqual(instance_type.cores, '1')
        self.assertEqual(instance_type.disk, '5')
        self.assertEqual(instance_type.memory, '256')
        instance_type = response[17]
        self.assertEqual(instance_type.name, 'hs1.8xlarge')
        self.assertEqual(instance_type.cores, '48')
        self.assertEqual(instance_type.disk, '24000')
        self.assertEqual(instance_type.memory, '119808')


if __name__ == '__main__':
    unittest.main()
