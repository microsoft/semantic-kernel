#!/usr/bin/env python
# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
import json
from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase
from mock import Mock

from boto.sns.connection import SNSConnection

QUEUE_POLICY = {
    u'Policy':
        (u'{"Version":"2008-10-17","Id":"arn:aws:sqs:us-east-1:'
         'idnum:testqueuepolicy/SQSDefaultPolicy","Statement":'
         '[{"Sid":"sidnum","Effect":"Allow","Principal":{"AWS":"*"},'
         '"Action":"SQS:GetQueueUrl","Resource":'
         '"arn:aws:sqs:us-east-1:idnum:testqueuepolicy"}]}')}


class TestSNSConnection(AWSMockServiceTestCase):
    connection_class = SNSConnection

    def setUp(self):
        super(TestSNSConnection, self).setUp()

    def default_body(self):
        return b"{}"

    def test_sqs_with_existing_policy(self):
        self.set_http_response(status_code=200)

        queue = Mock()
        queue.get_attributes.return_value = QUEUE_POLICY
        queue.arn = 'arn:aws:sqs:us-east-1:idnum:queuename'

        self.service_connection.subscribe_sqs_queue('topic_arn', queue)
        self.assert_request_parameters({
               'Action': 'Subscribe',
               'ContentType': 'JSON',
               'Endpoint': 'arn:aws:sqs:us-east-1:idnum:queuename',
               'Protocol': 'sqs',
               'TopicArn': 'topic_arn',
               'Version': '2010-03-31',
        }, ignore_params_values=[])

        # Verify that the queue policy was properly updated.
        actual_policy = json.loads(queue.set_attribute.call_args[0][1])
        self.assertEqual(actual_policy['Version'], '2008-10-17')
        # A new statement should be appended to the end of the statement list.
        self.assertEqual(len(actual_policy['Statement']), 2)
        self.assertEqual(actual_policy['Statement'][1]['Action'],
                         'SQS:SendMessage')

    def test_sqs_with_no_previous_policy(self):
        self.set_http_response(status_code=200)

        queue = Mock()
        queue.get_attributes.return_value = {}
        queue.arn = 'arn:aws:sqs:us-east-1:idnum:queuename'

        self.service_connection.subscribe_sqs_queue('topic_arn', queue)
        self.assert_request_parameters({
               'Action': 'Subscribe',
               'ContentType': 'JSON',
               'Endpoint': 'arn:aws:sqs:us-east-1:idnum:queuename',
               'Protocol': 'sqs',
               'TopicArn': 'topic_arn',
               'Version': '2010-03-31',
        }, ignore_params_values=[])
        actual_policy = json.loads(queue.set_attribute.call_args[0][1])
        # Only a single statement should be part of the policy.
        self.assertEqual(len(actual_policy['Statement']), 1)

    def test_publish_with_positional_args(self):
        self.set_http_response(status_code=200)

        self.service_connection.publish('topic', 'message', 'subject')
        self.assert_request_parameters({
            'Action': 'Publish',
            'TopicArn': 'topic',
            'Subject': 'subject',
            'Message': 'message',
        }, ignore_params_values=['Version', 'ContentType'])

    def test_publish_with_kwargs(self):
        self.set_http_response(status_code=200)

        self.service_connection.publish(topic='topic',
                                        message='message',
                                        subject='subject')
        self.assert_request_parameters({
            'Action': 'Publish',
            'TopicArn': 'topic',
            'Subject': 'subject',
            'Message': 'message',
        }, ignore_params_values=['Version', 'ContentType'])

    def test_publish_with_target_arn(self):
        self.set_http_response(status_code=200)

        self.service_connection.publish(target_arn='target_arn',
                                        message='message',
                                        subject='subject')
        self.assert_request_parameters({
            'Action': 'Publish',
            'TargetArn': 'target_arn',
            'Subject': 'subject',
            'Message': 'message',
        }, ignore_params_values=['Version', 'ContentType'])

    def test_create_platform_application(self):
        self.set_http_response(status_code=200)

        self.service_connection.create_platform_application(
            name='MyApp',
            platform='APNS',
            attributes={
                'PlatformPrincipal': 'a ssl certificate',
                'PlatformCredential': 'a private key'
            }
        )
        self.assert_request_parameters({
            'Action': 'CreatePlatformApplication',
            'Name': 'MyApp',
            'Platform': 'APNS',
            'Attributes.entry.1.key': 'PlatformCredential',
            'Attributes.entry.1.value': 'a private key',
            'Attributes.entry.2.key': 'PlatformPrincipal',
            'Attributes.entry.2.value': 'a ssl certificate',
        }, ignore_params_values=['Version', 'ContentType'])

    def test_set_platform_application_attributes(self):
        self.set_http_response(status_code=200)

        self.service_connection.set_platform_application_attributes(
            platform_application_arn='arn:myapp',
            attributes={'PlatformPrincipal': 'a ssl certificate',
                        'PlatformCredential': 'a private key'})
        self.assert_request_parameters({
            'Action': 'SetPlatformApplicationAttributes',
            'PlatformApplicationArn': 'arn:myapp',
            'Attributes.entry.1.key': 'PlatformCredential',
            'Attributes.entry.1.value': 'a private key',
            'Attributes.entry.2.key': 'PlatformPrincipal',
            'Attributes.entry.2.value': 'a ssl certificate',
        }, ignore_params_values=['Version', 'ContentType'])

    def test_create_platform_endpoint(self):
        self.set_http_response(status_code=200)

        self.service_connection.create_platform_endpoint(
            platform_application_arn='arn:myapp',
            token='abcde12345',
            custom_user_data='john',
            attributes={'Enabled': False})
        self.assert_request_parameters({
            'Action': 'CreatePlatformEndpoint',
            'PlatformApplicationArn': 'arn:myapp',
            'Token': 'abcde12345',
            'CustomUserData': 'john',
            'Attributes.entry.1.key': 'Enabled',
            'Attributes.entry.1.value': False,
        }, ignore_params_values=['Version', 'ContentType'])

    def test_set_endpoint_attributes(self):
        self.set_http_response(status_code=200)

        self.service_connection.set_endpoint_attributes(
            endpoint_arn='arn:myendpoint',
            attributes={'CustomUserData': 'john',
                        'Enabled': False})
        self.assert_request_parameters({
            'Action': 'SetEndpointAttributes',
            'EndpointArn': 'arn:myendpoint',
            'Attributes.entry.1.key': 'CustomUserData',
            'Attributes.entry.1.value': 'john',
            'Attributes.entry.2.key': 'Enabled',
            'Attributes.entry.2.value': False,
        }, ignore_params_values=['Version', 'ContentType'])

    def test_message_is_required(self):
        self.set_http_response(status_code=200)

        with self.assertRaises(TypeError):
            self.service_connection.publish(topic='topic', subject='subject')

    def test_publish_with_json(self):
        self.set_http_response(status_code=200)

        self.service_connection.publish(
            message=json.dumps({
                'default': 'Ignored.',
                'GCM': {
                    'data': 'goes here',
                }
            }),
            message_structure='json',
            subject='subject',
            target_arn='target_arn'
        )
        self.assert_request_parameters({
            'Action': 'Publish',
            'TargetArn': 'target_arn',
            'Subject': 'subject',
            'MessageStructure': 'json',
        }, ignore_params_values=['Version', 'ContentType', 'Message'])
        self.assertDictEqual(
            json.loads(self.actual_request.params["Message"]),
            {"default": "Ignored.", "GCM": {"data": "goes here"}})

    def test_publish_with_utf8_message(self):
        self.set_http_response(status_code=200)
        subject = message = u'We \u2665 utf-8'.encode('utf-8')
        self.service_connection.publish('topic', message, subject)
        self.assert_request_parameters({
            'Action': 'Publish',
            'TopicArn': 'topic',
            'Subject': subject,
            'Message': message,
        }, ignore_params_values=['Version', 'ContentType'])

    def test_publish_with_attributes(self):
        self.set_http_response(status_code=200)

        self.service_connection.publish(
            message=json.dumps({
                'default': 'Ignored.',
                'GCM': {
                    'data': 'goes here',
                }
            }, sort_keys=True),
            message_structure='json',
            subject='subject',
            target_arn='target_arn',
            message_attributes={
                'name1': {
                    'data_type': 'Number',
                    'string_value': '42'
                },
                'name2': {
                    'data_type': 'String',
                    'string_value': 'Bob'
                },
            },
        )
        self.assert_request_parameters({
            'Action': 'Publish',
            'TargetArn': 'target_arn',
            'Subject': 'subject',
            'Message': '{"GCM": {"data": "goes here"}, "default": "Ignored."}',
            'MessageStructure': 'json',
            'MessageAttributes.entry.1.Name': 'name1',
            'MessageAttributes.entry.1.Value.DataType': 'Number',
            'MessageAttributes.entry.1.Value.StringValue': '42',
            'MessageAttributes.entry.2.Name': 'name2',
            'MessageAttributes.entry.2.Value.DataType': 'String',
            'MessageAttributes.entry.2.Value.StringValue': 'Bob',
        }, ignore_params_values=['Version', 'ContentType'])


if __name__ == '__main__':
    unittest.main()
