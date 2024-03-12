#!/usr/bin/env python
import unittest
from datetime import datetime
from mock import Mock

from tests.unit import AWSMockServiceTestCase
from boto.cloudformation.connection import CloudFormationConnection
from boto.exception import BotoServerError
from boto.compat import json

SAMPLE_TEMPLATE = r"""
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Sample template",
  "Parameters" : {
    "KeyName" : {
      "Description" : "key pair",
      "Type" : "String"
    }
  },
  "Resources" : {
    "Ec2Instance" : {
      "Type" : "AWS::EC2::Instance",
      "Properties" : {
        "KeyName" : { "Ref" : "KeyName" },
        "ImageId" : "ami-7f418316",
        "UserData" : { "Fn::Base64" : "80" }
      }
    }
  },
  "Outputs" : {
    "InstanceId" : {
      "Description" : "InstanceId of the newly created EC2 instance",
      "Value" : { "Ref" : "Ec2Instance" }
    }
}
"""

class CloudFormationConnectionBase(AWSMockServiceTestCase):
    connection_class = CloudFormationConnection

    def setUp(self):
        super(CloudFormationConnectionBase, self).setUp()
        self.stack_id = u'arn:aws:cloudformation:us-east-1:18:stack/Name/id'


class TestCloudFormationCreateStack(CloudFormationConnectionBase):
    def default_body(self):
        return json.dumps(
            {u'CreateStackResponse':
                 {u'CreateStackResult': {u'StackId': self.stack_id},
                  u'ResponseMetadata': {u'RequestId': u'1'}}}).encode('utf-8')

    def test_create_stack_has_correct_request_params(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_stack(
            'stack_name', template_url='http://url',
            template_body=SAMPLE_TEMPLATE,
            parameters=[('KeyName', 'myKeyName')],
            tags={'TagKey': 'TagValue'},
            notification_arns=['arn:notify1', 'arn:notify2'],
            disable_rollback=True,
            timeout_in_minutes=20, capabilities=['CAPABILITY_IAM']
        )
        self.assertEqual(api_response, self.stack_id)
        # These are the parameters that are actually sent to the CloudFormation
        # service.
        self.assert_request_parameters({
            'Action': 'CreateStack',
            'Capabilities.member.1': 'CAPABILITY_IAM',
            'ContentType': 'JSON',
            'DisableRollback': 'true',
            'NotificationARNs.member.1': 'arn:notify1',
            'NotificationARNs.member.2': 'arn:notify2',
            'Parameters.member.1.ParameterKey': 'KeyName',
            'Parameters.member.1.ParameterValue': 'myKeyName',
            'Tags.member.1.Key': 'TagKey',
            'Tags.member.1.Value': 'TagValue',
            'StackName': 'stack_name',
            'Version': '2010-05-15',
            'TimeoutInMinutes': 20,
            'TemplateBody': SAMPLE_TEMPLATE,
            'TemplateURL': 'http://url',
        })

    # The test_create_stack_has_correct_request_params verified all of the
    # params needed when making a create_stack service call.  The rest of the
    # tests for create_stack only verify specific parts of the params sent
    # to CloudFormation.

    def test_create_stack_with_minimum_args(self):
        # This will fail in practice, but the API docs only require stack_name.
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_stack('stack_name')
        self.assertEqual(api_response, self.stack_id)
        self.assert_request_parameters({
            'Action': 'CreateStack',
            'ContentType': 'JSON',
            'DisableRollback': 'false',
            'StackName': 'stack_name',
            'Version': '2010-05-15',
        })

    def test_create_stack_fails(self):
        self.set_http_response(status_code=400, reason='Bad Request',
            body=b'{"Error": {"Code": 1, "Message": "Invalid arg."}}')
        with self.assertRaisesRegexp(self.service_connection.ResponseError,
            'Invalid arg.'):
            api_response = self.service_connection.create_stack(
                'stack_name', template_body=SAMPLE_TEMPLATE,
                parameters=[('KeyName', 'myKeyName')])

    def test_create_stack_fail_error(self):
        self.set_http_response(status_code=400, reason='Bad Request',
            body=b'{"RequestId": "abc", "Error": {"Code": 1, "Message": "Invalid arg."}}')
        try:
            api_response = self.service_connection.create_stack(
                'stack_name', template_body=SAMPLE_TEMPLATE,
                parameters=[('KeyName', 'myKeyName')])
        except BotoServerError as e:
            self.assertEqual('abc', e.request_id)
            self.assertEqual(1, e.error_code)
            self.assertEqual('Invalid arg.', e.message)

class TestCloudFormationUpdateStack(CloudFormationConnectionBase):
    def default_body(self):
        return json.dumps(
            {u'UpdateStackResponse':
                 {u'UpdateStackResult': {u'StackId': self.stack_id},
                  u'ResponseMetadata': {u'RequestId': u'1'}}}).encode('utf-8')

    def test_update_stack_all_args(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.update_stack(
            'stack_name', template_url='http://url',
            template_body=SAMPLE_TEMPLATE,
            parameters=[('KeyName', 'myKeyName'), ('KeyName2', "", True),
                        ('KeyName3', "", False), ('KeyName4', None, True),
                        ('KeyName5', "Ignore Me", True)],
            tags={'TagKey': 'TagValue'},
            notification_arns=['arn:notify1', 'arn:notify2'],
            disable_rollback=True,
            timeout_in_minutes=20,
            use_previous_template=True
        )
        self.assert_request_parameters({
            'Action': 'UpdateStack',
            'ContentType': 'JSON',
            'DisableRollback': 'true',
            'NotificationARNs.member.1': 'arn:notify1',
            'NotificationARNs.member.2': 'arn:notify2',
            'Parameters.member.1.ParameterKey': 'KeyName',
            'Parameters.member.1.ParameterValue': 'myKeyName',
            'Parameters.member.2.ParameterKey': 'KeyName2',
            'Parameters.member.2.UsePreviousValue': 'true',
            'Parameters.member.3.ParameterKey': 'KeyName3',
            'Parameters.member.3.ParameterValue': '',
            'Parameters.member.4.UsePreviousValue': 'true',
            'Parameters.member.4.ParameterKey': 'KeyName4',
            'Parameters.member.5.UsePreviousValue': 'true',
            'Parameters.member.5.ParameterKey': 'KeyName5',
            'Tags.member.1.Key': 'TagKey',
            'Tags.member.1.Value': 'TagValue',
            'StackName': 'stack_name',
            'Version': '2010-05-15',
            'TimeoutInMinutes': 20,
            'TemplateBody': SAMPLE_TEMPLATE,
            'TemplateURL': 'http://url',
            'UsePreviousTemplate': 'true',
        })

    def test_update_stack_with_minimum_args(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.update_stack('stack_name')
        self.assertEqual(api_response, self.stack_id)
        self.assert_request_parameters({
            'Action': 'UpdateStack',
            'ContentType': 'JSON',
            'DisableRollback': 'false',
            'StackName': 'stack_name',
            'Version': '2010-05-15',
        })

    def test_update_stack_fails(self):
        self.set_http_response(status_code=400, reason='Bad Request',
                               body=b'Invalid arg.')
        with self.assertRaises(self.service_connection.ResponseError):
            api_response = self.service_connection.update_stack(
                'stack_name', template_body=SAMPLE_TEMPLATE,
                parameters=[('KeyName', 'myKeyName')])


class TestCloudFormationDeleteStack(CloudFormationConnectionBase):
    def default_body(self):
        return json.dumps(
            {u'DeleteStackResponse':
                 {u'ResponseMetadata': {u'RequestId': u'1'}}}).encode('utf-8')

    def test_delete_stack(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_stack('stack_name')
        self.assertEqual(api_response, json.loads(self.default_body().decode('utf-8')))
        self.assert_request_parameters({
            'Action': 'DeleteStack',
            'ContentType': 'JSON',
            'StackName': 'stack_name',
            'Version': '2010-05-15',
        })

    def test_delete_stack_fails(self):
        self.set_http_response(status_code=400)
        with self.assertRaises(self.service_connection.ResponseError):
            api_response = self.service_connection.delete_stack('stack_name')


class TestCloudFormationDescribeStackResource(CloudFormationConnectionBase):
    def default_body(self):
        return json.dumps('fake server response').encode('utf-8')

    def test_describe_stack_resource(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.describe_stack_resource(
            'stack_name', 'resource_id')
        self.assertEqual(api_response, 'fake server response')
        self.assert_request_parameters({
            'Action': 'DescribeStackResource',
            'ContentType': 'JSON',
            'LogicalResourceId': 'resource_id',
            'StackName': 'stack_name',
            'Version': '2010-05-15',
        })

    def test_describe_stack_resource_fails(self):
        self.set_http_response(status_code=400)
        with self.assertRaises(self.service_connection.ResponseError):
            api_response = self.service_connection.describe_stack_resource(
                'stack_name', 'resource_id')


class TestCloudFormationGetTemplate(CloudFormationConnectionBase):
    def default_body(self):
        return json.dumps('fake server response').encode('utf-8')

    def test_get_template(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.get_template('stack_name')
        self.assertEqual(api_response, 'fake server response')
        self.assert_request_parameters({
            'Action': 'GetTemplate',
            'ContentType': 'JSON',
            'StackName': 'stack_name',
            'Version': '2010-05-15',
        })


    def test_get_template_fails(self):
        self.set_http_response(status_code=400)
        with self.assertRaises(self.service_connection.ResponseError):
            api_response = self.service_connection.get_template('stack_name')


class TestCloudFormationGetStackevents(CloudFormationConnectionBase):
    def default_body(self):
        return b"""
            <DescribeStackEventsResult>
              <StackEvents>
                <member>
                  <EventId>Event-1-Id</EventId>
                  <StackId>arn:aws:cfn:us-east-1:1:stack</StackId>
                  <StackName>MyStack</StackName>
                  <LogicalResourceId>MyStack</LogicalResourceId>
                  <PhysicalResourceId>MyStack_One</PhysicalResourceId>
                  <ResourceType>AWS::CloudFormation::Stack</ResourceType>
                  <Timestamp>2010-07-27T22:26:28Z</Timestamp>
                  <ResourceStatus>CREATE_IN_PROGRESS</ResourceStatus>
                  <ResourceStatusReason>User initiated</ResourceStatusReason>
                </member>
                <member>
                  <EventId>Event-2-Id</EventId>
                  <StackId>arn:aws:cfn:us-east-1:1:stack</StackId>
                  <StackName>MyStack</StackName>
                  <LogicalResourceId>MySG1</LogicalResourceId>
                  <PhysicalResourceId>MyStack_SG1</PhysicalResourceId>
                  <ResourceType>AWS::SecurityGroup</ResourceType>
                  <Timestamp>2010-07-27T22:28:28Z</Timestamp>
                  <ResourceStatus>CREATE_COMPLETE</ResourceStatus>
                </member>
              </StackEvents>
            </DescribeStackEventsResult>
        """

    def test_describe_stack_events(self):
        self.set_http_response(status_code=200)
        first, second = self.service_connection.describe_stack_events('stack_name', next_token='next_token')
        self.assertEqual(first.event_id, 'Event-1-Id')
        self.assertEqual(first.logical_resource_id, 'MyStack')
        self.assertEqual(first.physical_resource_id, 'MyStack_One')
        self.assertEqual(first.resource_properties, None)
        self.assertEqual(first.resource_status, 'CREATE_IN_PROGRESS')
        self.assertEqual(first.resource_status_reason, 'User initiated')
        self.assertEqual(first.resource_type, 'AWS::CloudFormation::Stack')
        self.assertEqual(first.stack_id, 'arn:aws:cfn:us-east-1:1:stack')
        self.assertEqual(first.stack_name, 'MyStack')
        self.assertIsNotNone(first.timestamp)

        self.assertEqual(second.event_id, 'Event-2-Id')
        self.assertEqual(second.logical_resource_id, 'MySG1')
        self.assertEqual(second.physical_resource_id, 'MyStack_SG1')
        self.assertEqual(second.resource_properties, None)
        self.assertEqual(second.resource_status, 'CREATE_COMPLETE')
        self.assertEqual(second.resource_status_reason, None)
        self.assertEqual(second.resource_type, 'AWS::SecurityGroup')
        self.assertEqual(second.stack_id, 'arn:aws:cfn:us-east-1:1:stack')
        self.assertEqual(second.stack_name, 'MyStack')
        self.assertIsNotNone(second.timestamp)

        self.assert_request_parameters({
            'Action': 'DescribeStackEvents',
            'NextToken': 'next_token',
            'StackName': 'stack_name',
            'Version': '2010-05-15',
        })


class TestCloudFormationDescribeStackResources(CloudFormationConnectionBase):
    def default_body(self):
        return b"""
            <DescribeStackResourcesResult>
              <StackResources>
                <member>
                  <StackId>arn:aws:cfn:us-east-1:1:stack</StackId>
                  <StackName>MyStack</StackName>
                  <LogicalResourceId>MyDBInstance</LogicalResourceId>
                  <PhysicalResourceId>MyStack_DB1</PhysicalResourceId>
                  <ResourceType>AWS::DBInstance</ResourceType>
                  <Timestamp>2010-07-27T22:27:28Z</Timestamp>
                  <ResourceStatus>CREATE_COMPLETE</ResourceStatus>
                </member>
                <member>
                  <StackId>arn:aws:cfn:us-east-1:1:stack</StackId>
                  <StackName>MyStack</StackName>
                  <LogicalResourceId>MyAutoScalingGroup</LogicalResourceId>
                  <PhysicalResourceId>MyStack_ASG1</PhysicalResourceId>
                  <ResourceType>AWS::AutoScalingGroup</ResourceType>
                  <Timestamp>2010-07-27T22:28:28Z</Timestamp>
                  <ResourceStatus>CREATE_IN_PROGRESS</ResourceStatus>
                </member>
              </StackResources>
            </DescribeStackResourcesResult>
        """

    def test_describe_stack_resources(self):
        self.set_http_response(status_code=200)
        first, second = self.service_connection.describe_stack_resources(
            'stack_name', 'logical_resource_id', 'physical_resource_id')
        self.assertEqual(first.description, None)
        self.assertEqual(first.logical_resource_id, 'MyDBInstance')
        self.assertEqual(first.physical_resource_id, 'MyStack_DB1')
        self.assertEqual(first.resource_status, 'CREATE_COMPLETE')
        self.assertEqual(first.resource_status_reason, None)
        self.assertEqual(first.resource_type, 'AWS::DBInstance')
        self.assertEqual(first.stack_id, 'arn:aws:cfn:us-east-1:1:stack')
        self.assertEqual(first.stack_name, 'MyStack')
        self.assertIsNotNone(first.timestamp)

        self.assertEqual(second.description, None)
        self.assertEqual(second.logical_resource_id, 'MyAutoScalingGroup')
        self.assertEqual(second.physical_resource_id, 'MyStack_ASG1')
        self.assertEqual(second.resource_status, 'CREATE_IN_PROGRESS')
        self.assertEqual(second.resource_status_reason, None)
        self.assertEqual(second.resource_type, 'AWS::AutoScalingGroup')
        self.assertEqual(second.stack_id, 'arn:aws:cfn:us-east-1:1:stack')
        self.assertEqual(second.stack_name, 'MyStack')
        self.assertIsNotNone(second.timestamp)

        self.assert_request_parameters({
            'Action': 'DescribeStackResources',
            'LogicalResourceId': 'logical_resource_id',
            'PhysicalResourceId': 'physical_resource_id',
            'StackName': 'stack_name',
            'Version': '2010-05-15',
        })


class TestCloudFormationDescribeStacks(CloudFormationConnectionBase):
    def default_body(self):
        return b"""
          <DescribeStacksResponse>
            <DescribeStacksResult>
              <Stacks>
                <member>
                  <StackId>arn:aws:cfn:us-east-1:1:stack</StackId>
                  <StackStatus>CREATE_COMPLETE</StackStatus>
                  <StackStatusReason>REASON</StackStatusReason>
                  <StackName>MyStack</StackName>
                  <Description>My Description</Description>
                  <CreationTime>2012-05-16T22:55:31Z</CreationTime>
                  <Capabilities>
                    <member>CAPABILITY_IAM</member>
                  </Capabilities>
                  <NotificationARNs>
                    <member>arn:aws:sns:region-name:account-name:topic-name</member>
                  </NotificationARNs>
                  <DisableRollback>false</DisableRollback>
                  <Parameters>
                    <member>
                      <ParameterValue>MyValue</ParameterValue>
                      <ParameterKey>MyKey</ParameterKey>
                    </member>
                  </Parameters>
                  <Outputs>
                    <member>
                      <OutputValue>http://url/</OutputValue>
                      <Description>Server URL</Description>
                      <OutputKey>ServerURL</OutputKey>
                    </member>
                  </Outputs>
                  <Tags>
                    <member>
                      <Key>MyTagKey</Key>
                      <Value>MyTagValue</Value>
                    </member>
                  </Tags>
                </member>
              </Stacks>
            </DescribeStacksResult>
            <ResponseMetadata>
              <RequestId>12345</RequestId>
            </ResponseMetadata>
        </DescribeStacksResponse>
        """

    def test_describe_stacks(self):
        self.set_http_response(status_code=200)

        stacks = self.service_connection.describe_stacks('MyStack')
        self.assertEqual(len(stacks), 1)

        stack = stacks[0]
        self.assertEqual(stack.creation_time,
                         datetime(2012, 5, 16, 22, 55, 31))
        self.assertEqual(stack.description, 'My Description')
        self.assertEqual(stack.disable_rollback, False)
        self.assertEqual(stack.stack_id, 'arn:aws:cfn:us-east-1:1:stack')
        self.assertEqual(stack.stack_status, 'CREATE_COMPLETE')
        self.assertEqual(stack.stack_name, 'MyStack')
        self.assertEqual(stack.stack_name_reason, 'REASON')
        self.assertEqual(stack.stack_status_reason, 'REASON')
        self.assertEqual(stack.timeout_in_minutes, None)

        self.assertEqual(len(stack.outputs), 1)
        self.assertEqual(stack.outputs[0].description, 'Server URL')
        self.assertEqual(stack.outputs[0].key, 'ServerURL')
        self.assertEqual(stack.outputs[0].value, 'http://url/')

        self.assertEqual(len(stack.parameters), 1)
        self.assertEqual(stack.parameters[0].key, 'MyKey')
        self.assertEqual(stack.parameters[0].value, 'MyValue')

        self.assertEqual(len(stack.capabilities), 1)
        self.assertEqual(stack.capabilities[0].value, 'CAPABILITY_IAM')

        self.assertEqual(len(stack.notification_arns), 1)
        self.assertEqual(stack.notification_arns[0].value, 'arn:aws:sns:region-name:account-name:topic-name')

        self.assertEqual(len(stack.tags), 1)
        self.assertEqual(stack.tags['MyTagKey'], 'MyTagValue')

        self.assert_request_parameters({
            'Action': 'DescribeStacks',
            'StackName': 'MyStack',
            'Version': '2010-05-15',
        })


class TestCloudFormationListStackResources(CloudFormationConnectionBase):
    def default_body(self):
        return b"""
            <ListStackResourcesResponse>
              <ListStackResourcesResult>
                <StackResourceSummaries>
                  <member>
                    <ResourceStatus>CREATE_COMPLETE</ResourceStatus>
                    <LogicalResourceId>SampleDB</LogicalResourceId>
                    <LastUpdatedTime>2011-06-21T20:25:57Z</LastUpdatedTime>
                    <PhysicalResourceId>My-db-ycx</PhysicalResourceId>
                    <ResourceType>AWS::RDS::DBInstance</ResourceType>
                  </member>
                  <member>
                    <ResourceStatus>CREATE_COMPLETE</ResourceStatus>
                    <LogicalResourceId>CPUAlarmHigh</LogicalResourceId>
                    <LastUpdatedTime>2011-06-21T20:29:23Z</LastUpdatedTime>
                    <PhysicalResourceId>MyStack-CPUH-PF</PhysicalResourceId>
                    <ResourceType>AWS::CloudWatch::Alarm</ResourceType>
                  </member>
                </StackResourceSummaries>
              </ListStackResourcesResult>
              <ResponseMetadata>
                <RequestId>2d06e36c-ac1d-11e0-a958-f9382b6eb86b</RequestId>
              </ResponseMetadata>
            </ListStackResourcesResponse>
        """

    def test_list_stack_resources(self):
        self.set_http_response(status_code=200)
        resources = self.service_connection.list_stack_resources('MyStack',
                                                              next_token='next_token')
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].last_updated_time,
                         datetime(2011, 6, 21, 20, 25, 57))
        self.assertEqual(resources[0].logical_resource_id, 'SampleDB')
        self.assertEqual(resources[0].physical_resource_id, 'My-db-ycx')
        self.assertEqual(resources[0].resource_status, 'CREATE_COMPLETE')
        self.assertEqual(resources[0].resource_status_reason, None)
        self.assertEqual(resources[0].resource_type, 'AWS::RDS::DBInstance')

        self.assertEqual(resources[1].last_updated_time,
                         datetime(2011, 6, 21, 20, 29, 23))
        self.assertEqual(resources[1].logical_resource_id, 'CPUAlarmHigh')
        self.assertEqual(resources[1].physical_resource_id, 'MyStack-CPUH-PF')
        self.assertEqual(resources[1].resource_status, 'CREATE_COMPLETE')
        self.assertEqual(resources[1].resource_status_reason, None)
        self.assertEqual(resources[1].resource_type, 'AWS::CloudWatch::Alarm')

        self.assert_request_parameters({
            'Action': 'ListStackResources',
            'NextToken': 'next_token',
            'StackName': 'MyStack',
            'Version': '2010-05-15',
        })


class TestCloudFormationListStacks(CloudFormationConnectionBase):
    def default_body(self):
        return b"""
            <ListStacksResponse>
             <ListStacksResult>
              <StackSummaries>
                <member>
                    <StackId>arn:aws:cfn:us-east-1:1:stack/Test1/aa</StackId>
                    <StackStatus>CREATE_IN_PROGRESS</StackStatus>
                    <StackName>vpc1</StackName>
                    <CreationTime>2011-05-23T15:47:44Z</CreationTime>
                    <TemplateDescription>My Description.</TemplateDescription>
                </member>
              </StackSummaries>
             </ListStacksResult>
            </ListStacksResponse>
        """

    def test_list_stacks(self):
        self.set_http_response(status_code=200)
        stacks = self.service_connection.list_stacks(['CREATE_IN_PROGRESS'],
                                                  next_token='next_token')
        self.assertEqual(len(stacks), 1)
        self.assertEqual(stacks[0].stack_id,
                         'arn:aws:cfn:us-east-1:1:stack/Test1/aa')
        self.assertEqual(stacks[0].stack_status, 'CREATE_IN_PROGRESS')
        self.assertEqual(stacks[0].stack_name, 'vpc1')
        self.assertEqual(stacks[0].creation_time,
                         datetime(2011, 5, 23, 15, 47, 44))
        self.assertEqual(stacks[0].deletion_time, None)
        self.assertEqual(stacks[0].template_description, 'My Description.')

        self.assert_request_parameters({
            'Action': 'ListStacks',
            'NextToken': 'next_token',
            'StackStatusFilter.member.1': 'CREATE_IN_PROGRESS',
            'Version': '2010-05-15',
        })


class TestCloudFormationValidateTemplate(CloudFormationConnectionBase):
    def default_body(self):
        return b"""
            <ValidateTemplateResponse xmlns="http://cloudformation.amazonaws.com/doc/2010-05-15/">
              <ValidateTemplateResult>
                <Description>My Description.</Description>
                <Parameters>
                  <member>
                    <NoEcho>false</NoEcho>
                    <ParameterKey>InstanceType</ParameterKey>
                    <Description>Type of instance to launch</Description>
                    <DefaultValue>m1.small</DefaultValue>
                  </member>
                  <member>
                    <NoEcho>false</NoEcho>
                    <ParameterKey>KeyName</ParameterKey>
                    <Description>EC2 KeyPair</Description>
                  </member>
                </Parameters>
                <CapabilitiesReason>Reason</CapabilitiesReason>
                <Capabilities>
                  <member>CAPABILITY_IAM</member>
                </Capabilities>
              </ValidateTemplateResult>
              <ResponseMetadata>
                <RequestId>0be7b6e8-e4a0-11e0-a5bd-9f8d5a7dbc91</RequestId>
              </ResponseMetadata>
            </ValidateTemplateResponse>
        """

    def test_validate_template(self):
        self.set_http_response(status_code=200)
        template = self.service_connection.validate_template(template_body=SAMPLE_TEMPLATE,
                                                          template_url='http://url')
        self.assertEqual(template.description, 'My Description.')
        self.assertEqual(len(template.template_parameters), 2)
        param1, param2 = template.template_parameters
        self.assertEqual(param1.default_value, 'm1.small')
        self.assertEqual(param1.description, 'Type of instance to launch')
        self.assertEqual(param1.no_echo, True)
        self.assertEqual(param1.parameter_key, 'InstanceType')

        self.assertEqual(param2.default_value, None)
        self.assertEqual(param2.description, 'EC2 KeyPair')
        self.assertEqual(param2.no_echo, True)
        self.assertEqual(param2.parameter_key, 'KeyName')

        self.assertEqual(template.capabilities_reason, 'Reason')

        self.assertEqual(len(template.capabilities), 1)
        self.assertEqual(template.capabilities[0].value, 'CAPABILITY_IAM')

        self.assert_request_parameters({
            'Action': 'ValidateTemplate',
            'TemplateBody': SAMPLE_TEMPLATE,
            'TemplateURL': 'http://url',
            'Version': '2010-05-15',
        })


class TestCloudFormationCancelUpdateStack(CloudFormationConnectionBase):
    def default_body(self):
        return b"""<CancelUpdateStackResult/>"""

    def test_cancel_update_stack(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.cancel_update_stack('stack_name')
        self.assertEqual(api_response, True)
        self.assert_request_parameters({
            'Action': 'CancelUpdateStack',
            'StackName': 'stack_name',
            'Version': '2010-05-15',
        })


class TestCloudFormationEstimateTemplateCost(CloudFormationConnectionBase):
    def default_body(self):
        return b"""
            {
                "EstimateTemplateCostResponse": {
                    "EstimateTemplateCostResult": {
                        "Url": "http://calculator.s3.amazonaws.com/calc5.html?key=cf-2e351785-e821-450c-9d58-625e1e1ebfb6"
                    }
                }
            }
        """

    def test_estimate_template_cost(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.estimate_template_cost(
            template_body='{}')
        self.assertEqual(api_response,
            'http://calculator.s3.amazonaws.com/calc5.html?key=cf-2e351785-e821-450c-9d58-625e1e1ebfb6')
        self.assert_request_parameters({
            'Action': 'EstimateTemplateCost',
            'ContentType': 'JSON',
            'TemplateBody': '{}',
            'Version': '2010-05-15',
        })


class TestCloudFormationGetStackPolicy(CloudFormationConnectionBase):
    def default_body(self):
        return b"""
            {
                "GetStackPolicyResponse": {
                    "GetStackPolicyResult": {
                        "StackPolicyBody": "{...}"
                    }
                }
            }
        """

    def test_get_stack_policy(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.get_stack_policy('stack-id')
        self.assertEqual(api_response, '{...}')
        self.assert_request_parameters({
            'Action': 'GetStackPolicy',
            'ContentType': 'JSON',
            'StackName': 'stack-id',
            'Version': '2010-05-15',
        })


class TestCloudFormationSetStackPolicy(CloudFormationConnectionBase):
    def default_body(self):
        return b"""
            {
                "SetStackPolicyResponse": {
                    "SetStackPolicyResult": {
                        "Some": "content"
                    }
                }
            }
        """

    def test_set_stack_policy(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.set_stack_policy('stack-id',
            stack_policy_body='{}')
        self.assertDictEqual(api_response, {'SetStackPolicyResult': {'Some': 'content'}})
        self.assert_request_parameters({
            'Action': 'SetStackPolicy',
            'ContentType': 'JSON',
            'StackName': 'stack-id',
            'StackPolicyBody': '{}',
            'Version': '2010-05-15',
        })


if __name__ == '__main__':
    unittest.main()
