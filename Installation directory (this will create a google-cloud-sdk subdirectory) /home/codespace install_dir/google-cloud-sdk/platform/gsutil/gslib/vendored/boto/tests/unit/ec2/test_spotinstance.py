from tests.unit import AWSMockServiceTestCase

from boto.ec2.connection import EC2Connection


class TestCancelSpotInstanceRequests(AWSMockServiceTestCase):

    connection_class = EC2Connection

    def default_body(self):
        return b"""
            <CancelSpotInstanceRequestsResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
              <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
              <spotInstanceRequestSet>
                <item>
                  <spotInstanceRequestId>sir-1a2b3c4d</spotInstanceRequestId>
                  <state>cancelled</state>
                </item>
                <item>
                  <spotInstanceRequestId>sir-9f8e7d6c</spotInstanceRequestId>
                  <state>cancelled</state>
                </item>
              </spotInstanceRequestSet>
            </CancelSpotInstanceRequestsResponse>
        """

    def test_cancel_spot_instance_requests(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.cancel_spot_instance_requests(['sir-1a2b3c4d',
                                                                          'sir-9f8e7d6c'])
        self.assert_request_parameters({
            'Action': 'CancelSpotInstanceRequests',
            'SpotInstanceRequestId.1': 'sir-1a2b3c4d',
            'SpotInstanceRequestId.2': 'sir-9f8e7d6c'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0].id, 'sir-1a2b3c4d')
        self.assertEqual(response[0].state, 'cancelled')
        self.assertEqual(response[1].id, 'sir-9f8e7d6c')
        self.assertEqual(response[1].state, 'cancelled')


class TestGetSpotPriceHistory(AWSMockServiceTestCase):

    connection_class = EC2Connection

    def default_body(self):
        return b"""
              <DescribeSpotPriceHistoryResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-15/">
              <requestId>b6c6978c-bd13-4ad7-9bc8-6f0ac9d32bcc</requestId>
              <spotPriceHistorySet>
                <item>
                  <instanceType>c3.large</instanceType>
                  <productDescription>Linux/UNIX</productDescription>
                  <spotPrice>0.032000</spotPrice>
                  <timestamp>2013-12-28T12:17:43.000Z</timestamp>
                  <availabilityZone>us-west-2c</availabilityZone>
                </item>
                <item>
                  <instanceType>c3.large</instanceType>
                  <productDescription>Windows (Amazon VPC)</productDescription>
                  <spotPrice>0.104000</spotPrice>
                  <timestamp>2013-12-28T07:49:40.000Z</timestamp>
                  <availabilityZone>us-west-2b</availabilityZone>
                </item>
              </spotPriceHistorySet>
              <nextToken>q5GwEl5bMGjKq6YmhpDLJ7hEwyWU54jJC2GQ93n61vZV4s1+fzZ674xzvUlTihrl</nextToken>
            </DescribeSpotPriceHistoryResponse>
        """

    def test_get_spot_price_history(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_spot_price_history(
            instance_type='c3.large')
        self.assert_request_parameters({
            'Action': 'DescribeSpotPriceHistory',
            'InstanceType': 'c3.large'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(len(response), 2)
        self.assertEqual(response.next_token,
                         'q5GwEl5bMGjKq6YmhpDLJ7hEwyWU54jJC2GQ93n61vZV4s1+fzZ674xzvUlTihrl')
        self.assertEqual(response.nextToken,
                         'q5GwEl5bMGjKq6YmhpDLJ7hEwyWU54jJC2GQ93n61vZV4s1+fzZ674xzvUlTihrl')
        self.assertEqual(response[0].instance_type, 'c3.large')
        self.assertEqual(response[0].availability_zone, 'us-west-2c')
        self.assertEqual(response[1].instance_type, 'c3.large')
        self.assertEqual(response[1].availability_zone, 'us-west-2b')

        response = self.service_connection.get_spot_price_history(
            filters={'instance-type': 'c3.large'})
        self.assert_request_parameters({
            'Action': 'DescribeSpotPriceHistory',
            'Filter.1.Name': 'instance-type',
            'Filter.1.Value.1': 'c3.large'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

        response = self.service_connection.get_spot_price_history(
            next_token='foobar')
        self.assert_request_parameters({
            'Action': 'DescribeSpotPriceHistory',
            'NextToken': 'foobar'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
