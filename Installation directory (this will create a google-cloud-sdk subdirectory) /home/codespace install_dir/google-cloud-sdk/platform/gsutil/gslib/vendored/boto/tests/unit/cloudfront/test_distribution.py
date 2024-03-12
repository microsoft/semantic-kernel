import unittest

from boto.cloudfront.distribution import DistributionConfig
from boto.cloudfront.logging import LoggingInfo


class CloudfrontDistributionTest(unittest.TestCase):
    cloudfront = True

    def setUp(self):
        self.dist = DistributionConfig()

    def test_logging(self):
        # Default.
        self.assertEqual(self.dist.logging, None)

        # Override.
        lo = LoggingInfo(bucket='whatever', prefix='override_')
        dist = DistributionConfig(logging=lo)
        self.assertEqual(dist.logging.bucket, 'whatever')
        self.assertEqual(dist.logging.prefix, 'override_')
