import boto

from time import time
from tests.compat import unittest

DEFAULT_S3_POLICY = """{
    "Version": "2012-10-17",
    "Statement": [
                {
                    "Sid": "AWSCloudTrailAclCheck20131101",
                    "Effect": "Allow",
                    "Principal": {
                "AWS": [
                "arn:aws:iam::086441151436:root",
                "arn:aws:iam::113285607260:root"
            ]
                    },
                    "Action": "s3:GetBucketAcl",
                    "Resource": "arn:aws:s3:::<BucketName>"
                },
                {
                    "Sid": "AWSCloudTrailWrite20131101",
                    "Effect": "Allow",
                    "Principal": {
                "AWS": [
                "arn:aws:iam::086441151436:root",
                "arn:aws:iam::113285607260:root"
            ]
                    },
                    "Action": "s3:PutObject",
                    "Resource": "arn:aws:s3:::<BucketName>/<Prefix>/AWSLogs/<CustomerAccountID>/*",
                    "Condition": {
                        "StringEquals": {
                                    "s3:x-amz-acl": "bucket-owner-full-control"
                        }
                    }
                }
    ]
}"""

class TestCloudTrail(unittest.TestCase):
    def test_cloudtrail(self):
        cloudtrail = boto.connect_cloudtrail()

        # Don't delete existing customer data!
        res = cloudtrail.describe_trails()
        if len(res['trailList']):
            self.fail('A trail already exists on this account!')

        # Who am I?
        iam = boto.connect_iam()
        response = iam.get_user()
        account_id = response['get_user_response']['get_user_result'] \
                             ['user']['user_id']

        # Setup a new bucket
        s3 = boto.connect_s3()
        bucket_name = 'cloudtrail-integ-{0}'.format(time())
        policy = DEFAULT_S3_POLICY.replace('<BucketName>', bucket_name)\
                                  .replace('<CustomerAccountID>', account_id)\
                                  .replace('<Prefix>/', '')
        b = s3.create_bucket(bucket_name)
        b.set_policy(policy)

        # Setup CloudTrail
        cloudtrail.create_trail(trail={'Name': 'test', 'S3BucketName': bucket_name})

        cloudtrail.update_trail(trail={'Name': 'test', 'IncludeGlobalServiceEvents': False})

        trails = cloudtrail.describe_trails()

        self.assertEqual('test', trails['trailList'][0]['Name'])
        self.assertFalse(trails['trailList'][0]['IncludeGlobalServiceEvents'])

        cloudtrail.start_logging(name='test')

        status = cloudtrail.get_trail_status(name='test')
        self.assertTrue(status['IsLogging'])

        cloudtrail.stop_logging(name='test')

        status = cloudtrail.get_trail_status(name='test')
        self.assertFalse(status['IsLogging'])

        # Clean up
        cloudtrail.delete_trail(name='test')

        for key in b.list():
            key.delete()

        s3.delete_bucket(bucket_name)
