#!/usr/bin/env python
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
# Copyright (c) 2014 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

from tests.unit import AWSMockServiceTestCase, MockServiceWithConfigTestCase

from tests.compat import mock

from boto.sqs.connection import SQSConnection
from boto.sqs.regioninfo import SQSRegionInfo
from boto.sqs.message import RawMessage
from boto.sqs.queue import Queue
from boto.connection import AWSQueryConnection

from nose.plugins.attrib import attr

class SQSAuthParams(AWSMockServiceTestCase):
    connection_class = SQSConnection

    def setUp(self):
        super(SQSAuthParams, self).setUp()

    def default_body(self):
        return """<?xml version="1.0"?>
            <CreateQueueResponse>
              <CreateQueueResult>
                <QueueUrl>
                  https://queue.amazonaws.com/599169622985/myqueue1
                </QueueUrl>
              </CreateQueueResult>
              <ResponseMetadata>
                <RequestId>54d4c94d-2307-54a8-bb27-806a682a5abd</RequestId>
              </ResponseMetadata>
            </CreateQueueResponse>"""

    @attr(sqs=True)
    def test_auth_service_name_override(self):
        self.set_http_response(status_code=200)
        # We can use the auth_service_name to change what service
        # name to use for the credential scope for sigv4.
        self.service_connection.auth_service_name = 'service_override'

        self.service_connection.create_queue('my_queue')
        # Note the service_override value instead.
        self.assertIn('us-east-1/service_override/aws4_request',
                      self.actual_request.headers['Authorization'])

    @attr(sqs=True)
    def test_class_attribute_can_set_service_name(self):
        self.set_http_response(status_code=200)
        # The SQS class has an 'AuthServiceName' param of 'sqs':
        self.assertEqual(self.service_connection.AuthServiceName, 'sqs')

        self.service_connection.create_queue('my_queue')
        # And because of this, the value of 'sqs' will be used instead of
        # 'queue' for the credential scope:
        self.assertIn('us-east-1/sqs/aws4_request',
                      self.actual_request.headers['Authorization'])

    @attr(sqs=True)
    def test_auth_region_name_is_automatically_updated(self):
        region = SQSRegionInfo(name='us-west-2',
                               endpoint='us-west-2.queue.amazonaws.com')
        self.service_connection = SQSConnection(
            https_connection_factory=self.https_connection_factory,
            aws_access_key_id='aws_access_key_id',
            aws_secret_access_key='aws_secret_access_key',
            region=region)
        self.initialize_service_connection()
        self.set_http_response(status_code=200)

        self.service_connection.create_queue('my_queue')

        # Note the region name below is 'us-west-2'.
        self.assertIn('us-west-2/sqs/aws4_request',
                      self.actual_request.headers['Authorization'])

    @attr(sqs=True)
    def test_set_get_auth_service_and_region_names(self):
        self.service_connection.auth_service_name = 'service_name'
        self.service_connection.auth_region_name = 'region_name'

        self.assertEqual(self.service_connection.auth_service_name,
                         'service_name')
        self.assertEqual(self.service_connection.auth_region_name, 'region_name')

    @attr(sqs=True)
    def test_get_queue_with_owner_account_id_returns_queue(self):

        self.set_http_response(status_code=200)
        self.service_connection.create_queue('my_queue')

        self.service_connection.get_queue('my_queue', '599169622985')

        assert 'QueueOwnerAWSAccountId' in self.actual_request.params.keys()
        self.assertEquals(self.actual_request.params['QueueOwnerAWSAccountId'], '599169622985')

class SQSProfileName(MockServiceWithConfigTestCase):
    connection_class = SQSConnection
    profile_name = 'prod'

    def setUp(self):
        super(SQSProfileName, self).setUp()
        self.config = {
            "profile prod": {
                'aws_access_key_id': 'access_key',
                'aws_secret_access_key': 'secret_access',
            }
        }

    @attr(sqs=True)
    def test_profile_name_gets_passed(self):

        region = SQSRegionInfo(name='us-west-2',
                               endpoint='us-west-2.queue.amazonaws.com')
        self.service_connection = SQSConnection(
            https_connection_factory=self.https_connection_factory,
            region=region,
            profile_name=self.profile_name)
        self.initialize_service_connection()
        self.set_http_response(status_code=200)

        self.assertEquals(self.service_connection.profile_name, self.profile_name)

class SQSMessageAttributesParsing(AWSMockServiceTestCase):
    connection_class = SQSConnection

    def default_body(self):
        return """<?xml version="1.0"?>
<ReceiveMessageResponse xmlns="http://queue.amazonaws.com/doc/2012-11-05/">
    <ReceiveMessageResult>
        <Message>
            <Body>This is a test</Body>
            <ReceiptHandle>+eXJYhj5rDql5hp2VwGkXvQVsefdjAlsQe5EGS57gyORPB48KwP1d/3Rfy4DrQXt+MgfRPHUCUH36xL9+Ol/UWD/ylKrrWhiXSY0Ip4EsI8jJNTo/aneEjKE/iZnz/nL8MFP5FmMj8PbDAy5dgvAqsdvX1rm8Ynn0bGnQLJGfH93cLXT65p6Z/FDyjeBN0M+9SWtTcuxOIcMdU8NsoFIwm/6mLWgWAV46OhlYujzvyopCvVwsj+Y8jLEpdSSvTQHNlQEaaY/V511DqAvUwru2p0ZbW7ZzcbhUTn6hHkUROo=</ReceiptHandle>
            <MD5OfBody>ce114e4501d2f4e2dcea3e17b546f339</MD5OfBody>
            <MessageAttribute>
                <Name>Count</Name>
                <Value>
                    <DataType>Number</DataType>
                    <StringValue>1</StringValue>
                </Value>
            </MessageAttribute>
            <MessageAttribute>
                <Name>Foo</Name>
                <Value>
                    <DataType>String</DataType>
                    <StringValue>Bar</StringValue>
                </Value>
            </MessageAttribute>
            <MessageId>7049431b-e5f6-430b-93c4-ded53864d02b</MessageId>
            <MD5OfMessageAttributes>324758f82d026ac6ec5b31a3b192d1e3</MD5OfMessageAttributes>
        </Message>
    </ReceiveMessageResult>
    <ResponseMetadata>
        <RequestId>73f978f2-400b-5460-8d38-3316e39e79c6</RequestId>
    </ResponseMetadata>
</ReceiveMessageResponse>"""

    @attr(sqs=True)
    def test_message_attribute_response(self):
        self.set_http_response(status_code=200)

        queue = Queue(
            url='http://sqs.us-east-1.amazonaws.com/123456789012/testQueue/',
            message_class=RawMessage)
        message = self.service_connection.receive_message(queue)[0]

        self.assertEqual(message.get_body(), 'This is a test')
        self.assertEqual(message.id, '7049431b-e5f6-430b-93c4-ded53864d02b')
        self.assertEqual(message.md5, 'ce114e4501d2f4e2dcea3e17b546f339')
        self.assertEqual(message.md5_message_attributes,
                         '324758f82d026ac6ec5b31a3b192d1e3')

        mattributes = message.message_attributes
        self.assertEqual(len(mattributes.keys()), 2)
        self.assertEqual(mattributes['Count']['data_type'], 'Number')
        self.assertEqual(mattributes['Foo']['string_value'], 'Bar')


class SQSSendMessageAttributes(AWSMockServiceTestCase):
    connection_class = SQSConnection

    def default_body(self):
        return """<SendMessageResponse>
    <SendMessageResult>
        <MD5OfMessageBody>
            fafb00f5732ab283681e124bf8747ed1
        </MD5OfMessageBody>
        <MD5OfMessageAttributes>
        3ae8f24a165a8cedc005670c81a27295
        </MD5OfMessageAttributes>
        <MessageId>
            5fea7756-0ea4-451a-a703-a558b933e274
        </MessageId>
    </SendMessageResult>
    <ResponseMetadata>
        <RequestId>
            27daac76-34dd-47df-bd01-1f6e873584a0
        </RequestId>
    </ResponseMetadata>
</SendMessageResponse>
"""

    @attr(sqs=True)
    def test_send_message_attributes(self):
        self.set_http_response(status_code=200)

        queue = Queue(
            url='http://sqs.us-east-1.amazonaws.com/123456789012/testQueue/',
            message_class=RawMessage)
        self.service_connection.send_message(queue, 'Test message',
            message_attributes={
                'name1': {
                    'data_type': 'String',
                    'string_value': 'Bob'
                },
                'name2': {
                    'data_type': 'Number',
                    'string_value': '1'
                }
            })

        self.assert_request_parameters({
            'Action': 'SendMessage',
            'MessageAttribute.1.Name': 'name1',
            'MessageAttribute.1.Value.DataType': 'String',
            'MessageAttribute.1.Value.StringValue': 'Bob',
            'MessageAttribute.2.Name': 'name2',
            'MessageAttribute.2.Value.DataType': 'Number',
            'MessageAttribute.2.Value.StringValue': '1',
            'MessageBody': 'Test message',
            'Version': '2012-11-05'
        })


class SQSSendBatchMessageAttributes(AWSMockServiceTestCase):
    connection_class = SQSConnection

    def default_body(self):
        return """<SendMessageBatchResponse>
<SendMessageBatchResult>
    <SendMessageBatchResultEntry>
        <Id>test_msg_001</Id>
        <MessageId>0a5231c7-8bff-4955-be2e-8dc7c50a25fa</MessageId>
        <MD5OfMessageBody>0e024d309850c78cba5eabbeff7cae71</MD5OfMessageBody>
    </SendMessageBatchResultEntry>
    <SendMessageBatchResultEntry>
        <Id>test_msg_002</Id>
        <MessageId>15ee1ed3-87e7-40c1-bdaa-2e49968ea7e9</MessageId>
        <MD5OfMessageBody>7fb8146a82f95e0af155278f406862c2</MD5OfMessageBody>
        <MD5OfMessageAttributes>295c5fa15a51aae6884d1d7c1d99ca50</MD5OfMessageAttributes>
    </SendMessageBatchResultEntry>
</SendMessageBatchResult>
<ResponseMetadata>
    <RequestId>ca1ad5d0-8271-408b-8d0f-1351bf547e74</RequestId>
</ResponseMetadata>
</SendMessageBatchResponse>
"""

    @attr(sqs=True)
    def test_send_message_attributes(self):
        self.set_http_response(status_code=200)

        queue = Queue(
            url='http://sqs.us-east-1.amazonaws.com/123456789012/testQueue/',
            message_class=RawMessage)

        message1 = (1, 'Message 1', 0, {'name1': {'data_type': 'String',
                                                  'string_value': 'foo'}})
        message2 = (2, 'Message 2', 0, {'name2': {'data_type': 'Number',
                                                  'string_value': '1'}})

        self.service_connection.send_message_batch(queue, (message1, message2))

        self.assert_request_parameters({
            'Action': 'SendMessageBatch',
            'SendMessageBatchRequestEntry.1.DelaySeconds': 0,
            'SendMessageBatchRequestEntry.1.Id': 1,
            'SendMessageBatchRequestEntry.1.MessageAttribute.1.Name': 'name1',
            'SendMessageBatchRequestEntry.1.MessageAttribute.1.Value.DataType': 'String',
            'SendMessageBatchRequestEntry.1.MessageAttribute.1.Value.StringValue': 'foo',
            'SendMessageBatchRequestEntry.1.MessageBody': 'Message 1',
            'SendMessageBatchRequestEntry.2.DelaySeconds': 0,
            'SendMessageBatchRequestEntry.2.Id': 2,
            'SendMessageBatchRequestEntry.2.MessageAttribute.1.Name': 'name2',
            'SendMessageBatchRequestEntry.2.MessageAttribute.1.Value.DataType': 'Number',
            'SendMessageBatchRequestEntry.2.MessageAttribute.1.Value.StringValue': '1',
            'SendMessageBatchRequestEntry.2.MessageBody': 'Message 2',
            'Version': '2012-11-05'
        })

if __name__ == '__main__':
    unittest.main()
