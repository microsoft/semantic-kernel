from boto.elasticache.layer1 import ElastiCacheConnection
from tests.unit import AWSMockServiceTestCase


class TestAPIInterface(AWSMockServiceTestCase):
    connection_class = ElastiCacheConnection

    def test_required_launch_params(self):
        """ Make sure only the AWS required params are required by boto """
        name = 'test_cache_cluster'
        self.set_http_response(status_code=200, body=b'{}')
        self.service_connection.create_cache_cluster(name)

        self.assert_request_parameters({
            'Action': 'CreateCacheCluster',
            'CacheClusterId': name,
        }, ignore_params_values=[
            'Version',
            'ContentType',
        ])
