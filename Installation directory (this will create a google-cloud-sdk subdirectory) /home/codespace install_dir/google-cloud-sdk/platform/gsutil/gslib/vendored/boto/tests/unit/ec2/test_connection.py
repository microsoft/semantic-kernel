#!/usr/bin/env python
from datetime import datetime, timedelta
from mock import MagicMock, Mock
from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

import boto.ec2

from boto.regioninfo import RegionInfo
from boto.ec2.blockdevicemapping import BlockDeviceType, BlockDeviceMapping
from boto.ec2.connection import EC2Connection
from boto.ec2.snapshot import Snapshot
from boto.ec2.reservedinstance import ReservedInstancesConfiguration
from boto.compat import http_client


class TestEC2ConnectionBase(AWSMockServiceTestCase):
    connection_class = EC2Connection

    def setUp(self):
        super(TestEC2ConnectionBase, self).setUp()
        self.ec2 = self.service_connection


class TestReservedInstanceOfferings(TestEC2ConnectionBase):

    def default_body(self):
        return b"""
            <DescribeReservedInstancesOfferingsResponse>
                <requestId>d3253568-edcf-4897-9a3d-fb28e0b3fa38</requestId>
                    <reservedInstancesOfferingsSet>
                    <item>
                        <reservedInstancesOfferingId>2964d1bf71d8</reservedInstancesOfferingId>
                        <instanceType>c1.medium</instanceType>
                        <availabilityZone>us-east-1c</availabilityZone>
                        <duration>94608000</duration>
                        <fixedPrice>775.0</fixedPrice>
                        <usagePrice>0.0</usagePrice>
                        <productDescription>product description</productDescription>
                        <instanceTenancy>default</instanceTenancy>
                        <currencyCode>USD</currencyCode>
                        <offeringType>Heavy Utilization</offeringType>
                        <recurringCharges>
                            <item>
                                <frequency>Hourly</frequency>
                                <amount>0.095</amount>
                            </item>
                        </recurringCharges>
                        <marketplace>false</marketplace>
                        <pricingDetailsSet>
                            <item>
                                <price>0.045</price>
                                <count>1</count>
                            </item>
                        </pricingDetailsSet>
                    </item>
                    <item>
                        <reservedInstancesOfferingId>2dce26e46889</reservedInstancesOfferingId>
                        <instanceType>c1.medium</instanceType>
                        <availabilityZone>us-east-1c</availabilityZone>
                        <duration>94608000</duration>
                        <fixedPrice>775.0</fixedPrice>
                        <usagePrice>0.0</usagePrice>
                        <productDescription>Linux/UNIX</productDescription>
                        <instanceTenancy>default</instanceTenancy>
                        <currencyCode>USD</currencyCode>
                        <offeringType>Heavy Utilization</offeringType>
                        <recurringCharges>
                            <item>
                                <frequency>Hourly</frequency>
                                <amount>0.035</amount>
                            </item>
                        </recurringCharges>
                        <marketplace>false</marketplace>
                        <pricingDetailsSet/>
                    </item>
                </reservedInstancesOfferingsSet>
                <nextToken>next_token</nextToken>
            </DescribeReservedInstancesOfferingsResponse>
        """

    def test_get_reserved_instance_offerings(self):
        self.set_http_response(status_code=200)
        response = self.ec2.get_all_reserved_instances_offerings()
        self.assertEqual(len(response), 2)
        instance = response[0]
        self.assertEqual(instance.id, '2964d1bf71d8')
        self.assertEqual(instance.instance_type, 'c1.medium')
        self.assertEqual(instance.availability_zone, 'us-east-1c')
        self.assertEqual(instance.duration, 94608000)
        self.assertEqual(instance.fixed_price, '775.0')
        self.assertEqual(instance.usage_price, '0.0')
        self.assertEqual(instance.description, 'product description')
        self.assertEqual(instance.instance_tenancy, 'default')
        self.assertEqual(instance.currency_code, 'USD')
        self.assertEqual(instance.offering_type, 'Heavy Utilization')
        self.assertEqual(len(instance.recurring_charges), 1)
        self.assertEqual(instance.recurring_charges[0].frequency, 'Hourly')
        self.assertEqual(instance.recurring_charges[0].amount, '0.095')
        self.assertEqual(len(instance.pricing_details), 1)
        self.assertEqual(instance.pricing_details[0].price, '0.045')
        self.assertEqual(instance.pricing_details[0].count, '1')

    def test_get_reserved_instance_offerings_params(self):
        self.set_http_response(status_code=200)
        self.ec2.get_all_reserved_instances_offerings(
            reserved_instances_offering_ids=['id1', 'id2'],
            instance_type='t1.micro',
            availability_zone='us-east-1',
            product_description='description',
            instance_tenancy='dedicated',
            offering_type='offering_type',
            include_marketplace=False,
            min_duration=100,
            max_duration=1000,
            max_instance_count=1,
            next_token='next_token',
            max_results=10
        )
        self.assert_request_parameters({
            'Action': 'DescribeReservedInstancesOfferings',
            'ReservedInstancesOfferingId.1': 'id1',
            'ReservedInstancesOfferingId.2': 'id2',
            'InstanceType': 't1.micro',
            'AvailabilityZone': 'us-east-1',
            'ProductDescription': 'description',
            'InstanceTenancy': 'dedicated',
            'OfferingType': 'offering_type',
            'IncludeMarketplace': 'false',
            'MinDuration': '100',
            'MaxDuration': '1000',
            'MaxInstanceCount': '1',
            'NextToken': 'next_token',
            'MaxResults': '10', },
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])


class TestPurchaseReservedInstanceOffering(TestEC2ConnectionBase):
    def default_body(self):
        return b"""<PurchaseReservedInstancesOffering />"""

    def test_serialized_api_args(self):
        self.set_http_response(status_code=200)
        response = self.ec2.purchase_reserved_instance_offering(
            'offering_id', 1, (100.0, 'USD'))
        self.assert_request_parameters({
            'Action': 'PurchaseReservedInstancesOffering',
            'InstanceCount': 1,
            'ReservedInstancesOfferingId': 'offering_id',
            'LimitPrice.Amount': '100.0',
            'LimitPrice.CurrencyCode': 'USD', },
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])


class TestCreateImage(TestEC2ConnectionBase):
    def default_body(self):
        return b"""<CreateImageResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
   <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
   <imageId>ami-4fa54026</imageId>
</CreateImageResponse>"""

    def test_minimal(self):
        self.set_http_response(status_code=200)
        response = self.ec2.create_image(
            'instance_id', 'name')
        self.assert_request_parameters({
            'Action': 'CreateImage',
            'InstanceId': 'instance_id',
            'Name': 'name'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_block_device_mapping(self):
        self.set_http_response(status_code=200)
        bdm = BlockDeviceMapping()
        bdm['test'] = BlockDeviceType()
        response = self.ec2.create_image(
            'instance_id', 'name', block_device_mapping=bdm)
        self.assert_request_parameters({
            'Action': 'CreateImage',
            'InstanceId': 'instance_id',
            'Name': 'name',
            'BlockDeviceMapping.1.DeviceName': 'test',
            'BlockDeviceMapping.1.Ebs.DeleteOnTermination': 'false'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])


class TestCancelReservedInstancesListing(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
            <CancelReservedInstancesListingResponse>
                <requestId>request_id</requestId>
                <reservedInstancesListingsSet>
                    <item>
                        <reservedInstancesListingId>listing_id</reservedInstancesListingId>
                        <reservedInstancesId>instance_id</reservedInstancesId>
                        <createDate>2012-07-12T16:55:28.000Z</createDate>
                        <updateDate>2012-07-12T16:55:28.000Z</updateDate>
                        <status>cancelled</status>
                        <statusMessage>CANCELLED</statusMessage>
                        <instanceCounts>
                            <item>
                                <state>Available</state>
                                <instanceCount>0</instanceCount>
                            </item>
                            <item>
                                <state>Sold</state>
                                <instanceCount>0</instanceCount>
                            </item>
                            <item>
                                <state>Cancelled</state>
                                <instanceCount>1</instanceCount>
                            </item>
                            <item>
                                <state>Pending</state>
                                <instanceCount>0</instanceCount>
                            </item>
                        </instanceCounts>
                        <priceSchedules>
                            <item>
                                <term>5</term>
                                <price>166.64</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>4</term>
                                <price>133.32</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>3</term>
                                <price>99.99</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>2</term>
                                <price>66.66</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>1</term>
                                <price>33.33</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                        </priceSchedules>
                        <tagSet/>
                        <clientToken>XqJIt1342112125076</clientToken>
                    </item>
                </reservedInstancesListingsSet>
            </CancelReservedInstancesListingResponse>
        """

    def test_reserved_instances_listing(self):
        self.set_http_response(status_code=200)
        response = self.ec2.cancel_reserved_instances_listing()
        self.assertEqual(len(response), 1)
        cancellation = response[0]
        self.assertEqual(cancellation.status, 'cancelled')
        self.assertEqual(cancellation.status_message, 'CANCELLED')
        self.assertEqual(len(cancellation.instance_counts), 4)
        first = cancellation.instance_counts[0]
        self.assertEqual(first.state, 'Available')
        self.assertEqual(first.instance_count, 0)
        self.assertEqual(len(cancellation.price_schedules), 5)
        schedule = cancellation.price_schedules[0]
        self.assertEqual(schedule.term, 5)
        self.assertEqual(schedule.price, '166.64')
        self.assertEqual(schedule.currency_code, 'USD')
        self.assertEqual(schedule.active, False)


class TestCreateReservedInstancesListing(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
            <CreateReservedInstancesListingResponse>
                <requestId>request_id</requestId>
                <reservedInstancesListingsSet>
                    <item>
                        <reservedInstancesListingId>listing_id</reservedInstancesListingId>
                        <reservedInstancesId>instance_id</reservedInstancesId>
                        <createDate>2012-07-17T17:11:09.449Z</createDate>
                        <updateDate>2012-07-17T17:11:09.468Z</updateDate>
                        <status>active</status>
                        <statusMessage>ACTIVE</statusMessage>
                        <instanceCounts>
                            <item>
                                <state>Available</state>
                                <instanceCount>1</instanceCount>
                            </item>
                            <item>
                                <state>Sold</state>
                                <instanceCount>0</instanceCount>
                            </item>
                            <item>
                                <state>Cancelled</state>
                                <instanceCount>0</instanceCount>
                            </item>
                            <item>
                                <state>Pending</state>
                                <instanceCount>0</instanceCount>
                            </item>
                        </instanceCounts>
                        <priceSchedules>
                            <item>
                                <term>11</term>
                                <price>2.5</price>
                                <currencyCode>USD</currencyCode>
                                <active>true</active>
                            </item>
                            <item>
                                <term>10</term>
                                <price>2.5</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>9</term>
                                <price>2.5</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>8</term>
                                <price>2.0</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>7</term>
                                <price>2.0</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>6</term>
                                <price>2.0</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>5</term>
                                <price>1.5</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>4</term>
                                <price>1.5</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>3</term>
                                <price>0.7</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>2</term>
                                <price>0.7</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                            <item>
                                <term>1</term>
                                <price>0.1</price>
                                <currencyCode>USD</currencyCode>
                                <active>false</active>
                            </item>
                        </priceSchedules>
                        <tagSet/>
                        <clientToken>myIdempToken1</clientToken>
                    </item>
                </reservedInstancesListingsSet>
            </CreateReservedInstancesListingResponse>
        """

    def test_create_reserved_instances_listing(self):
        self.set_http_response(status_code=200)
        response = self.ec2.create_reserved_instances_listing(
            'instance_id', 1, [('2.5', 11), ('2.0', 8)], 'client_token')
        self.assertEqual(len(response), 1)
        cancellation = response[0]
        self.assertEqual(cancellation.status, 'active')
        self.assertEqual(cancellation.status_message, 'ACTIVE')
        self.assertEqual(len(cancellation.instance_counts), 4)
        first = cancellation.instance_counts[0]
        self.assertEqual(first.state, 'Available')
        self.assertEqual(first.instance_count, 1)
        self.assertEqual(len(cancellation.price_schedules), 11)
        schedule = cancellation.price_schedules[0]
        self.assertEqual(schedule.term, 11)
        self.assertEqual(schedule.price, '2.5')
        self.assertEqual(schedule.currency_code, 'USD')
        self.assertEqual(schedule.active, True)

        self.assert_request_parameters({
            'Action': 'CreateReservedInstancesListing',
            'ReservedInstancesId': 'instance_id',
            'InstanceCount': '1',
            'ClientToken': 'client_token',
            'PriceSchedules.0.Price': '2.5',
            'PriceSchedules.0.Term': '11',
            'PriceSchedules.1.Price': '2.0',
            'PriceSchedules.1.Term': '8', },
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])


class TestDescribeSpotInstanceRequests(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
        <DescribeSpotInstanceRequestsResponse>
            <requestId>requestid</requestId>
            <spotInstanceRequestSet>
                <item>
                    <spotInstanceRequestId>sir-id</spotInstanceRequestId>
                    <spotPrice>0.003000</spotPrice>
                    <type>one-time</type>
                    <state>active</state>
                    <status>
                        <code>fulfilled</code>
                        <updateTime>2012-10-19T18:09:26.000Z</updateTime>
                        <message>Your Spot request is fulfilled.</message>
                    </status>
                    <launchGroup>mylaunchgroup</launchGroup>
                    <launchSpecification>
                        <imageId>ami-id</imageId>
                        <keyName>mykeypair</keyName>
                        <groupSet>
                            <item>
                                <groupId>sg-id</groupId>
                                <groupName>groupname</groupName>
                            </item>
                        </groupSet>
                        <instanceType>t1.micro</instanceType>
                        <monitoring>
                            <enabled>false</enabled>
                        </monitoring>
                    </launchSpecification>
                    <instanceId>i-id</instanceId>
                    <createTime>2012-10-19T18:07:05.000Z</createTime>
                    <productDescription>Linux/UNIX</productDescription>
                    <launchedAvailabilityZone>us-east-1d</launchedAvailabilityZone>
                </item>
            </spotInstanceRequestSet>
        </DescribeSpotInstanceRequestsResponse>
        """

    def test_describe_spot_instance_requets(self):
        self.set_http_response(status_code=200)
        response = self.ec2.get_all_spot_instance_requests()
        self.assertEqual(len(response), 1)
        spotrequest = response[0]
        self.assertEqual(spotrequest.id, 'sir-id')
        self.assertEqual(spotrequest.price, 0.003)
        self.assertEqual(spotrequest.type, 'one-time')
        self.assertEqual(spotrequest.state, 'active')
        self.assertEqual(spotrequest.fault, None)
        self.assertEqual(spotrequest.valid_from, None)
        self.assertEqual(spotrequest.valid_until, None)
        self.assertEqual(spotrequest.launch_group, 'mylaunchgroup')
        self.assertEqual(spotrequest.launched_availability_zone, 'us-east-1d')
        self.assertEqual(spotrequest.product_description, 'Linux/UNIX')
        self.assertEqual(spotrequest.availability_zone_group, None)
        self.assertEqual(spotrequest.create_time,
                         '2012-10-19T18:07:05.000Z')
        self.assertEqual(spotrequest.instance_id, 'i-id')
        launch_spec = spotrequest.launch_specification
        self.assertEqual(launch_spec.key_name, 'mykeypair')
        self.assertEqual(launch_spec.instance_type, 't1.micro')
        self.assertEqual(launch_spec.image_id, 'ami-id')
        self.assertEqual(launch_spec.placement, None)
        self.assertEqual(launch_spec.kernel, None)
        self.assertEqual(launch_spec.ramdisk, None)
        self.assertEqual(launch_spec.monitored, False)
        self.assertEqual(launch_spec.subnet_id, None)
        self.assertEqual(launch_spec.block_device_mapping, None)
        self.assertEqual(launch_spec.instance_profile, None)
        self.assertEqual(launch_spec.ebs_optimized, False)
        status = spotrequest.status
        self.assertEqual(status.code, 'fulfilled')
        self.assertEqual(status.update_time, '2012-10-19T18:09:26.000Z')
        self.assertEqual(status.message, 'Your Spot request is fulfilled.')


class TestCopySnapshot(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
        <CopySnapshotResponse xmlns="http://ec2.amazonaws.com/doc/2012-12-01/">
            <requestId>request_id</requestId>
            <snapshotId>snap-copied-id</snapshotId>
        </CopySnapshotResponse>
        """

    def test_copy_snapshot(self):
        self.set_http_response(status_code=200)
        snapshot_id = self.ec2.copy_snapshot('us-west-2', 'snap-id',
                                             'description')
        self.assertEqual(snapshot_id, 'snap-copied-id')

        self.assert_request_parameters({
            'Action': 'CopySnapshot',
            'Description': 'description',
            'SourceRegion': 'us-west-2',
            'SourceSnapshotId': 'snap-id'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])


class TestCopyImage(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
        <CopyImageResponse xmlns="http://ec2.amazonaws.com/doc/2013-07-15/">
           <requestId>request_id</requestId>
           <imageId>ami-copied-id</imageId>
        </CopyImageResponse>
        """

    def test_copy_image_required_params(self):
        self.set_http_response(status_code=200)
        copied_ami = self.ec2.copy_image('us-west-2', 'ami-id')
        self.assertEqual(copied_ami.image_id, 'ami-copied-id')
        self.assert_request_parameters({
            'Action': 'CopyImage',
            'SourceRegion': 'us-west-2',
            'SourceImageId': 'ami-id'
        }, ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_copy_image_name_and_description(self):
        self.set_http_response(status_code=200)
        copied_ami = self.ec2.copy_image('us-west-2', 'ami-id', 'name', 'description')
        self.assertEqual(copied_ami.image_id, 'ami-copied-id')
        self.assert_request_parameters({
            'Action': 'CopyImage',
            'SourceRegion': 'us-west-2',
            'SourceImageId': 'ami-id',
            'Name': 'name',
            'Description': 'description'
        }, ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_copy_image_client_token(self):
        self.set_http_response(status_code=200)
        copied_ami = self.ec2.copy_image('us-west-2', 'ami-id', client_token='client-token')
        self.assertEqual(copied_ami.image_id, 'ami-copied-id')
        self.assert_request_parameters({
            'Action': 'CopyImage',
            'SourceRegion': 'us-west-2',
            'SourceImageId': 'ami-id',
            'ClientToken': 'client-token'
        }, ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_copy_image_encrypted(self):
        self.set_http_response(status_code=200)
        copied_ami = self.ec2.copy_image('us-west-2', 'ami-id', encrypted=True)
        self.assertEqual(copied_ami.image_id, 'ami-copied-id')

        self.assert_request_parameters({
            'Action': 'CopyImage',
            'SourceRegion': 'us-west-2',
            'SourceImageId': 'ami-id',
            'Encrypted': 'true'
        }, ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_copy_image_not_encrypted(self):
        self.set_http_response(status_code=200)
        copied_ami = self.ec2.copy_image('us-west-2', 'ami-id', encrypted=False)
        self.assertEqual(copied_ami.image_id, 'ami-copied-id')

        self.assert_request_parameters({
            'Action': 'CopyImage',
            'SourceRegion': 'us-west-2',
            'SourceImageId': 'ami-id',
            'Encrypted': 'false'
        }, ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_copy_image_encrypted_with_kms_key(self):
        self.set_http_response(status_code=200)
        copied_ami = self.ec2.copy_image('us-west-2', 'ami-id', encrypted=False, kms_key_id='kms-key')
        self.assertEqual(copied_ami.image_id, 'ami-copied-id')

        self.assert_request_parameters({
            'Action': 'CopyImage',
            'SourceRegion': 'us-west-2',
            'SourceImageId': 'ami-id',
            'Encrypted': 'false',
            'KmsKeyId': 'kms-key'
        }, ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])


class TestAccountAttributes(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
        <DescribeAccountAttributesResponse xmlns="http://ec2.amazonaws.com/doc/2012-12-01/">
            <requestId>6d042e8a-4bc3-43e8-8265-3cbc54753f14</requestId>
            <accountAttributeSet>
                <item>
                    <attributeName>vpc-max-security-groups-per-interface</attributeName>
                    <attributeValueSet>
                        <item>
                            <attributeValue>5</attributeValue>
                        </item>
                    </attributeValueSet>
                </item>
                <item>
                    <attributeName>max-instances</attributeName>
                    <attributeValueSet>
                        <item>
                            <attributeValue>50</attributeValue>
                        </item>
                    </attributeValueSet>
                </item>
                <item>
                    <attributeName>supported-platforms</attributeName>
                    <attributeValueSet>
                        <item>
                            <attributeValue>EC2</attributeValue>
                        </item>
                        <item>
                            <attributeValue>VPC</attributeValue>
                        </item>
                    </attributeValueSet>
                </item>
                <item>
                    <attributeName>default-vpc</attributeName>
                    <attributeValueSet>
                        <item>
                            <attributeValue>none</attributeValue>
                        </item>
                    </attributeValueSet>
                </item>
            </accountAttributeSet>
        </DescribeAccountAttributesResponse>
        """

    def test_describe_account_attributes(self):
        self.set_http_response(status_code=200)
        parsed = self.ec2.describe_account_attributes()
        self.assertEqual(len(parsed), 4)
        self.assertEqual(parsed[0].attribute_name,
                         'vpc-max-security-groups-per-interface')
        self.assertEqual(parsed[0].attribute_values,
                         ['5'])
        self.assertEqual(parsed[-1].attribute_name,
                         'default-vpc')
        self.assertEqual(parsed[-1].attribute_values,
                         ['none'])


class TestDescribeVPCAttribute(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
        <DescribeVpcAttributeResponse xmlns="http://ec2.amazonaws.com/doc/2013-02-01/">
            <requestId>request_id</requestId>
            <vpcId>vpc-id</vpcId>
            <enableDnsHostnames>
                <value>false</value>
            </enableDnsHostnames>
        </DescribeVpcAttributeResponse>
        """

    def test_describe_vpc_attribute(self):
        self.set_http_response(status_code=200)
        parsed = self.ec2.describe_vpc_attribute('vpc-id',
                                                 'enableDnsHostnames')
        self.assertEqual(parsed.vpc_id, 'vpc-id')
        self.assertFalse(parsed.enable_dns_hostnames)
        self.assert_request_parameters({
            'Action': 'DescribeVpcAttribute',
            'VpcId': 'vpc-id',
            'Attribute': 'enableDnsHostnames', },
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])


class TestGetAllNetworkInterfaces(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
<DescribeNetworkInterfacesResponse xmlns="http://ec2.amazonaws.com/\
    doc/2013-06-15/">
    <requestId>fc45294c-006b-457b-bab9-012f5b3b0e40</requestId>
     <networkInterfaceSet>
       <item>
         <networkInterfaceId>eni-0f62d866</networkInterfaceId>
         <subnetId>subnet-c53c87ac</subnetId>
         <vpcId>vpc-cc3c87a5</vpcId>
         <availabilityZone>ap-southeast-1b</availabilityZone>
         <description/>
         <ownerId>053230519467</ownerId>
         <requesterManaged>false</requesterManaged>
         <status>in-use</status>
         <macAddress>02:81:60:cb:27:37</macAddress>
         <privateIpAddress>10.0.0.146</privateIpAddress>
         <sourceDestCheck>true</sourceDestCheck>
         <groupSet>
           <item>
             <groupId>sg-3f4b5653</groupId>
             <groupName>default</groupName>
           </item>
         </groupSet>
         <attachment>
           <attachmentId>eni-attach-6537fc0c</attachmentId>
           <instanceId>i-22197876</instanceId>
           <instanceOwnerId>053230519467</instanceOwnerId>
           <deviceIndex>5</deviceIndex>
           <status>attached</status>
           <attachTime>2012-07-01T21:45:27.000Z</attachTime>
           <deleteOnTermination>true</deleteOnTermination>
         </attachment>
         <tagSet/>
         <privateIpAddressesSet>
           <item>
             <privateIpAddress>10.0.0.146</privateIpAddress>
             <primary>true</primary>
           </item>
           <item>
             <privateIpAddress>10.0.0.148</privateIpAddress>
             <primary>false</primary>
           </item>
           <item>
             <privateIpAddress>10.0.0.150</privateIpAddress>
             <primary>false</primary>
           </item>
         </privateIpAddressesSet>
       </item>
    </networkInterfaceSet>
</DescribeNetworkInterfacesResponse>"""

    def test_get_all_network_interfaces(self):
        self.set_http_response(status_code=200)
        result = self.ec2.get_all_network_interfaces(network_interface_ids=['eni-0f62d866'])
        self.assert_request_parameters({
            'Action': 'DescribeNetworkInterfaces',
            'NetworkInterfaceId.1': 'eni-0f62d866'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 'eni-0f62d866')

    def test_attachment_has_device_index(self):
        self.set_http_response(status_code=200)
        parsed = self.ec2.get_all_network_interfaces()

        self.assertEqual(5, parsed[0].attachment.device_index)


class TestGetAllImages(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
<DescribeImagesResponse xmlns="http://ec2.amazonaws.com/doc/2013-02-01/">
    <requestId>e32375e8-4ac3-4099-a8bf-3ec902b9023e</requestId>
    <imagesSet>
        <item>
            <imageId>ami-abcd1234</imageId>
            <imageLocation>111111111111/windows2008r2-hvm-i386-20130702</imageLocation>
            <imageState>available</imageState>
            <imageOwnerId>111111111111</imageOwnerId>
            <isPublic>false</isPublic>
            <architecture>i386</architecture>
            <imageType>machine</imageType>
            <platform>windows</platform>
            <viridianEnabled>true</viridianEnabled>
            <name>Windows Test</name>
            <description>Windows Test Description</description>
            <billingProducts>
                        <item>
                                <billingProduct>bp-6ba54002</billingProduct>
                        </item>
                        </billingProducts>
            <rootDeviceType>ebs</rootDeviceType>
            <rootDeviceName>/dev/sda1</rootDeviceName>
            <blockDeviceMapping>
                <item>
                    <deviceName>/dev/sda1</deviceName>
                    <ebs>
                        <snapshotId>snap-abcd1234</snapshotId>
                        <volumeSize>30</volumeSize>
                        <deleteOnTermination>true</deleteOnTermination>
                        <volumeType>standard</volumeType>
                    </ebs>
                </item>
                <item>
                    <deviceName>xvdb</deviceName>
                    <virtualName>ephemeral0</virtualName>
                </item>
                <item>
                    <deviceName>xvdc</deviceName>
                    <virtualName>ephemeral1</virtualName>
                </item>
                <item>
                    <deviceName>xvdd</deviceName>
                    <virtualName>ephemeral2</virtualName>
                </item>
                <item>
                    <deviceName>xvde</deviceName>
                    <virtualName>ephemeral3</virtualName>
                </item>
            </blockDeviceMapping>
            <virtualizationType>hvm</virtualizationType>
            <hypervisor>xen</hypervisor>
        </item>
    </imagesSet>
</DescribeImagesResponse>"""

    def test_get_all_images(self):
        self.set_http_response(status_code=200)
        parsed = self.ec2.get_all_images()
        self.assertEquals(1, len(parsed))
        self.assertEquals("ami-abcd1234", parsed[0].id)
        self.assertEquals("111111111111/windows2008r2-hvm-i386-20130702", parsed[0].location)
        self.assertEquals("available", parsed[0].state)
        self.assertEquals("111111111111", parsed[0].ownerId)
        self.assertEquals("111111111111", parsed[0].owner_id)
        self.assertEquals(False, parsed[0].is_public)
        self.assertEquals("i386", parsed[0].architecture)
        self.assertEquals("machine", parsed[0].type)
        self.assertEquals(None, parsed[0].kernel_id)
        self.assertEquals(None, parsed[0].ramdisk_id)
        self.assertEquals(None, parsed[0].owner_alias)
        self.assertEquals("windows", parsed[0].platform)
        self.assertEquals("Windows Test", parsed[0].name)
        self.assertEquals("Windows Test Description", parsed[0].description)
        self.assertEquals("ebs", parsed[0].root_device_type)
        self.assertEquals("/dev/sda1", parsed[0].root_device_name)
        self.assertEquals("hvm", parsed[0].virtualization_type)
        self.assertEquals("xen", parsed[0].hypervisor)
        self.assertEquals(None, parsed[0].instance_lifecycle)

        # 1 billing product parsed into a list
        self.assertEquals(1, len(parsed[0].billing_products))
        self.assertEquals("bp-6ba54002", parsed[0].billing_products[0])

        # Just verify length, there is already a block_device_mapping test
        self.assertEquals(5, len(parsed[0].block_device_mapping))

        # TODO: No tests for product codes?


class TestModifyInterfaceAttribute(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
<ModifyNetworkInterfaceAttributeResponse \
    xmlns="http://ec2.amazonaws.com/doc/2013-06-15/">
    <requestId>657a4623-5620-4232-b03b-427e852d71cf</requestId>
    <return>true</return>
</ModifyNetworkInterfaceAttributeResponse>
"""

    def test_modify_description(self):
        self.set_http_response(status_code=200)
        self.ec2.modify_network_interface_attribute('id', 'description', 'foo')

        self.assert_request_parameters({
            'Action': 'ModifyNetworkInterfaceAttribute',
            'NetworkInterfaceId': 'id',
            'Description.Value': 'foo'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_modify_source_dest_check_bool(self):
        self.set_http_response(status_code=200)
        self.ec2.modify_network_interface_attribute('id', 'sourceDestCheck',
                                                    True)

        self.assert_request_parameters({
            'Action': 'ModifyNetworkInterfaceAttribute',
            'NetworkInterfaceId': 'id',
            'SourceDestCheck.Value': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_modify_source_dest_check_str(self):
        self.set_http_response(status_code=200)
        self.ec2.modify_network_interface_attribute('id', 'sourceDestCheck',
                                                    'true')

        self.assert_request_parameters({
            'Action': 'ModifyNetworkInterfaceAttribute',
            'NetworkInterfaceId': 'id',
            'SourceDestCheck.Value': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_modify_source_dest_check_invalid(self):
        self.set_http_response(status_code=200)

        with self.assertRaises(ValueError):
            self.ec2.modify_network_interface_attribute('id',
                                                        'sourceDestCheck',
                                                        123)

    def test_modify_delete_on_termination_str(self):
        self.set_http_response(status_code=200)
        self.ec2.modify_network_interface_attribute('id',
                                                    'deleteOnTermination',
                                                    True, attachment_id='bar')

        self.assert_request_parameters({
            'Action': 'ModifyNetworkInterfaceAttribute',
            'NetworkInterfaceId': 'id',
            'Attachment.AttachmentId': 'bar',
            'Attachment.DeleteOnTermination': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_modify_delete_on_termination_bool(self):
        self.set_http_response(status_code=200)
        self.ec2.modify_network_interface_attribute('id',
                                                    'deleteOnTermination',
                                                    'false',
                                                    attachment_id='bar')

        self.assert_request_parameters({
            'Action': 'ModifyNetworkInterfaceAttribute',
            'NetworkInterfaceId': 'id',
            'Attachment.AttachmentId': 'bar',
            'Attachment.DeleteOnTermination': 'false'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_modify_delete_on_termination_invalid(self):
        self.set_http_response(status_code=200)

        with self.assertRaises(ValueError):
            self.ec2.modify_network_interface_attribute('id',
                                                        'deleteOnTermination',
                                                        123,
                                                        attachment_id='bar')

    def test_modify_group_set_list(self):
        self.set_http_response(status_code=200)
        self.ec2.modify_network_interface_attribute('id', 'groupSet',
                                                    ['sg-1', 'sg-2'])

        self.assert_request_parameters({
            'Action': 'ModifyNetworkInterfaceAttribute',
            'NetworkInterfaceId': 'id',
            'SecurityGroupId.1': 'sg-1',
            'SecurityGroupId.2': 'sg-2'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

    def test_modify_group_set_invalid(self):
        self.set_http_response(status_code=200)

        with self.assertRaisesRegexp(TypeError, 'iterable'):
            self.ec2.modify_network_interface_attribute('id', 'groupSet',
                                                        False)

    def test_modify_attr_invalid(self):
        self.set_http_response(status_code=200)

        with self.assertRaisesRegexp(ValueError, 'Unknown attribute'):
            self.ec2.modify_network_interface_attribute('id', 'invalid', 0)


class TestConnectToRegion(unittest.TestCase):
    def setUp(self):
        self.https_connection = Mock(spec=http_client.HTTPSConnection)
        self.https_connection_factory = (
            Mock(return_value=self.https_connection), ())

    def test_aws_region(self):
        region = list(boto.ec2.RegionData.keys())[0]
        self.ec2 = boto.ec2.connect_to_region(
            region,
            https_connection_factory=self.https_connection_factory,
            aws_access_key_id='aws_access_key_id',
            aws_secret_access_key='aws_secret_access_key'
        )
        self.assertEqual(boto.ec2.RegionData[region], self.ec2.host)

    def test_non_aws_region(self):
        self.ec2 = boto.ec2.connect_to_region(
            'foo',
            https_connection_factory=self.https_connection_factory,
            aws_access_key_id='aws_access_key_id',
            aws_secret_access_key='aws_secret_access_key',
            region=RegionInfo(name='foo', endpoint='https://foo.com/bar')
        )
        self.assertEqual('https://foo.com/bar', self.ec2.host)

    def test_missing_region(self):
        self.ec2 = boto.ec2.connect_to_region(
            'foo',
            https_connection_factory=self.https_connection_factory,
            aws_access_key_id='aws_access_key_id',
            aws_secret_access_key='aws_secret_access_key'
        )
        self.assertEqual(None, self.ec2)


class TestTrimSnapshots(TestEC2ConnectionBase):
    """
    Test snapshot trimming functionality by ensuring that expected calls
    are made when given a known set of volume snapshots.
    """
    def _get_snapshots(self):
        """
        Generate a list of fake snapshots with names and dates.
        """
        snaps = []

        # Generate some dates offset by days, weeks, months.
        # This is to validate the various types of snapshot logic handled by
        # ``trim_snapshots``.
        now = datetime.now()
        dates = [
            now,
            now - timedelta(days=1),
            now - timedelta(days=2),
            now - timedelta(days=7),
            now - timedelta(days=14),
            # We want to simulate 30/60/90-day snapshots, but February is
            # short (only 28 days), so we decrease the delta by 2 days apiece.
            # This prevents the ``delete_snapshot`` code below from being
            # called, since they don't fall outside the allowed timeframes
            # for the snapshots.
            datetime(now.year, now.month, 1) - timedelta(days=28),
            datetime(now.year, now.month, 1) - timedelta(days=58),
            datetime(now.year, now.month, 1) - timedelta(days=88)
        ]

        for date in dates:
            # Create a fake snapshot for each date
            snap = Snapshot(self.ec2)
            snap.tags['Name'] = 'foo'
            # Times are expected to be ISO8601 strings
            snap.start_time = date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            snaps.append(snap)

        return snaps

    def test_trim_defaults(self):
        """
        Test trimming snapshots with the default arguments, which should
        keep all monthly backups forever. The result of this test should
        be that nothing is deleted.
        """
        # Setup mocks
        orig = {
            'get_all_snapshots': self.ec2.get_all_snapshots,
            'delete_snapshot': self.ec2.delete_snapshot
        }

        snaps = self._get_snapshots()

        self.ec2.get_all_snapshots = MagicMock(return_value=snaps)
        self.ec2.delete_snapshot = MagicMock()

        # Call the tested method
        self.ec2.trim_snapshots()

        # Assertions
        self.assertEqual(True, self.ec2.get_all_snapshots.called)
        self.assertEqual(False, self.ec2.delete_snapshot.called)

        # Restore
        self.ec2.get_all_snapshots = orig['get_all_snapshots']
        self.ec2.delete_snapshot = orig['delete_snapshot']

    def test_trim_months(self):
        """
        Test trimming monthly snapshots and ensure that older months
        get deleted properly. The result of this test should be that
        the two oldest snapshots get deleted.
        """
        # Setup mocks
        orig = {
            'get_all_snapshots': self.ec2.get_all_snapshots,
            'delete_snapshot': self.ec2.delete_snapshot
        }

        snaps = self._get_snapshots()

        self.ec2.get_all_snapshots = MagicMock(return_value=snaps)
        self.ec2.delete_snapshot = MagicMock()

        # Call the tested method
        self.ec2.trim_snapshots(monthly_backups=1)

        # Assertions
        self.assertEqual(True, self.ec2.get_all_snapshots.called)
        self.assertEqual(2, self.ec2.delete_snapshot.call_count)

        # Restore
        self.ec2.get_all_snapshots = orig['get_all_snapshots']
        self.ec2.delete_snapshot = orig['delete_snapshot']


class TestModifyReservedInstances(TestEC2ConnectionBase):
    def default_body(self):
        return b"""<ModifyReservedInstancesResponse xmlns='http://ec2.amazonaws.com/doc/2013-08-15/'>
    <requestId>bef729b6-0731-4489-8881-2258746ae163</requestId>
    <reservedInstancesModificationId>rimod-3aae219d-3d63-47a9-a7e9-e764example</reservedInstancesModificationId>
</ModifyReservedInstancesResponse>"""

    def test_serialized_api_args(self):
        self.set_http_response(status_code=200)
        response = self.ec2.modify_reserved_instances(
            'a-token-goes-here',
            reserved_instance_ids=[
                '2567o137-8a55-48d6-82fb-7258506bb497',
            ],
            target_configurations=[
                ReservedInstancesConfiguration(
                    availability_zone='us-west-2c',
                    platform='EC2-VPC',
                    instance_count=3,
                    instance_type='c3.large'
                ),
            ]
        )
        self.assert_request_parameters({
            'Action': 'ModifyReservedInstances',
            'ClientToken': 'a-token-goes-here',
            'ReservedInstancesConfigurationSetItemType.0.AvailabilityZone': 'us-west-2c',
            'ReservedInstancesConfigurationSetItemType.0.InstanceCount': 3,
            'ReservedInstancesConfigurationSetItemType.0.Platform': 'EC2-VPC',
            'ReservedInstancesConfigurationSetItemType.0.InstanceType': 'c3.large',
            'ReservedInstancesId.1': '2567o137-8a55-48d6-82fb-7258506bb497'
        }, ignore_params_values=[
            'AWSAccessKeyId', 'SignatureMethod',
            'SignatureVersion', 'Timestamp',
            'Version'
        ])

        self.assertEqual(response, 'rimod-3aae219d-3d63-47a9-a7e9-e764example')

    def test_none_token(self):
        """Ensures that if the token is set to None, nothing is serialized."""
        self.set_http_response(status_code=200)
        response = self.ec2.modify_reserved_instances(
            None,
            reserved_instance_ids=[
                '2567o137-8a55-48d6-82fb-7258506bb497',
            ],
            target_configurations=[
                ReservedInstancesConfiguration(
                    availability_zone='us-west-2c',
                    platform='EC2-VPC',
                    instance_count=3,
                    instance_type='c3.large'
                ),
            ]
        )
        self.assert_request_parameters({
            'Action': 'ModifyReservedInstances',
            'ReservedInstancesConfigurationSetItemType.0.AvailabilityZone': 'us-west-2c',
            'ReservedInstancesConfigurationSetItemType.0.InstanceCount': 3,
            'ReservedInstancesConfigurationSetItemType.0.Platform': 'EC2-VPC',
            'ReservedInstancesConfigurationSetItemType.0.InstanceType': 'c3.large',
            'ReservedInstancesId.1': '2567o137-8a55-48d6-82fb-7258506bb497'
        }, ignore_params_values=[
            'AWSAccessKeyId', 'SignatureMethod',
            'SignatureVersion', 'Timestamp',
            'Version'
        ])

        self.assertEqual(response, 'rimod-3aae219d-3d63-47a9-a7e9-e764example')


class TestDescribeReservedInstancesModifications(TestEC2ConnectionBase):
    def default_body(self):
        return b"""<DescribeReservedInstancesModificationsResponse xmlns='http://ec2.amazonaws.com/doc/2013-08-15/'>
    <requestId>eb4a6e3c-3689-445c-b536-19e38df35898</requestId>
    <reservedInstancesModificationsSet>
        <item>
            <reservedInstancesModificationId>rimod-49b9433e-fdc7-464a-a6e5-9dabcexample</reservedInstancesModificationId>
            <reservedInstancesSet>
                <item>
                    <reservedInstancesId>2567o137-8a55-48d6-82fb-7258506bb497</reservedInstancesId>
                </item>
            </reservedInstancesSet>
            <modificationResultSet>
                <item>
                    <reservedInstancesId>9d5cb137-5d65-4479-b4ac-8c337example</reservedInstancesId>
                    <targetConfiguration>
                        <availabilityZone>us-east-1b</availabilityZone>
                        <platform>EC2-VPC</platform>
                        <instanceCount>1</instanceCount>
                    </targetConfiguration>
                </item>
            </modificationResultSet>
            <createDate>2013-09-02T21:20:19.637Z</createDate>
            <updateDate>2013-09-02T21:38:24.143Z</updateDate>
            <effectiveDate>2013-09-02T21:00:00.000Z</effectiveDate>
            <status>fulfilled</status>
            <clientToken>token-f5b56c05-09b0-4d17-8d8c-c75d8a67b806</clientToken>
        </item>
    </reservedInstancesModificationsSet>
</DescribeReservedInstancesModificationsResponse>"""

    def test_serialized_api_args(self):
        self.set_http_response(status_code=200)
        response = self.ec2.describe_reserved_instances_modifications(
            reserved_instances_modification_ids=[
                '2567o137-8a55-48d6-82fb-7258506bb497'
            ],
            filters={
                'status': 'processing',
            }
        )
        self.assert_request_parameters({
            'Action': 'DescribeReservedInstancesModifications',
            'Filter.1.Name': 'status',
            'Filter.1.Value.1': 'processing',
            'ReservedInstancesModificationId.1': '2567o137-8a55-48d6-82fb-7258506bb497'
        }, ignore_params_values=[
            'AWSAccessKeyId', 'SignatureMethod',
            'SignatureVersion', 'Timestamp',
            'Version'
        ])

        # Make sure the response was parsed correctly.
        self.assertEqual(
            response[0].modification_id,
            'rimod-49b9433e-fdc7-464a-a6e5-9dabcexample'
        )
        self.assertEqual(
            response[0].create_date,
            datetime(2013, 9, 2, 21, 20, 19, 637000)
        )
        self.assertEqual(
            response[0].update_date,
            datetime(2013, 9, 2, 21, 38, 24, 143000)
        )
        self.assertEqual(
            response[0].effective_date,
            datetime(2013, 9, 2, 21, 0, 0, 0)
        )
        self.assertEqual(
            response[0].status,
            'fulfilled'
        )
        self.assertEqual(
            response[0].status_message,
            None
        )
        self.assertEqual(
            response[0].client_token,
            'token-f5b56c05-09b0-4d17-8d8c-c75d8a67b806'
        )
        self.assertEqual(
            response[0].reserved_instances[0].id,
            '2567o137-8a55-48d6-82fb-7258506bb497'
        )
        self.assertEqual(
            response[0].modification_results[0].availability_zone,
            'us-east-1b'
        )
        self.assertEqual(
            response[0].modification_results[0].platform,
            'EC2-VPC'
        )
        self.assertEqual(
            response[0].modification_results[0].instance_count,
            1
        )
        self.assertEqual(len(response), 1)


class TestRegisterImage(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
            <RegisterImageResponse xmlns="http://ec2.amazonaws.com/doc/2013-08-15/">
              <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
              <imageId>ami-1a2b3c4d</imageId>
            </RegisterImageResponse>
        """

    def test_vm_type_default(self):
        self.set_http_response(status_code=200)
        self.ec2.register_image('name', 'description',
                                image_location='s3://foo')

        self.assert_request_parameters({
            'Action': 'RegisterImage',
            'ImageLocation': 's3://foo',
            'Name': 'name',
            'Description': 'description',
        }, ignore_params_values=[
            'AWSAccessKeyId', 'SignatureMethod',
            'SignatureVersion', 'Timestamp',
            'Version'
        ])

    def test_vm_type_hvm(self):
        self.set_http_response(status_code=200)
        self.ec2.register_image('name', 'description',
                                image_location='s3://foo',
                                virtualization_type='hvm')

        self.assert_request_parameters({
            'Action': 'RegisterImage',
            'ImageLocation': 's3://foo',
            'Name': 'name',
            'Description': 'description',
            'VirtualizationType': 'hvm'
        }, ignore_params_values=[
            'AWSAccessKeyId', 'SignatureMethod',
            'SignatureVersion', 'Timestamp',
            'Version'
        ])

    def test_sriov_net_support_simple(self):
        self.set_http_response(status_code=200)
        self.ec2.register_image('name', 'description',
                                image_location='s3://foo',
                                sriov_net_support='simple')

        self.assert_request_parameters({
            'Action': 'RegisterImage',
            'ImageLocation': 's3://foo',
            'Name': 'name',
            'Description': 'description',
            'SriovNetSupport': 'simple'
        }, ignore_params_values=[
            'AWSAccessKeyId', 'SignatureMethod',
            'SignatureVersion', 'Timestamp',
            'Version'
        ])

    def test_volume_delete_on_termination_on(self):
        self.set_http_response(status_code=200)
        self.ec2.register_image('name', 'description',
                                snapshot_id='snap-12345678',
                                delete_root_volume_on_termination=True)

        self.assert_request_parameters({
            'Action': 'RegisterImage',
            'Name': 'name',
            'Description': 'description',
            'BlockDeviceMapping.1.DeviceName': None,
            'BlockDeviceMapping.1.Ebs.DeleteOnTermination': 'true',
            'BlockDeviceMapping.1.Ebs.SnapshotId': 'snap-12345678',
        }, ignore_params_values=[
            'AWSAccessKeyId', 'SignatureMethod',
            'SignatureVersion', 'Timestamp',
            'Version'
        ])

    def test_volume_delete_on_termination_default(self):
        self.set_http_response(status_code=200)
        self.ec2.register_image('name', 'description',
                                snapshot_id='snap-12345678')

        self.assert_request_parameters({
            'Action': 'RegisterImage',
            'Name': 'name',
            'Description': 'description',
            'BlockDeviceMapping.1.DeviceName': None,
            'BlockDeviceMapping.1.Ebs.DeleteOnTermination': 'false',
            'BlockDeviceMapping.1.Ebs.SnapshotId': 'snap-12345678',
        }, ignore_params_values=[
            'AWSAccessKeyId', 'SignatureMethod',
            'SignatureVersion', 'Timestamp',
            'Version'
        ])


class TestTerminateInstances(TestEC2ConnectionBase):
    def default_body(self):
        return b"""<?xml version="1.0" ?>
            <TerminateInstancesResponse xmlns="http://ec2.amazonaws.com/doc/2013-07-15/">
                <requestId>req-59a9ad52-0434-470c-ad48-4f89ded3a03e</requestId>
                <instancesSet>
                    <item>
                        <instanceId>i-000043a2</instanceId>
                        <shutdownState>
                            <code>16</code>
                            <name>running</name>
                        </shutdownState>
                        <previousState>
                            <code>16</code>
                            <name>running</name>
                        </previousState>
                    </item>
                </instancesSet>
            </TerminateInstancesResponse>
        """

    def test_terminate_bad_response(self):
        self.set_http_response(status_code=200)
        self.ec2.terminate_instances('foo')


class TestDescribeInstances(TestEC2ConnectionBase):

    def default_body(self):
        return b"""
            <DescribeInstancesResponse>
            </DescribeInstancesResponse>
        """

    def test_default_behavior(self):
        self.set_http_response(status_code=200)
        self.ec2.get_all_instances()
        self.assert_request_parameters({
            'Action': 'DescribeInstances'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])

        self.ec2.get_all_reservations()
        self.assert_request_parameters({
            'Action': 'DescribeInstances'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])

        self.ec2.get_only_instances()
        self.assert_request_parameters({
            'Action': 'DescribeInstances'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])

    def test_max_results(self):
        self.set_http_response(status_code=200)
        self.ec2.get_all_instances(
            max_results=10
        )
        self.assert_request_parameters({
            'Action': 'DescribeInstances',
            'MaxResults': 10},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])

    def test_next_token(self):
        self.set_http_response(status_code=200)
        self.ec2.get_all_reservations(
            next_token='abcdefgh',
        )
        self.assert_request_parameters({
            'Action': 'DescribeInstances',
            'NextToken': 'abcdefgh'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])


class TestDescribeTags(TestEC2ConnectionBase):

    def default_body(self):
        return b"""
            <DescribeTagsResponse>
            </DescribeTagsResponse>
        """

    def test_default_behavior(self):
        self.set_http_response(status_code=200)
        self.ec2.get_all_tags()
        self.assert_request_parameters({
            'Action': 'DescribeTags'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])

    def test_max_results(self):
        self.set_http_response(status_code=200)
        self.ec2.get_all_tags(
            max_results=10
        )
        self.assert_request_parameters({
            'Action': 'DescribeTags',
            'MaxResults': 10},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])


class TestSignatureAlteration(TestEC2ConnectionBase):
    def test_unchanged(self):
        self.assertEqual(
            self.service_connection._required_auth_capability(),
            ['hmac-v4']
        )

    def test_switched(self):
        region = RegionInfo(
            name='cn-north-1',
            endpoint='ec2.cn-north-1.amazonaws.com.cn',
            connection_cls=EC2Connection
        )

        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            region=region
        )
        self.assertEqual(
            conn._required_auth_capability(),
            ['hmac-v4']
        )


class TestAssociateAddress(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
            <AssociateAddressResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-15/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
               <associationId>eipassoc-fc5ca095</associationId>
            </AssociateAddressResponse>
        """

    def test_associate_address(self):
        self.set_http_response(status_code=200)
        result = self.ec2.associate_address(instance_id='i-1234',
                                            public_ip='192.0.2.1')
        self.assertEqual(True, result)

    def test_associate_address_object(self):
        self.set_http_response(status_code=200)
        result = self.ec2.associate_address_object(instance_id='i-1234',
                                                   public_ip='192.0.2.1')
        self.assertEqual('eipassoc-fc5ca095', result.association_id)


class TestAssociateAddressFail(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
            <Response>
                <Errors>
                     <Error>
                       <Code>InvalidInstanceID.NotFound</Code>
                       <Message>The instance ID 'i-4cbc822a' does not exist</Message>
                     </Error>
                </Errors>
                <RequestID>ea966190-f9aa-478e-9ede-cb5432daacc0</RequestID>
                <StatusCode>Failure</StatusCode>
            </Response>
        """

    def test_associate_address(self):
        self.set_http_response(status_code=200)
        result = self.ec2.associate_address(instance_id='i-1234',
                                            public_ip='192.0.2.1')
        self.assertEqual(False, result)


class TestDescribeVolumes(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
            <DescribeVolumesResponse xmlns="http://ec2.amazonaws.com/doc/2014-02-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <volumeSet>
                  <item>
                     <volumeId>vol-1a2b3c4d</volumeId>
                     <size>80</size>
                     <snapshotId/>
                     <availabilityZone>us-east-1a</availabilityZone>
                     <status>in-use</status>
                     <createTime>YYYY-MM-DDTHH:MM:SS.SSSZ</createTime>
                     <attachmentSet>
                        <item>
                           <volumeId>vol-1a2b3c4d</volumeId>
                           <instanceId>i-1a2b3c4d</instanceId>
                           <device>/dev/sdh</device>
                           <status>attached</status>
                           <attachTime>YYYY-MM-DDTHH:MM:SS.SSSZ</attachTime>
                           <deleteOnTermination>false</deleteOnTermination>
                        </item>
                     </attachmentSet>
                     <volumeType>standard</volumeType>
                     <encrypted>true</encrypted>
                  </item>
                  <item>
                     <volumeId>vol-5e6f7a8b</volumeId>
                     <size>80</size>
                     <snapshotId/>
                     <availabilityZone>us-east-1a</availabilityZone>
                     <status>in-use</status>
                     <createTime>YYYY-MM-DDTHH:MM:SS.SSSZ</createTime>
                     <attachmentSet>
                        <item>
                           <volumeId>vol-5e6f7a8b</volumeId>
                           <instanceId>i-5e6f7a8b</instanceId>
                           <device>/dev/sdz</device>
                           <status>attached</status>
                           <attachTime>YYYY-MM-DDTHH:MM:SS.SSSZ</attachTime>
                           <deleteOnTermination>false</deleteOnTermination>
                        </item>
                     </attachmentSet>
                     <volumeType>standard</volumeType>
                     <encrypted>false</encrypted>
                  </item>
               </volumeSet>
            </DescribeVolumesResponse>
        """

    def test_get_all_volumes(self):
        self.set_http_response(status_code=200)
        result = self.ec2.get_all_volumes(volume_ids=['vol-1a2b3c4d', 'vol-5e6f7a8b'])
        self.assert_request_parameters({
            'Action': 'DescribeVolumes',
            'VolumeId.1': 'vol-1a2b3c4d',
            'VolumeId.2': 'vol-5e6f7a8b'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 'vol-1a2b3c4d')
        self.assertTrue(result[0].encrypted)
        self.assertEqual(result[1].id, 'vol-5e6f7a8b')
        self.assertFalse(result[1].encrypted)


class TestDescribeSnapshots(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
            <DescribeSnapshotsResponse xmlns="http://ec2.amazonaws.com/doc/2014-02-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <snapshotSet>
                  <item>
                     <snapshotId>snap-1a2b3c4d</snapshotId>
                     <volumeId>vol-1a2b3c4d</volumeId>
                     <status>pending</status>
                     <startTime>YYYY-MM-DDTHH:MM:SS.SSSZ</startTime>
                     <progress>80%</progress>
                     <ownerId>111122223333</ownerId>
                     <volumeSize>15</volumeSize>
                     <description>Daily Backup</description>
                     <tagSet/>
                     <encrypted>true</encrypted>
                  </item>
               </snapshotSet>
               <snapshotSet>
                  <item>
                     <snapshotId>snap-5e6f7a8b</snapshotId>
                     <volumeId>vol-5e6f7a8b</volumeId>
                     <status>completed</status>
                     <startTime>YYYY-MM-DDTHH:MM:SS.SSSZ</startTime>
                     <progress>100%</progress>
                     <ownerId>111122223333</ownerId>
                     <volumeSize>15</volumeSize>
                     <description>Daily Backup</description>
                     <tagSet/>
                     <encrypted>false</encrypted>
                  </item>
               </snapshotSet>
           </DescribeSnapshotsResponse>
        """

    def test_get_all_snapshots(self):
        self.set_http_response(status_code=200)
        result = self.ec2.get_all_snapshots(snapshot_ids=['snap-1a2b3c4d', 'snap-5e6f7a8b'])
        self.assert_request_parameters({
            'Action': 'DescribeSnapshots',
            'SnapshotId.1': 'snap-1a2b3c4d',
            'SnapshotId.2': 'snap-5e6f7a8b'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 'snap-1a2b3c4d')
        self.assertTrue(result[0].encrypted)
        self.assertEqual(result[1].id, 'snap-5e6f7a8b')
        self.assertFalse(result[1].encrypted)


class TestCreateVolume(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
            <CreateVolumeResponse xmlns="http://ec2.amazonaws.com/doc/2014-05-01/">
              <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
              <volumeId>vol-1a2b3c4d</volumeId>
              <size>80</size>
              <snapshotId/>
              <availabilityZone>us-east-1a</availabilityZone>
              <status>creating</status>
              <createTime>YYYY-MM-DDTHH:MM:SS.000Z</createTime>
              <volumeType>standard</volumeType>
              <encrypted>true</encrypted>
            </CreateVolumeResponse>
        """

    def test_create_volume(self):
        self.set_http_response(status_code=200)
        result = self.ec2.create_volume(80, 'us-east-1e', snapshot='snap-1a2b3c4d',
                                        encrypted=True)
        self.assert_request_parameters({
            'Action': 'CreateVolume',
            'AvailabilityZone': 'us-east-1e',
            'Size': 80,
            'SnapshotId': 'snap-1a2b3c4d',
            'Encrypted': 'true'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(result.id, 'vol-1a2b3c4d')
        self.assertTrue(result.encrypted)

    def test_create_volume_with_specify_kms(self):
        self.set_http_response(status_code=200)
        result = self.ec2.create_volume(80, 'us-east-1e', snapshot='snap-1a2b3c4d',
                                        encrypted=True,kms_key_id='arn:aws:kms:us-east-1:012345678910:key/abcd1234-a123-456a-a12b-a123b4cd56ef')
        self.assert_request_parameters({
            'Action': 'CreateVolume',
            'AvailabilityZone': 'us-east-1e',
            'Size': 80,
            'SnapshotId': 'snap-1a2b3c4d',
            'Encrypted': 'true',
            'KmsKeyId': 'arn:aws:kms:us-east-1:012345678910:key/abcd1234-a123-456a-a12b-a123b4cd56ef'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(result.id, 'vol-1a2b3c4d')
        self.assertTrue(result.encrypted)


class TestGetClassicLinkInstances(TestEC2ConnectionBase):
    def default_body(self):
        return b"""
            <DescribeClassicLinkInstancesResponse xmlns="http://ec2.amazonaws.com/doc/2014-09-01/">
               <requestId>f4bf0cc6-5967-4687-9355-90ce48394bd3</requestId>
               <instancesSet>
                  <item>
                     <instanceId>i-31489bd8</instanceId>
                     <vpcId>vpc-9d24f8f8</vpcId>
                     <groupSet>
                        <item>
                           <groupId>sg-9b4343fe</groupId>
                        </item>
                    </groupSet>
                    <tagSet>
                        <item>
                           <key>Name</key>
                           <value>hello</value>
                        </item>
                    </tagSet>
                 </item>
              </instancesSet>
           </DescribeClassicLinkInstancesResponse>
        """
    def test_get_classic_link_instances(self):
        self.set_http_response(status_code=200)
        response = self.ec2.get_all_classic_link_instances()
        self.assertEqual(len(response), 1)
        instance = response[0]
        self.assertEqual(instance.id, 'i-31489bd8')
        self.assertEqual(instance.vpc_id, 'vpc-9d24f8f8')
        self.assertEqual(len(instance.groups), 1)
        self.assertEqual(instance.groups[0].id, 'sg-9b4343fe')
        self.assertEqual(instance.tags, {'Name': 'hello'})


    def test_get_classic_link_instances_params(self):
        self.set_http_response(status_code=200)
        self.ec2.get_all_classic_link_instances(
            instance_ids=['id1', 'id2'],
            filters={'GroupId': 'sg-9b4343fe'},
            dry_run=True,
            next_token='next_token',
            max_results=10
        )
        self.assert_request_parameters({
            'Action': 'DescribeClassicLinkInstances',
            'InstanceId.1': 'id1',
            'InstanceId.2': 'id2',
            'Filter.1.Name': 'GroupId',
            'Filter.1.Value.1': 'sg-9b4343fe',
            'DryRun': 'true',
            'NextToken': 'next_token',
            'MaxResults': 10},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp', 'Version'])


if __name__ == '__main__':
    unittest.main()
