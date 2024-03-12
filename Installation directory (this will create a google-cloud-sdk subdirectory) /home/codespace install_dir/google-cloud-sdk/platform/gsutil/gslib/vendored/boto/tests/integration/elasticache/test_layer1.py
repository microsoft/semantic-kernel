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
import time
from tests.unit import unittest

from boto.elasticache import layer1
from boto.exception import BotoServerError


class TestElastiCacheConnection(unittest.TestCase):
    def setUp(self):
        self.elasticache = layer1.ElastiCacheConnection()

    def wait_until_cluster_available(self, cluster_id):
        timeout = time.time() + 600
        while time.time() < timeout:
            response = self.elasticache.describe_cache_clusters(cluster_id)
            status = (response['DescribeCacheClustersResponse']
                              ['DescribeCacheClustersResult']
                              ['CacheClusters'][0]['CacheClusterStatus'])
            if status == 'available':
                break
            time.sleep(5)
        else:
            self.fail('Timeout waiting for cache cluster %r'
                      'to become available.' % cluster_id)

    def test_create_delete_cache_cluster(self):
        cluster_id = 'cluster-id2'
        self.elasticache.create_cache_cluster(
            cluster_id, 1, 'cache.t1.micro', 'memcached')
        self.wait_until_cluster_available(cluster_id)

        self.elasticache.delete_cache_cluster(cluster_id)
        timeout = time.time() + 600
        while time.time() < timeout:
            try:
                self.elasticache.describe_cache_clusters(cluster_id)
            except BotoServerError:
                break
            time.sleep(5)
        else:
            self.fail('Timeout waiting for cache cluster %s'
                      'to be deleted.' % cluster_id)


if __name__ == '__main__':
    unittest.main()
