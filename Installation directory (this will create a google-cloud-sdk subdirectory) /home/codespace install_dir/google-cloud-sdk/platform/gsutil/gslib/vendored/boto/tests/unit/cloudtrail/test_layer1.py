#!/usr/bin/env python

import json

from boto.cloudtrail.layer1 import CloudTrailConnection
from tests.unit import AWSMockServiceTestCase


class TestDescribeTrails(AWSMockServiceTestCase):
    connection_class = CloudTrailConnection

    def default_body(self):
        return b'''
            {"trailList":
                [
                    {
                        "IncludeGlobalServiceEvents": false,
                        "Name": "test",
                        "SnsTopicName": "cloudtrail-1",
                        "S3BucketName": "cloudtrail-1"
                    }
                ]
            }'''

    def test_describe(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.describe_trails()

        self.assertEqual(1, len(api_response['trailList']))
        self.assertEqual('test', api_response['trailList'][0]['Name'])

        self.assert_request_parameters({})

        target = self.actual_request.headers['X-Amz-Target']
        self.assertTrue('DescribeTrails' in target)

    def test_describe_name_list(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.describe_trails(
            trail_name_list=['test'])

        self.assertEqual(1, len(api_response['trailList']))
        self.assertEqual('test', api_response['trailList'][0]['Name'])

        self.assertEqual(json.dumps({
            'trailNameList': ['test']
        }), self.actual_request.body.decode('utf-8'))

        target = self.actual_request.headers['X-Amz-Target']
        self.assertTrue('DescribeTrails' in target)


class TestCreateTrail(AWSMockServiceTestCase):
    connection_class = CloudTrailConnection

    def default_body(self):
        return b'''
            {"trail":
                {
                    "IncludeGlobalServiceEvents": false,
                    "Name": "test",
                    "SnsTopicName": "cloudtrail-1",
                    "S3BucketName": "cloudtrail-1"
                }
            }'''

    def test_create(self):
        self.set_http_response(status_code=200)

        api_response = self.service_connection.create_trail(
            'test', 'cloudtrail-1', sns_topic_name='cloudtrail-1',
            include_global_service_events=False)

        self.assertEqual('test', api_response['trail']['Name'])
        self.assertEqual('cloudtrail-1', api_response['trail']['S3BucketName'])
        self.assertEqual('cloudtrail-1', api_response['trail']['SnsTopicName'])
        self.assertEqual(False,
                         api_response['trail']['IncludeGlobalServiceEvents'])

        target = self.actual_request.headers['X-Amz-Target']
        self.assertTrue('CreateTrail' in target)
