# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.
# All rights reserved.
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
import boto.utils

from datetime import datetime
from time import time
from tests.unit import AWSMockServiceTestCase

from boto.compat import six
from boto.emr.connection import EmrConnection
from boto.emr.emrobject import BootstrapAction, BootstrapActionList, \
    ClusterStateChangeReason, ClusterStatus, ClusterSummaryList, \
    ClusterSummary, ClusterTimeline, InstanceInfo, \
    InstanceList, InstanceGroupInfo, \
    InstanceGroup, InstanceGroupList, JobFlow, \
    JobFlowStepList, Step, StepSummaryList, \
    Cluster, RunJobFlowResponse


# These tests are just checking the basic structure of
# the Elastic MapReduce code, by picking a few calls
# and verifying we get the expected results with mocked
# responses.  The integration tests actually verify the
# API calls interact with the service correctly.


class TestListClusters(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""
<ListClustersResponse xmlns="http://elasticmapreduce.amazonaws.com/doc/2009-03-31">
  <ListClustersResult>
    <Clusters>
      <member>
        <Id>j-aaaaaaaaaaaa</Id>
        <Status>
          <StateChangeReason>
            <Message>Terminated by user request</Message>
            <Code>USER_REQUEST</Code>
          </StateChangeReason>
          <State>TERMINATED</State>
          <Timeline>
            <CreationDateTime>2014-01-24T01:21:21Z</CreationDateTime>
            <ReadyDateTime>2014-01-24T01:25:26Z</ReadyDateTime>
            <EndDateTime>2014-01-24T02:19:46Z</EndDateTime>
          </Timeline>
        </Status>
        <Name>analytics test</Name>
        <NormalizedInstanceHours>10</NormalizedInstanceHours>
      </member>
      <member>
        <Id>j-aaaaaaaaaaaab</Id>
        <Status>
          <StateChangeReason>
            <Message>Terminated by user request</Message>
            <Code>USER_REQUEST</Code>
          </StateChangeReason>
          <State>TERMINATED</State>
          <Timeline>
            <CreationDateTime>2014-01-21T02:53:08Z</CreationDateTime>
            <ReadyDateTime>2014-01-21T02:56:40Z</ReadyDateTime>
            <EndDateTime>2014-01-21T03:40:22Z</EndDateTime>
          </Timeline>
        </Status>
        <Name>test job</Name>
        <NormalizedInstanceHours>20</NormalizedInstanceHours>
      </member>
    </Clusters>
  </ListClustersResult>
  <ResponseMetadata>
    <RequestId>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</RequestId>
  </ResponseMetadata>
</ListClustersResponse>
        """

    def test_list_clusters(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.list_clusters()

        self.assert_request_parameters({
            'Action': 'ListClusters',
            'Version': '2009-03-31',
        })

        self.assertTrue(isinstance(response, ClusterSummaryList))

        self.assertEqual(len(response.clusters), 2)

        self.assertTrue(isinstance(response.clusters[0], ClusterSummary))
        self.assertEqual(response.clusters[0].name, 'analytics test')
        self.assertEqual(response.clusters[0].normalizedinstancehours, '10')

        self.assertTrue(isinstance(response.clusters[0].status, ClusterStatus))
        self.assertEqual(response.clusters[0].status.state, 'TERMINATED')

        self.assertTrue(
            isinstance(response.clusters[0].status.timeline, ClusterTimeline))

        self.assertEqual(
            response.clusters[0].status.timeline.creationdatetime, '2014-01-24T01:21:21Z')
        self.assertEqual(
            response.clusters[0].status.timeline.readydatetime, '2014-01-24T01:25:26Z')
        self.assertEqual(
            response.clusters[0].status.timeline.enddatetime, '2014-01-24T02:19:46Z')

        self.assertTrue(isinstance(
            response.clusters[0].status.statechangereason, ClusterStateChangeReason))
        self.assertEqual(
            response.clusters[0].status.statechangereason.code, 'USER_REQUEST')
        self.assertEqual(response.clusters[
                         0].status.statechangereason.message, 'Terminated by user request')

    def test_list_clusters_created_before(self):
        self.set_http_response(status_code=200)

        date = datetime.now()
        response = self.service_connection.list_clusters(created_before=date)

        self.assert_request_parameters({
            'Action': 'ListClusters',
            'CreatedBefore': date.strftime(boto.utils.ISO8601),
            'Version': '2009-03-31'
        })

    def test_list_clusters_created_after(self):
        self.set_http_response(status_code=200)

        date = datetime.now()
        response = self.service_connection.list_clusters(created_after=date)

        self.assert_request_parameters({
            'Action': 'ListClusters',
            'CreatedAfter': date.strftime(boto.utils.ISO8601),
            'Version': '2009-03-31'
        })

    def test_list_clusters_states(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.list_clusters(cluster_states=[
            'RUNNING',
            'WAITING'
        ])

        self.assert_request_parameters({
            'Action': 'ListClusters',
            'ClusterStates.member.1': 'RUNNING',
            'ClusterStates.member.2': 'WAITING',
            'Version': '2009-03-31'
        })


class TestListInstanceGroups(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""
<ListInstanceGroupsResponse xmlns="http://elasticmapreduce.amazonaws.com/doc/2009-03-31">
  <ListInstanceGroupsResult>
    <InstanceGroups>
      <member>
        <Id>ig-aaaaaaaaaaaaa</Id>
        <InstanceType>m1.large</InstanceType>
        <Market>ON_DEMAND</Market>
        <Status>
          <StateChangeReason>
            <Message>Job flow terminated</Message>
            <Code>CLUSTER_TERMINATED</Code>
          </StateChangeReason>
          <State>TERMINATED</State>
          <Timeline>
            <CreationDateTime>2014-01-24T01:21:21Z</CreationDateTime>
            <ReadyDateTime>2014-01-24T01:25:08Z</ReadyDateTime>
            <EndDateTime>2014-01-24T02:19:46Z</EndDateTime>
          </Timeline>
        </Status>
        <Name>Master instance group</Name>
        <RequestedInstanceCount>1</RequestedInstanceCount>
        <RunningInstanceCount>0</RunningInstanceCount>
        <InstanceGroupType>MASTER</InstanceGroupType>
      </member>
      <member>
        <Id>ig-aaaaaaaaaaab</Id>
        <InstanceType>m1.large</InstanceType>
        <Market>ON_DEMAND</Market>
        <Status>
          <StateChangeReason>
            <Message>Job flow terminated</Message>
            <Code>CLUSTER_TERMINATED</Code>
          </StateChangeReason>
          <State>TERMINATED</State>
          <Timeline>
            <CreationDateTime>2014-01-24T01:21:21Z</CreationDateTime>
            <ReadyDateTime>2014-01-24T01:25:26Z</ReadyDateTime>
            <EndDateTime>2014-01-24T02:19:46Z</EndDateTime>
          </Timeline>
        </Status>
        <Name>Core instance group</Name>
        <RequestedInstanceCount>2</RequestedInstanceCount>
        <RunningInstanceCount>0</RunningInstanceCount>
        <InstanceGroupType>CORE</InstanceGroupType>
      </member>
    </InstanceGroups>
  </ListInstanceGroupsResult>
  <ResponseMetadata>
    <RequestId>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</RequestId>
  </ResponseMetadata>
</ListInstanceGroupsResponse>

"""

    def test_list_instance_groups(self):
        self.set_http_response(200)

        with self.assertRaises(TypeError):
            self.service_connection.list_instance_groups()

        response = self.service_connection.list_instance_groups(
            cluster_id='j-123')

        self.assert_request_parameters({
            'Action': 'ListInstanceGroups',
            'ClusterId': 'j-123',
            'Version': '2009-03-31'
        })

        self.assertTrue(isinstance(response, InstanceGroupList))
        self.assertEqual(len(response.instancegroups), 2)
        self.assertTrue(
            isinstance(response.instancegroups[0], InstanceGroupInfo))
        self.assertEqual(response.instancegroups[0].id, 'ig-aaaaaaaaaaaaa')
        self.assertEqual(
            response.instancegroups[0].instancegrouptype, "MASTER")
        self.assertEqual(response.instancegroups[0].instancetype, "m1.large")
        self.assertEqual(response.instancegroups[0].market, "ON_DEMAND")
        self.assertEqual(
            response.instancegroups[0].name, "Master instance group")
        self.assertEqual(
            response.instancegroups[0].requestedinstancecount, '1')
        self.assertEqual(response.instancegroups[0].runninginstancecount, '0')
        self.assertTrue(
            isinstance(response.instancegroups[0].status, ClusterStatus))
        self.assertEqual(response.instancegroups[0].status.state, 'TERMINATED')
        # status.statechangereason is not parsed into an object
        #self.assertEqual(response.instancegroups[0].status.statechangereason.code, 'CLUSTER_TERMINATED')


class TestListInstances(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""
<ListInstancesResponse xmlns="http://elasticmapreduce.amazonaws.com/doc/2009-03-31">
  <ListInstancesResult>
    <Instances>
      <member>
        <Id>ci-123456789abc</Id>
        <Status>
          <StateChangeReason>
            <Message>Cluster was terminated.</Message>
            <Code>CLUSTER_TERMINATED</Code>
          </StateChangeReason>
          <State>TERMINATED</State>
          <Timeline>
            <CreationDateTime>2014-01-24T01:21:26Z</CreationDateTime>
            <ReadyDateTime>2014-01-24T01:25:25Z</ReadyDateTime>
            <EndDateTime>2014-01-24T02:19:46Z</EndDateTime>
          </Timeline>
        </Status>
        <PrivateDnsName>ip-10-0-0-60.us-west-1.compute.internal</PrivateDnsName>
        <PublicIpAddress>54.0.0.1</PublicIpAddress>
        <PublicDnsName>ec2-54-0-0-1.us-west-1.compute.amazonaws.com</PublicDnsName>
        <Ec2InstanceId>i-aaaaaaaa</Ec2InstanceId>
        <PrivateIpAddress>10.0.0.60</PrivateIpAddress>
      </member>
      <member>
        <Id>ci-123456789abd</Id>
        <Status>
          <StateChangeReason>
            <Message>Cluster was terminated.</Message>
            <Code>CLUSTER_TERMINATED</Code>
          </StateChangeReason>
          <State>TERMINATED</State>
          <Timeline>
            <CreationDateTime>2014-01-24T01:21:26Z</CreationDateTime>
            <ReadyDateTime>2014-01-24T01:25:25Z</ReadyDateTime>
            <EndDateTime>2014-01-24T02:19:46Z</EndDateTime>
          </Timeline>
        </Status>
        <PrivateDnsName>ip-10-0-0-61.us-west-1.compute.internal</PrivateDnsName>
        <PublicIpAddress>54.0.0.2</PublicIpAddress>
        <PublicDnsName>ec2-54-0-0-2.us-west-1.compute.amazonaws.com</PublicDnsName>
        <Ec2InstanceId>i-aaaaaaab</Ec2InstanceId>
        <PrivateIpAddress>10.0.0.61</PrivateIpAddress>
      </member>
      <member>
        <Id>ci-123456789abe3</Id>
        <Status>
          <StateChangeReason>
            <Message>Cluster was terminated.</Message>
            <Code>CLUSTER_TERMINATED</Code>
          </StateChangeReason>
          <State>TERMINATED</State>
          <Timeline>
            <CreationDateTime>2014-01-24T01:21:33Z</CreationDateTime>
            <ReadyDateTime>2014-01-24T01:25:08Z</ReadyDateTime>
            <EndDateTime>2014-01-24T02:19:46Z</EndDateTime>
          </Timeline>
        </Status>
        <PrivateDnsName>ip-10-0-0-62.us-west-1.compute.internal</PrivateDnsName>
        <PublicIpAddress>54.0.0.3</PublicIpAddress>
        <PublicDnsName>ec2-54-0-0-3.us-west-1.compute.amazonaws.com</PublicDnsName>
        <Ec2InstanceId>i-aaaaaaac</Ec2InstanceId>
        <PrivateIpAddress>10.0.0.62</PrivateIpAddress>
      </member>
    </Instances>
  </ListInstancesResult>
  <ResponseMetadata>
    <RequestId>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</RequestId>
  </ResponseMetadata>
</ListInstancesResponse>
        """

    def test_list_instances(self):
        self.set_http_response(200)

        with self.assertRaises(TypeError):
            self.service_connection.list_instances()

        response = self.service_connection.list_instances(cluster_id='j-123')
        self.assertTrue(isinstance(response, InstanceList))
        self.assertEqual(len(response.instances), 3)
        self.assertTrue(isinstance(response.instances[0], InstanceInfo))
        self.assertEqual(response.instances[0].ec2instanceid, 'i-aaaaaaaa')
        self.assertEqual(response.instances[0].id, 'ci-123456789abc')
        self.assertEqual(
            response.instances[0].privatednsname, 'ip-10-0-0-60.us-west-1.compute.internal')
        self.assertEqual(response.instances[0].privateipaddress, '10.0.0.60')
        self.assertEqual(response.instances[
                         0].publicdnsname, 'ec2-54-0-0-1.us-west-1.compute.amazonaws.com')
        self.assertEqual(response.instances[0].publicipaddress, '54.0.0.1')

        self.assert_request_parameters({
            'Action': 'ListInstances',
            'ClusterId': 'j-123',
            'Version': '2009-03-31'
        })

    def test_list_instances_with_group_id(self):
        self.set_http_response(200)
        response = self.service_connection.list_instances(
            cluster_id='j-123', instance_group_id='abc')

        self.assert_request_parameters({
            'Action': 'ListInstances',
            'ClusterId': 'j-123',
            'InstanceGroupId': 'abc',
            'Version': '2009-03-31'
        })

    def test_list_instances_with_types(self):
        self.set_http_response(200)

        response = self.service_connection.list_instances(
            cluster_id='j-123', instance_group_types=[
                'MASTER',
                'TASK'
            ])

        self.assert_request_parameters({
            'Action': 'ListInstances',
            'ClusterId': 'j-123',
            'InstanceGroupTypes.member.1': 'MASTER',
            'InstanceGroupTypes.member.2': 'TASK',
            'Version': '2009-03-31'
        })


class TestListSteps(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""<ListStepsResponse xmlns="http://elasticmapreduce.amazonaws.com/doc/2009-03-31">
  <ListStepsResult>
    <Steps>
      <member>
        <Id>abc123</Id>
        <Status>
          <StateChangeReason/>
          <Timeline>
            <CreationDateTime>2014-07-01T00:00:00.000Z</CreationDateTime>
          </Timeline>
          <State>PENDING</State>
        </Status>
        <Name>Step 1</Name>
        <Config>
          <Jar>/home/hadoop/lib/emr-s3distcp-1.0.jar</Jar>
          <Args>
            <member>--src</member>
            <member>hdfs:///data/test/</member>
            <member>--dest</member>
            <member>s3n://test/data</member>
          </Args>
          <Properties/>
        </Config>
        <ActionOnFailure>CONTINUE</ActionOnFailure>
      </member>
      <member>
        <Id>def456</Id>
        <Status>
          <StateChangeReason/>
          <Timeline>
            <CreationDateTime>2014-07-01T00:00:00.000Z</CreationDateTime>
          </Timeline>
          <State>COMPLETED</State>
        </Status>
        <Name>Step 2</Name>
        <Config>
          <MainClass>my.main.SomeClass</MainClass>
          <Jar>s3n://test/jars/foo.jar</Jar>
        </Config>
        <ActionOnFailure>CONTINUE</ActionOnFailure>
      </member>
      <member>
        <Id>ghi789</Id>
        <Status>
          <StateChangeReason/>
          <Timeline>
            <CreationDateTime>2014-07-01T00:00:00.000Z</CreationDateTime>
          </Timeline>
          <State>FAILED</State>
        </Status>
        <Name>Step 3</Name>
        <Config>
          <Jar>s3n://test/jars/bar.jar</Jar>
          <Args>
            <member>-arg</member>
            <member>value</member>
          </Args>
          <Properties/>
        </Config>
        <ActionOnFailure>TERMINATE_CLUSTER</ActionOnFailure>
      </member>
    </Steps>
  </ListStepsResult>
  <ResponseMetadata>
    <RequestId>eff31ee5-0342-11e4-b3c7-9de5a93f6fcb</RequestId>
  </ResponseMetadata>
</ListStepsResponse>
"""

    def test_list_steps(self):
        self.set_http_response(200)

        with self.assertRaises(TypeError):
            self.service_connection.list_steps()

        response = self.service_connection.list_steps(cluster_id='j-123')

        self.assert_request_parameters({
            'Action': 'ListSteps',
            'ClusterId': 'j-123',
            'Version': '2009-03-31'
        })
        self.assertTrue(isinstance(response, StepSummaryList))
        self.assertEqual(response.steps[0].name, 'Step 1')

        valid_states = [
            'PENDING',
            'RUNNING',
            'COMPLETED',
            'CANCELLED',
            'FAILED',
            'INTERRUPTED'
        ]

        # Check for step states
        for step in response.steps:
            self.assertIn(step.status.state, valid_states)

        # Check for step config
        step = response.steps[0]
        self.assertEqual(step.config.jar,
                         '/home/hadoop/lib/emr-s3distcp-1.0.jar')
        self.assertEqual(len(step.config.args), 4)
        self.assertEqual(step.config.args[0].value, '--src')
        self.assertEqual(step.config.args[1].value, 'hdfs:///data/test/')

        step = response.steps[1]
        self.assertEqual(step.config.mainclass, 'my.main.SomeClass')

    def test_list_steps_with_states(self):
        self.set_http_response(200)
        response = self.service_connection.list_steps(
            cluster_id='j-123', step_states=[
                'COMPLETED',
                'FAILED'
            ])

        self.assert_request_parameters({
            'Action': 'ListSteps',
            'ClusterId': 'j-123',
            'StepStates.member.1': 'COMPLETED',
            'StepStates.member.2': 'FAILED',
            'Version': '2009-03-31'
        })
        self.assertTrue(isinstance(response, StepSummaryList))
        self.assertEqual(response.steps[0].name, 'Step 1')


class TestListBootstrapActions(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""<ListBootstrapActionsOutput></ListBootstrapActionsOutput>"""

    def test_list_bootstrap_actions(self):
        self.set_http_response(200)

        with self.assertRaises(TypeError):
            self.service_connection.list_bootstrap_actions()

        response = self.service_connection.list_bootstrap_actions(
            cluster_id='j-123')

        self.assert_request_parameters({
            'Action': 'ListBootstrapActions',
            'ClusterId': 'j-123',
            'Version': '2009-03-31'
        })


class TestDescribeCluster(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""
<DescribeClusterResponse xmlns="http://elasticmapreduce.amazonaws.com/doc/2009-03-31">
  <DescribeClusterResult>
    <Cluster>
      <Id>j-aaaaaaaaa</Id>
      <Tags/>
      <Ec2InstanceAttributes>
        <Ec2AvailabilityZone>us-west-1c</Ec2AvailabilityZone>
        <Ec2KeyName>my_secret_key</Ec2KeyName>
      </Ec2InstanceAttributes>
      <RunningAmiVersion>2.4.2</RunningAmiVersion>
      <VisibleToAllUsers>true</VisibleToAllUsers>
      <Status>
        <StateChangeReason>
          <Message>Terminated by user request</Message>
          <Code>USER_REQUEST</Code>
        </StateChangeReason>
        <State>TERMINATED</State>
        <Timeline>
          <CreationDateTime>2014-01-24T01:21:21Z</CreationDateTime>
          <ReadyDateTime>2014-01-24T01:25:26Z</ReadyDateTime>
          <EndDateTime>2014-01-24T02:19:46Z</EndDateTime>
        </Timeline>
      </Status>
      <AutoTerminate>false</AutoTerminate>
      <Name>test analytics</Name>
      <RequestedAmiVersion>2.4.2</RequestedAmiVersion>
      <Applications>
        <member>
          <Name>hadoop</Name>
          <Version>1.0.3</Version>
        </member>
      </Applications>
      <TerminationProtected>false</TerminationProtected>
      <MasterPublicDnsName>ec2-184-0-0-1.us-west-1.compute.amazonaws.com</MasterPublicDnsName>
      <NormalizedInstanceHours>10</NormalizedInstanceHours>
      <ServiceRole>my-service-role</ServiceRole>
    </Cluster>
  </DescribeClusterResult>
  <ResponseMetadata>
    <RequestId>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</RequestId>
  </ResponseMetadata>
</DescribeClusterResponse>
        """

    def test_describe_cluster(self):
        self.set_http_response(200)

        with self.assertRaises(TypeError):
            self.service_connection.describe_cluster()

        response = self.service_connection.describe_cluster(cluster_id='j-123')

        self.assertTrue(isinstance(response, Cluster))
        self.assertEqual(response.id, 'j-aaaaaaaaa')
        self.assertEqual(response.runningamiversion, '2.4.2')
        self.assertEqual(response.visibletoallusers, 'true')
        self.assertEqual(response.autoterminate, 'false')
        self.assertEqual(response.name, 'test analytics')
        self.assertEqual(response.requestedamiversion, '2.4.2')
        self.assertEqual(response.terminationprotected, 'false')
        self.assertEqual(
            response.ec2instanceattributes.ec2availabilityzone, "us-west-1c")
        self.assertEqual(
            response.ec2instanceattributes.ec2keyname, 'my_secret_key')
        self.assertEqual(response.status.state, 'TERMINATED')
        self.assertEqual(response.applications[0].name, 'hadoop')
        self.assertEqual(response.applications[0].version, '1.0.3')
        self.assertEqual(
            response.masterpublicdnsname, 'ec2-184-0-0-1.us-west-1.compute.amazonaws.com')
        self.assertEqual(response.normalizedinstancehours, '10')
        self.assertEqual(response.servicerole, 'my-service-role')

        self.assert_request_parameters({
            'Action': 'DescribeCluster',
            'ClusterId': 'j-123',
            'Version': '2009-03-31'
        })


class TestDescribeStep(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""<DescribeStepOutput></DescribeStepOutput>"""

    def test_describe_step(self):
        self.set_http_response(200)

        with self.assertRaises(TypeError):
            self.service_connection.describe_step()

        with self.assertRaises(TypeError):
            self.service_connection.describe_step(cluster_id='j-123')

        with self.assertRaises(TypeError):
            self.service_connection.describe_step(step_id='abc')

        response = self.service_connection.describe_step(
            cluster_id='j-123', step_id='abc')

        self.assert_request_parameters({
            'Action': 'DescribeStep',
            'ClusterId': 'j-123',
            'StepId': 'abc',
            'Version': '2009-03-31'
        })


class TestAddJobFlowSteps(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""
<AddJobFlowStepsOutput>
    <StepIds>
        <member>Foo</member>
        <member>Bar</member>
    </StepIds>
</AddJobFlowStepsOutput>
"""

    def test_add_jobflow_steps(self):
        self.set_http_response(200)

        response = self.service_connection.add_jobflow_steps(
            jobflow_id='j-123', steps=[])

        # Make sure the correct object is returned, as this was
        # previously set to incorrectly return an empty instance
        # of RunJobFlowResponse.
        self.assertTrue(isinstance(response, JobFlowStepList))
        self.assertEqual(response.stepids[0].value, 'Foo')
        self.assertEqual(response.stepids[1].value, 'Bar')


class TestBuildTagList(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def test_key_without_value_encoding(self):
        input_dict = {
            'KeyWithNoValue': '',
            'AnotherKeyWithNoValue': None
        }
        res = self.service_connection._build_tag_list(input_dict)
        # Keys are outputted in ascending key order.
        expected = {
            'Tags.member.1.Key': 'AnotherKeyWithNoValue',
            'Tags.member.2.Key': 'KeyWithNoValue'
        }
        self.assertEqual(expected, res)

    def test_key_full_key_value_encoding(self):
        input_dict = {
            'FirstKey': 'One',
            'SecondKey': 'Two'
        }
        res = self.service_connection._build_tag_list(input_dict)
        # Keys are outputted in ascending key order.
        expected = {
            'Tags.member.1.Key': 'FirstKey',
            'Tags.member.1.Value': 'One',
            'Tags.member.2.Key': 'SecondKey',
            'Tags.member.2.Value': 'Two'
        }
        self.assertEqual(expected, res)


class TestAddTag(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""<AddTagsResponse
               xmlns="http://elasticmapreduce.amazonaws.com/doc/2009-03-31">
                   <AddTagsResult/>
                   <ResponseMetadata>
                        <RequestId>88888888-8888-8888-8888-888888888888</RequestId>
                   </ResponseMetadata>
               </AddTagsResponse>
               """

    def test_add_mix_of_tags_with_without_values(self):
        input_tags = {
            'FirstKey': 'One',
            'SecondKey': 'Two',
            'ZzzNoValue': ''
        }
        self.set_http_response(200)

        with self.assertRaises(TypeError):
            self.service_connection.add_tags()

        with self.assertRaises(TypeError):
            self.service_connection.add_tags('j-123')

        with self.assertRaises(AssertionError):
            self.service_connection.add_tags('j-123', [])

        response = self.service_connection.add_tags('j-123', input_tags)

        self.assertTrue(response)
        self.assert_request_parameters({
            'Action': 'AddTags',
            'ResourceId': 'j-123',
            'Tags.member.1.Key': 'FirstKey',
            'Tags.member.1.Value': 'One',
            'Tags.member.2.Key': 'SecondKey',
            'Tags.member.2.Value': 'Two',
            'Tags.member.3.Key': 'ZzzNoValue',
            'Version': '2009-03-31'
        })


class TestRemoveTag(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""<RemoveTagsResponse
               xmlns="http://elasticmapreduce.amazonaws.com/doc/2009-03-31">
                   <RemoveTagsResult/>
                   <ResponseMetadata>
                        <RequestId>88888888-8888-8888-8888-888888888888</RequestId>
                   </ResponseMetadata>
               </RemoveTagsResponse>
               """

    def test_remove_tags(self):
        input_tags = {
            'FirstKey': 'One',
            'SecondKey': 'Two',
            'ZzzNoValue': ''
        }
        self.set_http_response(200)

        with self.assertRaises(TypeError):
            self.service_connection.add_tags()

        with self.assertRaises(TypeError):
            self.service_connection.add_tags('j-123')

        with self.assertRaises(AssertionError):
            self.service_connection.add_tags('j-123', [])

        response = self.service_connection.remove_tags(
            'j-123', ['FirstKey', 'SecondKey'])

        self.assertTrue(response)
        self.assert_request_parameters({
            'Action': 'RemoveTags',
            'ResourceId': 'j-123',
            'TagKeys.member.1': 'FirstKey',
            'TagKeys.member.2': 'SecondKey',
            'Version': '2009-03-31'
        })


class DescribeJobFlowsTestBase(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""
<DescribeJobFlowsResponse xmlns="http://elasticmapreduce.amazonaws.com/doc/2009-03-31">
  <DescribeJobFlowsResult>
    <JobFlows>
      <member>
        <AmiVersion>2.4.2</AmiVersion>
        <ExecutionStatusDetail>
          <CreationDateTime>2014-01-24T01:21:21Z</CreationDateTime>
          <LastStateChangeReason>Terminated by user request</LastStateChangeReason>
          <StartDateTime>2014-01-24T01:25:26Z</StartDateTime>
          <ReadyDateTime>2014-01-24T01:25:26Z</ReadyDateTime>
          <State>TERMINATED</State>
          <EndDateTime>2014-01-24T02:19:46Z</EndDateTime>
        </ExecutionStatusDetail>
        <BootstrapActions/>
        <VisibleToAllUsers>true</VisibleToAllUsers>
        <SupportedProducts/>
        <Name>test analytics</Name>
        <JobFlowId>j-aaaaaa</JobFlowId>
        <Steps>
          <member>
            <ExecutionStatusDetail>
              <CreationDateTime>2014-01-24T01:21:21Z</CreationDateTime>
              <StartDateTime>2014-01-24T01:25:26Z</StartDateTime>
              <State>COMPLETED</State>
              <EndDateTime>2014-01-24T01:26:08Z</EndDateTime>
            </ExecutionStatusDetail>
            <StepConfig>
              <HadoopJarStep>
                <Args>
                  <member>s3://us-west-1.elasticmapreduce/libs/hive/hive-script</member>
                  <member>--base-path</member>
                  <member>s3://us-west-1.elasticmapreduce/libs/hive/</member>
                  <member>--install-hive</member>
                  <member>--hive-versions</member>
                  <member>0.11.0.1</member>
                </Args>
                <Jar>s3://us-west-1.elasticmapreduce/libs/script-runner/script-runner.jar</Jar>
                <Properties/>
              </HadoopJarStep>
              <Name>Setup hive</Name>
              <ActionOnFailure>TERMINATE_JOB_FLOW</ActionOnFailure>
            </StepConfig>
          </member>
        </Steps>
        <Instances>
          <Placement>
            <AvailabilityZone>us-west-1c</AvailabilityZone>
          </Placement>
          <MasterInstanceType>m1.large</MasterInstanceType>
          <Ec2KeyName>my_key</Ec2KeyName>
          <KeepJobFlowAliveWhenNoSteps>true</KeepJobFlowAliveWhenNoSteps>
          <InstanceGroups>
            <member>
              <CreationDateTime>2014-01-24T01:21:21Z</CreationDateTime>
              <InstanceRunningCount>0</InstanceRunningCount>
              <StartDateTime>2014-01-24T01:23:56Z</StartDateTime>
              <ReadyDateTime>2014-01-24T01:25:08Z</ReadyDateTime>
              <State>ENDED</State>
              <EndDateTime>2014-01-24T02:19:46Z</EndDateTime>
              <InstanceRequestCount>1</InstanceRequestCount>
              <InstanceType>m1.large</InstanceType>
              <LastStateChangeReason>Job flow terminated</LastStateChangeReason>
              <Market>ON_DEMAND</Market>
              <InstanceGroupId>ig-aaaaaa</InstanceGroupId>
              <InstanceRole>MASTER</InstanceRole>
              <Name>Master instance group</Name>
            </member>
            <member>
              <CreationDateTime>2014-01-24T01:21:21Z</CreationDateTime>
              <InstanceRunningCount>0</InstanceRunningCount>
              <StartDateTime>2014-01-24T01:25:26Z</StartDateTime>
              <ReadyDateTime>2014-01-24T01:25:26Z</ReadyDateTime>
              <State>ENDED</State>
              <EndDateTime>2014-01-24T02:19:46Z</EndDateTime>
              <InstanceRequestCount>2</InstanceRequestCount>
              <InstanceType>m1.large</InstanceType>
              <LastStateChangeReason>Job flow terminated</LastStateChangeReason>
              <Market>ON_DEMAND</Market>
              <InstanceGroupId>ig-aaaaab</InstanceGroupId>
              <InstanceRole>CORE</InstanceRole>
              <Name>Core instance group</Name>
            </member>
          </InstanceGroups>
          <SlaveInstanceType>m1.large</SlaveInstanceType>
          <MasterInstanceId>i-aaaaaa</MasterInstanceId>
          <HadoopVersion>1.0.3</HadoopVersion>
          <NormalizedInstanceHours>12</NormalizedInstanceHours>
          <MasterPublicDnsName>ec2-184-0-0-1.us-west-1.compute.amazonaws.com</MasterPublicDnsName>
          <InstanceCount>3</InstanceCount>
          <TerminationProtected>false</TerminationProtected>
        </Instances>
      </member>
    </JobFlows>
  </DescribeJobFlowsResult>
  <ResponseMetadata>
    <RequestId>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</RequestId>
  </ResponseMetadata>
</DescribeJobFlowsResponse>
        """


class TestDescribeJobFlows(DescribeJobFlowsTestBase):

    def test_describe_jobflows_response(self):
        self.set_http_response(200)

        response = self.service_connection.describe_jobflows()
        self.assertTrue(isinstance(response, list))

        jf = response[0]
        self.assertTrue(isinstance(jf, JobFlow))
        self.assertEqual(jf.amiversion, '2.4.2')
        self.assertEqual(jf.visibletoallusers, 'true')
        self.assertEqual(jf.name, 'test analytics')
        self.assertEqual(jf.jobflowid, 'j-aaaaaa')
        self.assertEqual(jf.ec2keyname, 'my_key')
        self.assertEqual(jf.masterinstancetype, 'm1.large')
        self.assertEqual(jf.availabilityzone, 'us-west-1c')
        self.assertEqual(jf.keepjobflowalivewhennosteps, 'true')
        self.assertEqual(jf.slaveinstancetype, 'm1.large')
        self.assertEqual(jf.masterinstanceid, 'i-aaaaaa')
        self.assertEqual(jf.hadoopversion, '1.0.3')
        self.assertEqual(jf.normalizedinstancehours, '12')
        self.assertEqual(
            jf.masterpublicdnsname, 'ec2-184-0-0-1.us-west-1.compute.amazonaws.com')
        self.assertEqual(jf.instancecount, '3')
        self.assertEqual(jf.terminationprotected, 'false')

        self.assertTrue(isinstance(jf.steps, list))
        step = jf.steps[0]
        self.assertTrue(isinstance(step, Step))
        self.assertEqual(
            step.jar, 's3://us-west-1.elasticmapreduce/libs/script-runner/script-runner.jar')
        self.assertEqual(step.name, 'Setup hive')
        self.assertEqual(step.actiononfailure, 'TERMINATE_JOB_FLOW')

        self.assertTrue(isinstance(jf.instancegroups, list))
        ig = jf.instancegroups[0]
        self.assertTrue(isinstance(ig, InstanceGroup))
        self.assertEqual(ig.creationdatetime, '2014-01-24T01:21:21Z')
        self.assertEqual(ig.state, 'ENDED')
        self.assertEqual(ig.instancerequestcount, '1')
        self.assertEqual(ig.instancetype, 'm1.large')
        self.assertEqual(ig.laststatechangereason, 'Job flow terminated')
        self.assertEqual(ig.market, 'ON_DEMAND')
        self.assertEqual(ig.instancegroupid, 'ig-aaaaaa')
        self.assertEqual(ig.instancerole, 'MASTER')
        self.assertEqual(ig.name, 'Master instance group')

    def test_describe_jobflows_no_args(self):
        self.set_http_response(200)

        self.service_connection.describe_jobflows()

        self.assert_request_parameters({
            'Action': 'DescribeJobFlows',
        }, ignore_params_values=['Version'])

    def test_describe_jobflows_filtered(self):
        self.set_http_response(200)

        now = datetime.now()
        a_bit_before = datetime.fromtimestamp(time() - 1000)

        self.service_connection.describe_jobflows(states=['WAITING', 'RUNNING'], jobflow_ids=[
                                                  'j-aaaaaa', 'j-aaaaab'], created_after=a_bit_before, created_before=now)
        self.assert_request_parameters({
            'Action': 'DescribeJobFlows',
            'JobFlowIds.member.1': 'j-aaaaaa',
            'JobFlowIds.member.2': 'j-aaaaab',
            'JobFlowStates.member.1': 'WAITING',
            'JobFlowStates.member.2': 'RUNNING',
            'CreatedAfter': a_bit_before.strftime(boto.utils.ISO8601),
            'CreatedBefore': now.strftime(boto.utils.ISO8601),
        }, ignore_params_values=['Version'])


class TestDescribeJobFlow(DescribeJobFlowsTestBase):

    def test_describe_jobflow(self):
        self.set_http_response(200)

        response = self.service_connection.describe_jobflow('j-aaaaaa')
        self.assertTrue(isinstance(response, JobFlow))
        self.assert_request_parameters({
            'Action': 'DescribeJobFlows',
            'JobFlowIds.member.1': 'j-aaaaaa',
        }, ignore_params_values=['Version'])


class TestRunJobFlow(AWSMockServiceTestCase):
    connection_class = EmrConnection

    def default_body(self):
        return b"""
<RunJobFlowResponse xmlns="http://elasticmapreduce.amazonaws.com/doc/2009-03-31">
  <RunJobFlowResult>
    <JobFlowId>j-ZKIY4CKQRX72</JobFlowId>
  </RunJobFlowResult>
  <ResponseMetadata>
    <RequestId>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</RequestId>
  </ResponseMetadata>
</RunJobFlowResponse>
"""

    def test_run_jobflow_service_role(self):
        self.set_http_response(200)

        response = self.service_connection.run_jobflow(
            'EmrCluster', service_role='EMR_DefaultRole')

        self.assertTrue(response)
        self.assert_request_parameters({
            'Action': 'RunJobFlow',
            'Version': '2009-03-31',
            'ServiceRole': 'EMR_DefaultRole',
            'Name': 'EmrCluster'},
            ignore_params_values=['ActionOnFailure', 'Instances.InstanceCount',
                                  'Instances.KeepJobFlowAliveWhenNoSteps',
                                  'Instances.MasterInstanceType',
                                  'Instances.SlaveInstanceType'])

    def test_run_jobflow_enable_debugging(self):
        self.region = 'ap-northeast-2'
        self.set_http_response(200)
        self.service_connection.run_jobflow(
            'EmrCluster', enable_debugging=True)

        actual_params = set(self.actual_request.params.copy().items())

        expected_params = set([
            ('Steps.member.1.HadoopJarStep.Jar',
             's3://ap-northeast-2.elasticmapreduce/libs/script-runner/script-runner.jar'),
            ('Steps.member.1.HadoopJarStep.Args.member.1',
                's3://ap-northeast-2.elasticmapreduce/libs/state-pusher/0.1/fetch'),
        ])

        self.assertTrue(expected_params <= actual_params)
