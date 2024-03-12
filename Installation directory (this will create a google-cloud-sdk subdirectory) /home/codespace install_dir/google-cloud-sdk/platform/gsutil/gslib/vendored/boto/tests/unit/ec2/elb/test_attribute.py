from tests.unit import unittest
from tests.compat import mock

from boto.ec2.elb import ELBConnection
from boto.ec2.elb import LoadBalancer
from boto.ec2.elb.attributes import LbAttributes

ATTRIBUTE_GET_TRUE_CZL_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<DescribeLoadBalancerAttributesResponse  xmlns="http://elasticloadbalancing.amazonaws.com/doc/2012-06-01/">
 <DescribeLoadBalancerAttributesResult>
    <LoadBalancerAttributes>
      <CrossZoneLoadBalancing>
        <Enabled>true</Enabled>
      </CrossZoneLoadBalancing>
    </LoadBalancerAttributes>
  </DescribeLoadBalancerAttributesResult>
<ResponseMetadata>
    <RequestId>83c88b9d-12b7-11e3-8b82-87b12EXAMPLE</RequestId>
</ResponseMetadata>
</DescribeLoadBalancerAttributesResponse>
"""

ATTRIBUTE_GET_FALSE_CZL_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<DescribeLoadBalancerAttributesResponse  xmlns="http://elasticloadbalancing.amazonaws.com/doc/2012-06-01/">
 <DescribeLoadBalancerAttributesResult>
    <LoadBalancerAttributes>
      <CrossZoneLoadBalancing>
        <Enabled>false</Enabled>
      </CrossZoneLoadBalancing>
    </LoadBalancerAttributes>
  </DescribeLoadBalancerAttributesResult>
<ResponseMetadata>
    <RequestId>83c88b9d-12b7-11e3-8b82-87b12EXAMPLE</RequestId>
</ResponseMetadata>
</DescribeLoadBalancerAttributesResponse>
"""

ATTRIBUTE_GET_CS_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<DescribeLoadBalancerAttributesResponse  xmlns="http://elasticloadbalancing.amazonaws.com/doc/2012-06-01/">
 <DescribeLoadBalancerAttributesResult>
    <LoadBalancerAttributes>
      <ConnectionSettings>
        <IdleTimeout>30</IdleTimeout>
      </ConnectionSettings>
    </LoadBalancerAttributes>
  </DescribeLoadBalancerAttributesResult>
<ResponseMetadata>
    <RequestId>83c88b9d-12b7-11e3-8b82-87b12EXAMPLE</RequestId>
</ResponseMetadata>
</DescribeLoadBalancerAttributesResponse>
"""

ATTRIBUTE_SET_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<ModifyLoadBalancerAttributesResponse xmlns="http://elasticloadbalancing.amazonaws.com/doc/2012-06-01/">
<ModifyLoadBalancerAttributesResult/>
<ResponseMetadata>
    <RequestId>83c88b9d-12b7-11e3-8b82-87b12EXAMPLE</RequestId>
</ResponseMetadata>
</ModifyLoadBalancerAttributesResponse>
"""

# make_request arguments for setting attributes.
# Format: (API_COMMAND, API_PARAMS, API_PATH, API_METHOD)
ATTRIBUTE_SET_CZL_TRUE_REQUEST = (
    'ModifyLoadBalancerAttributes',
    {'LoadBalancerAttributes.CrossZoneLoadBalancing.Enabled': 'true',
     'LoadBalancerName': 'test_elb'}, mock.ANY, mock.ANY)
ATTRIBUTE_SET_CZL_FALSE_REQUEST = (
    'ModifyLoadBalancerAttributes',
    {'LoadBalancerAttributes.CrossZoneLoadBalancing.Enabled': 'false',
     'LoadBalancerName': 'test_elb'}, mock.ANY, mock.ANY)

# Tests to be run on an LbAttributes
# Format:
# (EC2_RESPONSE_STRING, list( (string_of_attribute_to_test, value) ) )
ATTRIBUTE_TESTS = [
    (ATTRIBUTE_GET_TRUE_CZL_RESPONSE,
     [('cross_zone_load_balancing.enabled', True)]),
    (ATTRIBUTE_GET_FALSE_CZL_RESPONSE,
     [('cross_zone_load_balancing.enabled', False)]),
    (ATTRIBUTE_GET_CS_RESPONSE,
     [('connecting_settings.idle_timeout', 30)]),
]


class TestLbAttributes(unittest.TestCase):
    """Tests LB Attributes."""
    def _setup_mock(self):
        """Sets up a mock elb request.
        Returns: response, elb connection and LoadBalancer
        """
        mock_response = mock.Mock()
        mock_response.status = 200
        elb = ELBConnection(aws_access_key_id='aws_access_key_id',
                            aws_secret_access_key='aws_secret_access_key')
        elb.make_request = mock.Mock(return_value=mock_response)
        return mock_response, elb, LoadBalancer(elb, 'test_elb')

    def _verify_attributes(self, attributes, attr_tests):
        """Verifies an LbAttributes object."""
        for attr, result in attr_tests:
            attr_result = attributes
            for sub_attr in attr.split('.'):
                attr_result = getattr(attr_result, sub_attr, None)
            self.assertEqual(attr_result, result)

    def test_get_all_lb_attributes(self):
        """Tests getting the LbAttributes from the elb.connection."""
        mock_response, elb, _ = self._setup_mock()

        for response, attr_tests in ATTRIBUTE_TESTS:
            mock_response.read.return_value = response
            attributes = elb.get_all_lb_attributes('test_elb')
            self.assertTrue(isinstance(attributes, LbAttributes))
            self._verify_attributes(attributes, attr_tests)

    def test_get_lb_attribute(self):
        """Tests getting a single attribute from elb.connection."""
        mock_response, elb, _ = self._setup_mock()

        tests = [
            ('crossZoneLoadBalancing', True, ATTRIBUTE_GET_TRUE_CZL_RESPONSE),
            ('crossZoneLoadBalancing', False, ATTRIBUTE_GET_FALSE_CZL_RESPONSE),
        ]

        for attr, value, response in tests:
            mock_response.read.return_value = response
            status = elb.get_lb_attribute('test_elb', attr)
            self.assertEqual(status, value)

    def test_modify_lb_attribute(self):
        """Tests setting the attributes from elb.connection."""
        mock_response, elb, _ = self._setup_mock()

        tests = [
            ('crossZoneLoadBalancing', True, ATTRIBUTE_SET_CZL_TRUE_REQUEST),
            ('crossZoneLoadBalancing', False, ATTRIBUTE_SET_CZL_FALSE_REQUEST),
        ]

        for attr, value, args in tests:
            mock_response.read.return_value = ATTRIBUTE_SET_RESPONSE
            result = elb.modify_lb_attribute('test_elb', attr, value)
            self.assertTrue(result)
            elb.make_request.assert_called_with(*args)

    def test_lb_get_attributes(self):
        """Tests the LbAttributes from the ELB object."""
        mock_response, _, lb = self._setup_mock()

        for response, attr_tests in ATTRIBUTE_TESTS:
            mock_response.read.return_value = response
            attributes = lb.get_attributes(force=True)
            self.assertTrue(isinstance(attributes, LbAttributes))
            self._verify_attributes(attributes, attr_tests)

    def test_lb_is_cross_zone_load_balancing(self):
        """Tests checking is_cross_zone_load_balancing."""
        mock_response, _, lb = self._setup_mock()

        tests = [
            # Format: (method, args, result, response)
            # Gets a true result.
            (lb.is_cross_zone_load_balancing, [], True,
             ATTRIBUTE_GET_TRUE_CZL_RESPONSE),
            # Returns the previous calls cached value.
            (lb.is_cross_zone_load_balancing, [], True,
             ATTRIBUTE_GET_FALSE_CZL_RESPONSE),
            # Gets a false result.
            (lb.is_cross_zone_load_balancing, [True], False,
             ATTRIBUTE_GET_FALSE_CZL_RESPONSE),
        ]

        for method, args, result, response in tests:
            mock_response.read.return_value = response
            self.assertEqual(method(*args), result)

    def test_lb_enable_cross_zone_load_balancing(self):
        """Tests enabling cross zone balancing from LoadBalancer."""
        mock_response, elb, lb = self._setup_mock()

        mock_response.read.return_value = ATTRIBUTE_SET_RESPONSE
        self.assertTrue(lb.enable_cross_zone_load_balancing())
        elb.make_request.assert_called_with(*ATTRIBUTE_SET_CZL_TRUE_REQUEST)

    def test_lb_disable_cross_zone_load_balancing(self):
        """Tests disabling cross zone balancing from LoadBalancer."""
        mock_response, elb, lb = self._setup_mock()

        mock_response.read.return_value = ATTRIBUTE_SET_RESPONSE
        self.assertTrue(lb.disable_cross_zone_load_balancing())
        elb.make_request.assert_called_with(*ATTRIBUTE_SET_CZL_FALSE_REQUEST)

    def test_lb_get_connection_settings(self):
        """Tests checking connectionSettings attribute"""
        mock_response, elb, _ = self._setup_mock()
        
        attrs = [('idle_timeout', 30), ]
        mock_response.read.return_value = ATTRIBUTE_GET_CS_RESPONSE
        attributes = elb.get_all_lb_attributes('test_elb')
        self.assertTrue(isinstance(attributes, LbAttributes))
        for attr, value in attrs:
            self.assertEqual(getattr(attributes.connecting_settings, attr), value)

if __name__ == '__main__':
    unittest.main()
