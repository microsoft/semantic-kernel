#!/usr/bin/env python

from tests.compat import mock, unittest

from boto.ec2.connection import EC2Connection

INSTANCE_STATUS_RESPONSE = br"""<?xml version="1.0" encoding="UTF-8"?>
<DescribeInstanceStatusResponse xmlns="http://ec2.amazonaws.com/doc/2013-02-01/">
    <requestId>3be1508e-c444-4fef-89cc-0b1223c4f02fEXAMPLE</requestId>
    <nextToken>page-2</nextToken>
    <instanceStatusSet />
</DescribeInstanceStatusResponse>
"""


class TestInstanceStatusResponseParsing(unittest.TestCase):
    def test_next_token(self):
        ec2 = EC2Connection(aws_access_key_id='aws_access_key_id',
                            aws_secret_access_key='aws_secret_access_key')
        mock_response = mock.Mock()
        mock_response.read.return_value = INSTANCE_STATUS_RESPONSE
        mock_response.status = 200
        ec2.make_request = mock.Mock(return_value=mock_response)
        all_statuses = ec2.get_all_instance_status()
        self.assertNotIn('IncludeAllInstances', ec2.make_request.call_args[0][1])
        self.assertEqual(all_statuses.next_token, 'page-2')

    def test_include_all_instances(self):
        ec2 = EC2Connection(aws_access_key_id='aws_access_key_id',
                            aws_secret_access_key='aws_secret_access_key')
        mock_response = mock.Mock()
        mock_response.read.return_value = INSTANCE_STATUS_RESPONSE
        mock_response.status = 200
        ec2.make_request = mock.Mock(return_value=mock_response)
        all_statuses = ec2.get_all_instance_status(include_all_instances=True)
        self.assertIn('IncludeAllInstances', ec2.make_request.call_args[0][1])
        self.assertEqual('true', ec2.make_request.call_args[0][1]['IncludeAllInstances'])
        self.assertEqual(all_statuses.next_token, 'page-2')


if __name__ == '__main__':
    unittest.main()
