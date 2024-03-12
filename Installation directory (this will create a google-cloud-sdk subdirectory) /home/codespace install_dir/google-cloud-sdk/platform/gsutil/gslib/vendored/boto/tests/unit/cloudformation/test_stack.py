#!/usr/bin/env python
import datetime
import xml.sax
import unittest
import boto.handler
import boto.resultset
import boto.cloudformation

SAMPLE_XML = b"""
<DescribeStacksResponse xmlns="http://cloudformation.amazonaws.com/doc/2010-05-15/">
  <DescribeStacksResult>
    <Stacks>
      <member>
        <Tags>
          <member>
            <Value>value0</Value>
            <Key>key0</Key>
          </member>
          <member>
            <Key>key1</Key>
            <Value>value1</Value>
          </member>
        </Tags>
        <StackId>arn:aws:cloudformation:ap-southeast-1:100:stack/Name/id</StackId>
        <StackStatus>CREATE_COMPLETE</StackStatus>
        <StackName>Name</StackName>
        <StackStatusReason/>
        <Description/>
        <NotificationARNs>
          <member>arn:aws:sns:ap-southeast-1:100:name</member>
        </NotificationARNs>
        <CreationTime>2013-01-10T05:04:56Z</CreationTime>
        <DisableRollback>false</DisableRollback>
        <Outputs>
          <member>
            <OutputValue>value0</OutputValue>
            <Description>output0</Description>
            <OutputKey>key0</OutputKey>
          </member>
          <member>
            <OutputValue>value1</OutputValue>
            <Description>output1</Description>
            <OutputKey>key1</OutputKey>
          </member>
        </Outputs>
      </member>
    </Stacks>
  </DescribeStacksResult>
  <ResponseMetadata>
    <RequestId>1</RequestId>
  </ResponseMetadata>
</DescribeStacksResponse>
"""

DESCRIBE_STACK_RESOURCE_XML = b"""
<DescribeStackResourcesResult>
  <StackResources>
    <member>
      <StackId>arn:aws:cloudformation:us-east-1:123456789:stack/MyStack/aaf549a0-a413-11df-adb3-5081b3858e83</StackId>
      <StackName>MyStack</StackName>
      <LogicalResourceId>MyDBInstance</LogicalResourceId>
      <PhysicalResourceId>MyStack_DB1</PhysicalResourceId>
      <ResourceType>AWS::DBInstance</ResourceType>
      <Timestamp>2010-07-27T22:27:28Z</Timestamp>
      <ResourceStatus>CREATE_COMPLETE</ResourceStatus>
    </member>
    <member>
      <StackId>arn:aws:cloudformation:us-east-1:123456789:stack/MyStack/aaf549a0-a413-11df-adb3-5081b3858e83</StackId>
      <StackName>MyStack</StackName>
      <LogicalResourceId>MyAutoScalingGroup</LogicalResourceId>
      <PhysicalResourceId>MyStack_ASG1</PhysicalResourceId>
      <ResourceType>AWS::AutoScalingGroup</ResourceType>
      <Timestamp>2010-07-27T22:28:28.123456Z</Timestamp>
      <ResourceStatus>CREATE_IN_PROGRESS</ResourceStatus>
    </member>
  </StackResources>
</DescribeStackResourcesResult>
"""

LIST_STACKS_XML = b"""
<ListStacksResponse>
 <ListStacksResult>
  <StackSummaries>
    <member>
        <StackId>
            arn:aws:cloudformation:us-east-1:1234567:stack/TestCreate1/aaaaa
        </StackId>
        <StackStatus>CREATE_IN_PROGRESS</StackStatus>
        <StackName>vpc1</StackName>
        <CreationTime>2011-05-23T15:47:44Z</CreationTime>
        <TemplateDescription>
            Creates one EC2 instance and a load balancer.
        </TemplateDescription>
    </member>
    <member>
        <StackId>
            arn:aws:cloudformation:us-east-1:1234567:stack/TestDelete2/bbbbb
        </StackId>
        <StackStatus>DELETE_COMPLETE</StackStatus>
        <DeletionTime>2011-03-10T16:20:51.575757Z</DeletionTime>
        <StackName>WP1</StackName>
        <CreationTime>2011-03-05T19:57:58.161616Z</CreationTime>
        <TemplateDescription>
            A simple basic Cloudformation Template.
        </TemplateDescription>
    </member>
  </StackSummaries>
 </ListStacksResult>
</ListStacksResponse>
"""

LIST_STACK_RESOURCES_XML = b"""
<ListStackResourcesResponse>
  <ListStackResourcesResult>
    <StackResourceSummaries>
      <member>
        <ResourceStatus>CREATE_COMPLETE</ResourceStatus>
        <LogicalResourceId>DBSecurityGroup</LogicalResourceId>
        <LastUpdatedTime>2011-06-21T20:15:58Z</LastUpdatedTime>
        <PhysicalResourceId>gmarcteststack-dbsecuritygroup-1s5m0ez5lkk6w</PhysicalResourceId>
        <ResourceType>AWS::RDS::DBSecurityGroup</ResourceType>
      </member>
      <member>
        <ResourceStatus>CREATE_COMPLETE</ResourceStatus>
        <LogicalResourceId>SampleDB</LogicalResourceId>
        <LastUpdatedTime>2011-06-21T20:25:57.875643Z</LastUpdatedTime>
        <PhysicalResourceId>MyStack-sampledb-ycwhk1v830lx</PhysicalResourceId>
        <ResourceType>AWS::RDS::DBInstance</ResourceType>
      </member>
    </StackResourceSummaries>
  </ListStackResourcesResult>
  <ResponseMetadata>
    <RequestId>2d06e36c-ac1d-11e0-a958-f9382b6eb86b</RequestId>
  </ResponseMetadata>
</ListStackResourcesResponse>
"""

class TestStackParse(unittest.TestCase):
    def test_parse_tags(self):
        rs = boto.resultset.ResultSet([
          ('member', boto.cloudformation.stack.Stack)
        ])
        h = boto.handler.XmlHandler(rs, None)
        xml.sax.parseString(SAMPLE_XML, h)
        tags = rs[0].tags
        self.assertEqual(tags, {u'key0': u'value0', u'key1': u'value1'})

    def test_event_creation_time_with_millis(self):
        millis_xml = SAMPLE_XML.replace(
          b"<CreationTime>2013-01-10T05:04:56Z</CreationTime>",
          b"<CreationTime>2013-01-10T05:04:56.102342Z</CreationTime>"
        )

        rs = boto.resultset.ResultSet([
          ('member', boto.cloudformation.stack.Stack)
        ])
        h = boto.handler.XmlHandler(rs, None)
        xml.sax.parseString(millis_xml, h)
        creation_time = rs[0].creation_time
        self.assertEqual(
          creation_time,
          datetime.datetime(2013, 1, 10, 5, 4, 56, 102342)
        )

    def test_resource_time_with_millis(self):
        rs = boto.resultset.ResultSet([
          ('member', boto.cloudformation.stack.StackResource)
        ])
        h = boto.handler.XmlHandler(rs, None)
        xml.sax.parseString(DESCRIBE_STACK_RESOURCE_XML, h)
        timestamp_1 = rs[0].timestamp
        self.assertEqual(
          timestamp_1,
          datetime.datetime(2010, 7, 27, 22, 27, 28)
        )
        timestamp_2 = rs[1].timestamp
        self.assertEqual(
          timestamp_2,
          datetime.datetime(2010, 7, 27, 22, 28, 28, 123456)
        )

    def test_list_stacks_time_with_millis(self):
        rs = boto.resultset.ResultSet([
            ('member', boto.cloudformation.stack.StackSummary)
        ])
        h = boto.handler.XmlHandler(rs, None)
        xml.sax.parseString(LIST_STACKS_XML, h)
        timestamp_1 = rs[0].creation_time
        self.assertEqual(
            timestamp_1,
            datetime.datetime(2011, 5, 23, 15, 47, 44)
        )
        timestamp_2 = rs[1].creation_time
        self.assertEqual(
            timestamp_2,
            datetime.datetime(2011, 3, 5, 19, 57, 58, 161616)
        )
        timestamp_3 = rs[1].deletion_time
        self.assertEqual(
            timestamp_3,
            datetime.datetime(2011, 3, 10, 16, 20, 51, 575757)
        )

    def test_list_stacks_time_with_millis_again(self):
        rs = boto.resultset.ResultSet([
            ('member', boto.cloudformation.stack.StackResourceSummary)
        ])
        h = boto.handler.XmlHandler(rs, None)
        xml.sax.parseString(LIST_STACK_RESOURCES_XML, h)
        timestamp_1 = rs[0].last_updated_time
        self.assertEqual(
            timestamp_1,
            datetime.datetime(2011, 6, 21, 20, 15, 58)
        )
        timestamp_2 = rs[1].last_updated_time
        self.assertEqual(
            timestamp_2,
            datetime.datetime(2011, 6, 21, 20, 25, 57, 875643)
        )

    def test_disable_rollback_false(self):
        # SAMPLE_XML defines DisableRollback=="false"
        rs = boto.resultset.ResultSet([('member', boto.cloudformation.stack.Stack)])
        h = boto.handler.XmlHandler(rs, None)
        xml.sax.parseString(SAMPLE_XML, h)
        disable_rollback = rs[0].disable_rollback
        self.assertFalse(disable_rollback)

    def test_disable_rollback_false_upper(self):
        # Should also handle "False"
        rs = boto.resultset.ResultSet([('member', boto.cloudformation.stack.Stack)])
        h = boto.handler.XmlHandler(rs, None)
        sample_xml_upper = SAMPLE_XML.replace(b'false', b'False')
        xml.sax.parseString(sample_xml_upper, h)
        disable_rollback = rs[0].disable_rollback
        self.assertFalse(disable_rollback)

    def test_disable_rollback_true(self):
        rs = boto.resultset.ResultSet([('member', boto.cloudformation.stack.Stack)])
        h = boto.handler.XmlHandler(rs, None)
        sample_xml_upper = SAMPLE_XML.replace(b'false', b'true')
        xml.sax.parseString(sample_xml_upper, h)
        disable_rollback = rs[0].disable_rollback
        self.assertTrue(disable_rollback)

    def test_disable_rollback_true_upper(self):
        rs = boto.resultset.ResultSet([('member', boto.cloudformation.stack.Stack)])
        h = boto.handler.XmlHandler(rs, None)
        sample_xml_upper = SAMPLE_XML.replace(b'false', b'True')
        xml.sax.parseString(sample_xml_upper, h)
        disable_rollback = rs[0].disable_rollback
        self.assertTrue(disable_rollback)


if __name__ == '__main__':
    unittest.main()
