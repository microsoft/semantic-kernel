#!/usr/bin/env python
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
#

import base64
from datetime import datetime

from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.ec2.autoscale import AutoScaleConnection
from boto.ec2.autoscale.group import AutoScalingGroup
from boto.ec2.autoscale.policy import ScalingPolicy
from boto.ec2.autoscale.tag import Tag

from boto.ec2.blockdevicemapping import EBSBlockDeviceType, BlockDeviceMapping

from boto.ec2.autoscale import launchconfig, LaunchConfiguration


class TestAutoScaleGroup(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def setUp(self):
        super(TestAutoScaleGroup, self).setUp()

    def default_body(self):
        return b"""
            <CreateLaunchConfigurationResponse>
              <ResponseMetadata>
                <RequestId>requestid</RequestId>
              </ResponseMetadata>
            </CreateLaunchConfigurationResponse>
        """

    def test_autoscaling_group_with_termination_policies(self):
        self.set_http_response(status_code=200)
        autoscale = AutoScalingGroup(
            name='foo', launch_config='lauch_config',
            min_size=1, max_size=2,
            termination_policies=['OldestInstance', 'OldestLaunchConfiguration'],
            instance_id='test-id')
        self.service_connection.create_auto_scaling_group(autoscale)
        self.assert_request_parameters({
            'Action': 'CreateAutoScalingGroup',
            'AutoScalingGroupName': 'foo',
            'LaunchConfigurationName': 'lauch_config',
            'MaxSize': 2,
            'MinSize': 1,
            'TerminationPolicies.member.1': 'OldestInstance',
            'TerminationPolicies.member.2': 'OldestLaunchConfiguration',
            'InstanceId': 'test-id',
        }, ignore_params_values=['Version'])

    def test_autoscaling_group_single_vpc_zone_identifier(self):
        self.set_http_response(status_code=200)
        autoscale = AutoScalingGroup(
            name='foo',
            vpc_zone_identifier='vpc_zone_1')
        self.service_connection.create_auto_scaling_group(autoscale)
        self.assert_request_parameters({
            'Action': 'CreateAutoScalingGroup',
            'AutoScalingGroupName': 'foo',
            'VPCZoneIdentifier': 'vpc_zone_1',
        }, ignore_params_values=['MaxSize', 'MinSize', 'LaunchConfigurationName', 'Version'])

    def test_autoscaling_group_vpc_zone_identifier_list(self):
        self.set_http_response(status_code=200)
        autoscale = AutoScalingGroup(
            name='foo',
            vpc_zone_identifier=['vpc_zone_1', 'vpc_zone_2'])
        self.service_connection.create_auto_scaling_group(autoscale)
        self.assert_request_parameters({
            'Action': 'CreateAutoScalingGroup',
            'AutoScalingGroupName': 'foo',
            'VPCZoneIdentifier': 'vpc_zone_1,vpc_zone_2',
        }, ignore_params_values=['MaxSize', 'MinSize', 'LaunchConfigurationName', 'Version'])

    def test_autoscaling_group_vpc_zone_identifier_multi(self):
        self.set_http_response(status_code=200)
        autoscale = AutoScalingGroup(
            name='foo',
            vpc_zone_identifier='vpc_zone_1,vpc_zone_2')
        self.service_connection.create_auto_scaling_group(autoscale)
        self.assert_request_parameters({
            'Action': 'CreateAutoScalingGroup',
            'AutoScalingGroupName': 'foo',
            'VPCZoneIdentifier': 'vpc_zone_1,vpc_zone_2',
        }, ignore_params_values=['MaxSize', 'MinSize', 'LaunchConfigurationName', 'Version'])


class TestAutoScaleGroupHonorCooldown(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def default_body(self):
        return b"""
            <SetDesiredCapacityResponse>
              <ResponseMetadata>
                <RequestId>9fb7e2db-6998-11e2-a985-57c82EXAMPLE</RequestId>
              </ResponseMetadata>
            </SetDesiredCapacityResponse>
        """

    def test_honor_cooldown(self):
        self.set_http_response(status_code=200)
        self.service_connection.set_desired_capacity('foo', 10, True)
        self.assert_request_parameters({
            'Action': 'SetDesiredCapacity',
            'AutoScalingGroupName': 'foo',
            'DesiredCapacity': 10,
            'HonorCooldown': 'true',
        }, ignore_params_values=['Version'])


class TestScheduledGroup(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def setUp(self):
        super(TestScheduledGroup, self).setUp()

    def default_body(self):
        return b"""
            <PutScheduledUpdateGroupActionResponse>
                <ResponseMetadata>
                  <RequestId>requestid</RequestId>
                </ResponseMetadata>
            </PutScheduledUpdateGroupActionResponse>
        """

    def test_scheduled_group_creation(self):
        self.set_http_response(status_code=200)
        self.service_connection.create_scheduled_group_action('foo',
                                                              'scheduled-foo',
                                                              desired_capacity=1,
                                                              start_time=datetime(2013, 1, 1, 22, 55, 31),
                                                              end_time=datetime(2013, 2, 1, 22, 55, 31),
                                                              min_size=1,
                                                              max_size=2,
                                                              recurrence='0 10 * * *')
        self.assert_request_parameters({
            'Action': 'PutScheduledUpdateGroupAction',
            'AutoScalingGroupName': 'foo',
            'ScheduledActionName': 'scheduled-foo',
            'MaxSize': 2,
            'MinSize': 1,
            'DesiredCapacity': 1,
            'EndTime': '2013-02-01T22:55:31',
            'StartTime': '2013-01-01T22:55:31',
            'Recurrence': '0 10 * * *',
        }, ignore_params_values=['Version'])


class TestParseAutoScaleGroupResponse(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def default_body(self):
        return b"""
          <DescribeAutoScalingGroupsResult>
             <AutoScalingGroups>
               <member>
                 <Tags/>
                 <SuspendedProcesses/>
                 <AutoScalingGroupName>test_group</AutoScalingGroupName>
                 <HealthCheckType>EC2</HealthCheckType>
                 <CreatedTime>2012-09-27T20:19:47.082Z</CreatedTime>
                 <EnabledMetrics/>
                 <LaunchConfigurationName>test_launchconfig</LaunchConfigurationName>
                 <Instances>
                   <member>
                     <HealthStatus>Healthy</HealthStatus>
                     <AvailabilityZone>us-east-1a</AvailabilityZone>
                     <InstanceId>i-z118d054</InstanceId>
                     <LaunchConfigurationName>test_launchconfig</LaunchConfigurationName>
                     <LifecycleState>InService</LifecycleState>
                   </member>
                 </Instances>
                 <DesiredCapacity>1</DesiredCapacity>
                 <AvailabilityZones>
                   <member>us-east-1c</member>
                   <member>us-east-1a</member>
                 </AvailabilityZones>
                 <LoadBalancerNames/>
                 <MinSize>1</MinSize>
                 <VPCZoneIdentifier/>
                 <HealthCheckGracePeriod>0</HealthCheckGracePeriod>
                 <DefaultCooldown>300</DefaultCooldown>
                 <AutoScalingGroupARN>myarn</AutoScalingGroupARN>
                 <TerminationPolicies>
                   <member>OldestInstance</member>
                   <member>OldestLaunchConfiguration</member>
                 </TerminationPolicies>
                 <MaxSize>2</MaxSize>
                 <InstanceId>Something</InstanceId>
               </member>
             </AutoScalingGroups>
          </DescribeAutoScalingGroupsResult>
        """

    def test_get_all_groups_is_parsed_correctly(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_all_groups(names=['test_group'])
        self.assertEqual(len(response), 1, response)
        as_group = response[0]
        self.assertEqual(as_group.availability_zones, ['us-east-1c', 'us-east-1a'])
        self.assertEqual(as_group.default_cooldown, 300)
        self.assertEqual(as_group.desired_capacity, 1)
        self.assertEqual(as_group.enabled_metrics, [])
        self.assertEqual(as_group.health_check_period, 0)
        self.assertEqual(as_group.health_check_type, 'EC2')
        self.assertEqual(as_group.launch_config_name, 'test_launchconfig')
        self.assertEqual(as_group.load_balancers, [])
        self.assertEqual(as_group.min_size, 1)
        self.assertEqual(as_group.max_size, 2)
        self.assertEqual(as_group.name, 'test_group')
        self.assertEqual(as_group.suspended_processes, [])
        self.assertEqual(as_group.tags, [])
        self.assertEqual(as_group.termination_policies,
                         ['OldestInstance', 'OldestLaunchConfiguration'])
        self.assertEqual(as_group.instance_id, 'Something')


class TestDescribeTerminationPolicies(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def default_body(self):
        return b"""
          <DescribeTerminationPolicyTypesResponse>
            <DescribeTerminationPolicyTypesResult>
              <TerminationPolicyTypes>
                <member>ClosestToNextInstanceHour</member>
                <member>Default</member>
                <member>NewestInstance</member>
                <member>OldestInstance</member>
                <member>OldestLaunchConfiguration</member>
              </TerminationPolicyTypes>
            </DescribeTerminationPolicyTypesResult>
            <ResponseMetadata>
              <RequestId>requestid</RequestId>
            </ResponseMetadata>
          </DescribeTerminationPolicyTypesResponse>
        """

    def test_autoscaling_group_with_termination_policies(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_termination_policies()
        self.assertListEqual(
            response,
            ['ClosestToNextInstanceHour', 'Default',
             'NewestInstance', 'OldestInstance', 'OldestLaunchConfiguration'])


class TestLaunchConfigurationDescribe(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def default_body(self):
        # This is a dummy response
        return b"""
        <DescribeLaunchConfigurationsResponse>
          <DescribeLaunchConfigurationsResult>
            <LaunchConfigurations>
              <member>
                <AssociatePublicIpAddress>true</AssociatePublicIpAddress>
                <SecurityGroups/>
                <CreatedTime>2013-01-21T23:04:42.200Z</CreatedTime>
                <KernelId/>
                <LaunchConfigurationName>my-test-lc</LaunchConfigurationName>
                <UserData/>
                <InstanceType>m1.small</InstanceType>
                <LaunchConfigurationARN>arn:aws:autoscaling:us-east-1:803981987763:launchConfiguration:9dbbbf87-6141-428a-a409-0752edbe6cad:launchConfigurationName/my-test-lc</LaunchConfigurationARN>
                <BlockDeviceMappings/>
                <ImageId>ami-514ac838</ImageId>
                <KeyName/>
                <RamdiskId/>
                <InstanceMonitoring>
                  <Enabled>true</Enabled>
                </InstanceMonitoring>
                <EbsOptimized>false</EbsOptimized>
                <ClassicLinkVPCId>vpc-12345</ClassicLinkVPCId>
                <ClassicLinkVPCSecurityGroups>
                    <member>sg-1234</member>
                </ClassicLinkVPCSecurityGroups>
              </member>
            </LaunchConfigurations>
          </DescribeLaunchConfigurationsResult>
          <ResponseMetadata>
            <RequestId>d05a22f8-b690-11e2-bf8e-2113fEXAMPLE</RequestId>
          </ResponseMetadata>
        </DescribeLaunchConfigurationsResponse>
        """

    def test_get_all_launch_configurations(self):
        self.set_http_response(status_code=200)

        response = self.service_connection.get_all_launch_configurations()
        self.assertTrue(isinstance(response, list))
        self.assertEqual(len(response), 1)
        self.assertTrue(isinstance(response[0], LaunchConfiguration))

        self.assertEqual(response[0].associate_public_ip_address, True)
        self.assertEqual(response[0].name, "my-test-lc")
        self.assertEqual(response[0].instance_type, "m1.small")
        self.assertEqual(response[0].launch_configuration_arn, "arn:aws:autoscaling:us-east-1:803981987763:launchConfiguration:9dbbbf87-6141-428a-a409-0752edbe6cad:launchConfigurationName/my-test-lc")
        self.assertEqual(response[0].image_id, "ami-514ac838")
        self.assertTrue(isinstance(response[0].instance_monitoring, launchconfig.InstanceMonitoring))
        self.assertEqual(response[0].instance_monitoring.enabled, 'true')
        self.assertEqual(response[0].ebs_optimized, False)
        self.assertEqual(response[0].block_device_mappings, [])
        self.assertEqual(response[0].classic_link_vpc_id, 'vpc-12345')
        self.assertEqual(response[0].classic_link_vpc_security_groups,
                         ['sg-1234'])

        self.assert_request_parameters({
            'Action': 'DescribeLaunchConfigurations',
        }, ignore_params_values=['Version'])

    def test_get_all_configuration_limited(self):
        self.set_http_response(status_code=200)

        response = self.service_connection.get_all_launch_configurations(max_records=10, names=["my-test1", "my-test2"])
        self.assert_request_parameters({
            'Action': 'DescribeLaunchConfigurations',
            'MaxRecords': 10,
            'LaunchConfigurationNames.member.1': 'my-test1',
            'LaunchConfigurationNames.member.2': 'my-test2'
        }, ignore_params_values=['Version'])


class TestLaunchConfiguration(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def default_body(self):
        # This is a dummy response
        return b"""
        <DescribeLaunchConfigurationsResponse>
        </DescribeLaunchConfigurationsResponse>
        """

    def test_launch_config(self):
        # This unit test is based on #753 and #1343
        self.set_http_response(status_code=200)
        dev_sdf = EBSBlockDeviceType(snapshot_id='snap-12345')

        bdm = BlockDeviceMapping()
        bdm['/dev/sdf'] = dev_sdf

        lc = launchconfig.LaunchConfiguration(
            connection=self.service_connection,
            name='launch_config',
            image_id='123456',
            instance_type='m1.large',
            user_data='#!/bin/bash',
            security_groups=['group1'],
            spot_price='price',
            block_device_mappings=[bdm],
            associate_public_ip_address=True,
            volume_type='atype',
            delete_on_termination=False,
            iops=3000,
            classic_link_vpc_id='vpc-1234',
            classic_link_vpc_security_groups=['classic_link_group']
        )

        response = self.service_connection.create_launch_configuration(lc)

        self.assert_request_parameters({
            'Action': 'CreateLaunchConfiguration',
            'BlockDeviceMappings.member.1.DeviceName': '/dev/sdf',
            'BlockDeviceMappings.member.1.Ebs.DeleteOnTermination': 'false',
            'BlockDeviceMappings.member.1.Ebs.SnapshotId': 'snap-12345',
            'EbsOptimized': 'false',
            'LaunchConfigurationName': 'launch_config',
            'ImageId': '123456',
            'UserData': base64.b64encode(b'#!/bin/bash').decode('utf-8'),
            'InstanceMonitoring.Enabled': 'false',
            'InstanceType': 'm1.large',
            'SecurityGroups.member.1': 'group1',
            'SpotPrice': 'price',
            'AssociatePublicIpAddress': 'true',
            'VolumeType': 'atype',
            'DeleteOnTermination': 'false',
            'Iops': 3000,
            'ClassicLinkVPCId': 'vpc-1234',
            'ClassicLinkVPCSecurityGroups.member.1': 'classic_link_group'
        }, ignore_params_values=['Version'])


class TestCreateAutoScalePolicy(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def setUp(self):
        super(TestCreateAutoScalePolicy, self).setUp()

    def default_body(self):
        return b"""
            <PutScalingPolicyResponse xmlns="http://autoscaling.amazonaws.com\
            /doc/2011-01-01/">
              <PutScalingPolicyResult>
                <PolicyARN>arn:aws:autoscaling:us-east-1:803981987763:scaling\
                Policy:b0dcf5e8
            -02e6-4e31-9719-0675d0dc31ae:autoScalingGroupName/my-test-asg:\
            policyName/my-scal
            eout-policy</PolicyARN>
              </PutScalingPolicyResult>
              <ResponseMetadata>
                <RequestId>3cfc6fef-c08b-11e2-a697-2922EXAMPLE</RequestId>
              </ResponseMetadata>
            </PutScalingPolicyResponse>
        """

    def test_scaling_policy_with_min_adjustment_step(self):
        self.set_http_response(status_code=200)

        policy = ScalingPolicy(
            name='foo', as_name='bar',
            adjustment_type='PercentChangeInCapacity', scaling_adjustment=50,
            min_adjustment_step=30)
        self.service_connection.create_scaling_policy(policy)

        self.assert_request_parameters({
            'Action': 'PutScalingPolicy',
            'PolicyName': 'foo',
            'AutoScalingGroupName': 'bar',
            'AdjustmentType': 'PercentChangeInCapacity',
            'ScalingAdjustment': 50,
            'MinAdjustmentStep': 30
        }, ignore_params_values=['Version'])

    def test_scaling_policy_with_wrong_adjustment_type(self):
        self.set_http_response(status_code=200)

        policy = ScalingPolicy(
            name='foo', as_name='bar',
            adjustment_type='ChangeInCapacity', scaling_adjustment=50,
            min_adjustment_step=30)
        self.service_connection.create_scaling_policy(policy)

        self.assert_request_parameters({
            'Action': 'PutScalingPolicy',
            'PolicyName': 'foo',
            'AutoScalingGroupName': 'bar',
            'AdjustmentType': 'ChangeInCapacity',
            'ScalingAdjustment': 50
        }, ignore_params_values=['Version'])

    def test_scaling_policy_without_min_adjustment_step(self):
        self.set_http_response(status_code=200)

        policy = ScalingPolicy(
            name='foo', as_name='bar',
            adjustment_type='PercentChangeInCapacity', scaling_adjustment=50)
        self.service_connection.create_scaling_policy(policy)

        self.assert_request_parameters({
            'Action': 'PutScalingPolicy',
            'PolicyName': 'foo',
            'AutoScalingGroupName': 'bar',
            'AdjustmentType': 'PercentChangeInCapacity',
            'ScalingAdjustment': 50
        }, ignore_params_values=['Version'])


class TestPutNotificationConfiguration(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def setUp(self):
        super(TestPutNotificationConfiguration, self).setUp()

    def default_body(self):
        return b"""
            <PutNotificationConfigurationResponse>
              <ResponseMetadata>
                <RequestId>requestid</RequestId>
              </ResponseMetadata>
            </PutNotificationConfigurationResponse>
        """

    def test_autoscaling_group_put_notification_configuration(self):
        self.set_http_response(status_code=200)
        autoscale = AutoScalingGroup(
            name='ana', launch_config='lauch_config',
            min_size=1, max_size=2,
            termination_policies=['OldestInstance', 'OldestLaunchConfiguration'])
        self.service_connection.put_notification_configuration(autoscale, 'arn:aws:sns:us-east-1:19890506:AutoScaling-Up', ['autoscaling:EC2_INSTANCE_LAUNCH'])
        self.assert_request_parameters({
            'Action': 'PutNotificationConfiguration',
            'AutoScalingGroupName': 'ana',
            'NotificationTypes.member.1': 'autoscaling:EC2_INSTANCE_LAUNCH',
            'TopicARN': 'arn:aws:sns:us-east-1:19890506:AutoScaling-Up',
        }, ignore_params_values=['Version'])


class TestDeleteNotificationConfiguration(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def setUp(self):
        super(TestDeleteNotificationConfiguration, self).setUp()

    def default_body(self):
        return b"""
            <DeleteNotificationConfigurationResponse>
              <ResponseMetadata>
                <RequestId>requestid</RequestId>
              </ResponseMetadata>
            </DeleteNotificationConfigurationResponse>
        """

    def test_autoscaling_group_put_notification_configuration(self):
        self.set_http_response(status_code=200)
        autoscale = AutoScalingGroup(
            name='ana', launch_config='lauch_config',
            min_size=1, max_size=2,
            termination_policies=['OldestInstance', 'OldestLaunchConfiguration'])
        self.service_connection.delete_notification_configuration(autoscale, 'arn:aws:sns:us-east-1:19890506:AutoScaling-Up')
        self.assert_request_parameters({
            'Action': 'DeleteNotificationConfiguration',
            'AutoScalingGroupName': 'ana',
            'TopicARN': 'arn:aws:sns:us-east-1:19890506:AutoScaling-Up',
        }, ignore_params_values=['Version'])


class TestAutoScalingTag(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def default_body(self):
        return b"""
        <CreateOrUpdateTagsResponse>
            <ResponseMetadata>
                <RequestId>requestId</RequestId>
            </ResponseMetadata>
        </CreateOrUpdateTagsResponse>
        """

    def test_create_or_update_tags(self):
        self.set_http_response(status_code=200)

        tags = [
            Tag(
                connection=self.service_connection,
                key='alpha',
                value='tango',
                resource_id='sg-00000000',
                resource_type='auto-scaling-group',
                propagate_at_launch=True
            ),
            Tag(
                connection=self.service_connection,
                key='bravo',
                value='sierra',
                resource_id='sg-00000000',
                resource_type='auto-scaling-group',
                propagate_at_launch=False
            )]

        response = self.service_connection.create_or_update_tags(tags)

        self.assert_request_parameters({
            'Action': 'CreateOrUpdateTags',
            'Tags.member.1.ResourceType': 'auto-scaling-group',
            'Tags.member.1.ResourceId': 'sg-00000000',
            'Tags.member.1.Key': 'alpha',
            'Tags.member.1.Value': 'tango',
            'Tags.member.1.PropagateAtLaunch': 'true',
            'Tags.member.2.ResourceType': 'auto-scaling-group',
            'Tags.member.2.ResourceId': 'sg-00000000',
            'Tags.member.2.Key': 'bravo',
            'Tags.member.2.Value': 'sierra',
            'Tags.member.2.PropagateAtLaunch': 'false'
        }, ignore_params_values=['Version'])

    def test_endElement(self):
        for i in [
            ('Key', 'mykey', 'key'),
            ('Value', 'myvalue', 'value'),
            ('ResourceType', 'auto-scaling-group', 'resource_type'),
            ('ResourceId', 'sg-01234567', 'resource_id'),
            ('PropagateAtLaunch', 'true', 'propagate_at_launch')]:
                self.check_tag_attributes_set(i[0], i[1], i[2])

    def check_tag_attributes_set(self, name, value, attr):
        tag = Tag()
        tag.endElement(name, value, None)
        if value == 'true':
            self.assertEqual(getattr(tag, attr), True)
        else:
            self.assertEqual(getattr(tag, attr), value)


class TestAttachInstances(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def setUp(self):
        super(TestAttachInstances, self).setUp()

    def default_body(self):
        return b"""
            <AttachInstancesResponse>
              <ResponseMetadata>
                <RequestId>requestid</RequestId>
              </ResponseMetadata>
            </AttachInstancesResponse>
        """

    def test_attach_instances(self):
        self.set_http_response(status_code=200)
        self.service_connection.attach_instances(
            'autoscale',
            ['inst2', 'inst1', 'inst4']
        )
        self.assert_request_parameters({
            'Action': 'AttachInstances',
            'AutoScalingGroupName': 'autoscale',
            'InstanceIds.member.1': 'inst2',
            'InstanceIds.member.2': 'inst1',
            'InstanceIds.member.3': 'inst4',
        }, ignore_params_values=['Version'])


class TestDetachInstances(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def setUp(self):
        super(TestDetachInstances, self).setUp()

    def default_body(self):
        return b"""
            <DetachInstancesResponse>
              <ResponseMetadata>
                <RequestId>requestid</RequestId>
              </ResponseMetadata>
            </DetachInstancesResponse>
        """

    def test_detach_instances(self):
        self.set_http_response(status_code=200)
        self.service_connection.detach_instances(
            'autoscale',
            ['inst2', 'inst1', 'inst4']
        )
        self.assert_request_parameters({
            'Action': 'DetachInstances',
            'AutoScalingGroupName': 'autoscale',
            'InstanceIds.member.1': 'inst2',
            'InstanceIds.member.2': 'inst1',
            'InstanceIds.member.3': 'inst4',
            'ShouldDecrementDesiredCapacity': 'true',
        }, ignore_params_values=['Version'])

    def test_detach_instances_with_decrement_desired_capacity(self):
        self.set_http_response(status_code=200)
        self.service_connection.detach_instances(
            'autoscale',
            ['inst2', 'inst1', 'inst4'],
            True
        )
        self.assert_request_parameters({
            'Action': 'DetachInstances',
            'AutoScalingGroupName': 'autoscale',
            'InstanceIds.member.1': 'inst2',
            'InstanceIds.member.2': 'inst1',
            'InstanceIds.member.3': 'inst4',
            'ShouldDecrementDesiredCapacity': 'true',
        }, ignore_params_values=['Version'])

    def test_detach_instances_without_decrement_desired_capacity(self):
        self.set_http_response(status_code=200)
        self.service_connection.detach_instances(
            'autoscale',
            ['inst2', 'inst1', 'inst4'],
            False
        )
        self.assert_request_parameters({
            'Action': 'DetachInstances',
            'AutoScalingGroupName': 'autoscale',
            'InstanceIds.member.1': 'inst2',
            'InstanceIds.member.2': 'inst1',
            'InstanceIds.member.3': 'inst4',
            'ShouldDecrementDesiredCapacity': 'false',
        }, ignore_params_values=['Version'])


class TestGetAccountLimits(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def setUp(self):
        super(TestGetAccountLimits, self).setUp()

    def default_body(self):
        return b"""
            <DescribeAccountLimitsAnswer>
              <MaxNumberOfAutoScalingGroups>6</MaxNumberOfAutoScalingGroups>
              <MaxNumberOfLaunchConfigurations>3</MaxNumberOfLaunchConfigurations>
              <ResponseMetadata>
                <RequestId>requestid</RequestId>
              </ResponseMetadata>
            </DescribeAccountLimitsAnswer>
        """

    def test_autoscaling_group_put_notification_configuration(self):
        self.set_http_response(status_code=200)
        limits = self.service_connection.get_account_limits()
        self.assert_request_parameters({
            'Action': 'DescribeAccountLimits',
        }, ignore_params_values=['Version'])
        self.assertEqual(limits.max_autoscaling_groups, 6)
        self.assertEqual(limits.max_launch_configurations, 3)


class TestGetAdjustmentTypes(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def setUp(self):
        super(TestGetAdjustmentTypes, self).setUp()

    def default_body(self):
        return b"""
            <DescribeAdjustmentTypesResponse xmlns="http://autoscaling.amazonaws.com/doc/201-01-01/">
              <DescribeAdjustmentTypesResult>
                <AdjustmentTypes>
                  <member>
                    <AdjustmentType>ChangeInCapacity</AdjustmentType>
                  </member>
                  <member>
                    <AdjustmentType>ExactCapacity</AdjustmentType>
                  </member>
                  <member>
                    <AdjustmentType>PercentChangeInCapacity</AdjustmentType>
                  </member>
                </AdjustmentTypes>
              </DescribeAdjustmentTypesResult>
              <ResponseMetadata>
                <RequestId>requestId</RequestId>
              </ResponseMetadata>
            </DescribeAdjustmentTypesResponse>
        """

    def test_autoscaling_adjustment_types(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_all_adjustment_types()
        self.assert_request_parameters({
            'Action': 'DescribeAdjustmentTypes'
        }, ignore_params_values=['Version'])

        self.assertTrue(isinstance(response, list))
        self.assertEqual(response[0].adjustment_type, "ChangeInCapacity")
        self.assertEqual(response[1].adjustment_type, "ExactCapacity")
        self.assertEqual(response[2].adjustment_type, "PercentChangeInCapacity")


class TestLaunchConfigurationDescribeWithBlockDeviceTypes(AWSMockServiceTestCase):
    connection_class = AutoScaleConnection

    def default_body(self):
        # This is a dummy response
        return b"""
        <DescribeLaunchConfigurationsResponse>
          <DescribeLaunchConfigurationsResult>
            <LaunchConfigurations>
              <member>
                <AssociatePublicIpAddress>true</AssociatePublicIpAddress>
                <SecurityGroups/>
                <CreatedTime>2013-01-21T23:04:42.200Z</CreatedTime>
                <KernelId/>
                <LaunchConfigurationName>my-test-lc</LaunchConfigurationName>
                <UserData/>
                <InstanceType>m1.small</InstanceType>
                <LaunchConfigurationARN>arn:aws:autoscaling:us-east-1:803981987763:launchConfiguration:9dbbbf87-6141-428a-a409-0752edbe6cad:launchConfigurationName/my-test-lc</LaunchConfigurationARN>
                <BlockDeviceMappings>
                  <member>
                    <DeviceName>/dev/xvdp</DeviceName>
                    <Ebs>
                      <SnapshotId>snap-1234abcd</SnapshotId>
                      <Iops>1000</Iops>
                      <DeleteOnTermination>true</DeleteOnTermination>
                      <VolumeType>io1</VolumeType>
                      <VolumeSize>100</VolumeSize>
                    </Ebs>
                  </member>
                  <member>
                    <VirtualName>ephemeral1</VirtualName>
                    <DeviceName>/dev/xvdc</DeviceName>
                  </member>
                  <member>
                    <VirtualName>ephemeral0</VirtualName>
                    <DeviceName>/dev/xvdb</DeviceName>
                  </member>
                  <member>
                    <DeviceName>/dev/xvdh</DeviceName>
                    <Ebs>
                      <Iops>2000</Iops>
                      <DeleteOnTermination>false</DeleteOnTermination>
                      <VolumeType>io1</VolumeType>
                      <VolumeSize>200</VolumeSize>
                    </Ebs>
                  </member>
                </BlockDeviceMappings>
                <ImageId>ami-514ac838</ImageId>
                <KeyName/>
                <RamdiskId/>
                <InstanceMonitoring>
                  <Enabled>true</Enabled>
                </InstanceMonitoring>
                <EbsOptimized>false</EbsOptimized>
              </member>
            </LaunchConfigurations>
          </DescribeLaunchConfigurationsResult>
          <ResponseMetadata>
            <RequestId>d05a22f8-b690-11e2-bf8e-2113fEXAMPLE</RequestId>
          </ResponseMetadata>
        </DescribeLaunchConfigurationsResponse>
        """

    def test_get_all_launch_configurations_with_block_device_types(self):
        self.set_http_response(status_code=200)
        self.service_connection.use_block_device_types = True

        response = self.service_connection.get_all_launch_configurations()
        self.assertTrue(isinstance(response, list))
        self.assertEqual(len(response), 1)
        self.assertTrue(isinstance(response[0], LaunchConfiguration))

        self.assertEqual(response[0].associate_public_ip_address, True)
        self.assertEqual(response[0].name, "my-test-lc")
        self.assertEqual(response[0].instance_type, "m1.small")
        self.assertEqual(response[0].launch_configuration_arn, "arn:aws:autoscaling:us-east-1:803981987763:launchConfiguration:9dbbbf87-6141-428a-a409-0752edbe6cad:launchConfigurationName/my-test-lc")
        self.assertEqual(response[0].image_id, "ami-514ac838")
        self.assertTrue(isinstance(response[0].instance_monitoring, launchconfig.InstanceMonitoring))
        self.assertEqual(response[0].instance_monitoring.enabled, 'true')
        self.assertEqual(response[0].ebs_optimized, False)

        self.assertEqual(response[0].block_device_mappings['/dev/xvdb'].ephemeral_name, 'ephemeral0')

        self.assertEqual(response[0].block_device_mappings['/dev/xvdc'].ephemeral_name, 'ephemeral1')

        self.assertEqual(response[0].block_device_mappings['/dev/xvdp'].snapshot_id, 'snap-1234abcd')
        self.assertEqual(response[0].block_device_mappings['/dev/xvdp'].delete_on_termination, True)
        self.assertEqual(response[0].block_device_mappings['/dev/xvdp'].iops, 1000)
        self.assertEqual(response[0].block_device_mappings['/dev/xvdp'].size, 100)
        self.assertEqual(response[0].block_device_mappings['/dev/xvdp'].volume_type, 'io1')

        self.assertEqual(response[0].block_device_mappings['/dev/xvdh'].delete_on_termination, False)
        self.assertEqual(response[0].block_device_mappings['/dev/xvdh'].iops, 2000)
        self.assertEqual(response[0].block_device_mappings['/dev/xvdh'].size, 200)
        self.assertEqual(response[0].block_device_mappings['/dev/xvdh'].volume_type, 'io1')

        self.assert_request_parameters({
            'Action': 'DescribeLaunchConfigurations',
        }, ignore_params_values=['Version'])

    def test_get_all_configuration_limited(self):
        self.set_http_response(status_code=200)

        response = self.service_connection.get_all_launch_configurations(max_records=10, names=["my-test1", "my-test2"])
        self.assert_request_parameters({
            'Action': 'DescribeLaunchConfigurations',
            'MaxRecords': 10,
            'LaunchConfigurationNames.member.1': 'my-test1',
            'LaunchConfigurationNames.member.2': 'my-test2'
        }, ignore_params_values=['Version'])


if __name__ == '__main__':
    unittest.main()
