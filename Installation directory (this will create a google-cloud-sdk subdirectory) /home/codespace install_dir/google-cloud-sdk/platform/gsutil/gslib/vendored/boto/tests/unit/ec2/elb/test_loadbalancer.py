#!/usr/bin/env python

from tests.unit import unittest
from tests.compat import mock

from boto.ec2.elb import ELBConnection
from boto.ec2.elb import LoadBalancer

DISABLE_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<DisableAvailabilityZonesForLoadBalancerResult xmlns="http://ec2.amazonaws.com/doc/2013-02-01/">
    <requestId>3be1508e-c444-4fef-89cc-0b1223c4f02fEXAMPLE</requestId>
    <AvailabilityZones>
        <member>sample-zone</member>
    </AvailabilityZones>
</DisableAvailabilityZonesForLoadBalancerResult>
"""


class TestInstanceStatusResponseParsing(unittest.TestCase):
    def test_next_token(self):
        elb = ELBConnection(aws_access_key_id='aws_access_key_id',
                            aws_secret_access_key='aws_secret_access_key')
        mock_response = mock.Mock()
        mock_response.read.return_value = DISABLE_RESPONSE
        mock_response.status = 200
        elb.make_request = mock.Mock(return_value=mock_response)
        disabled = elb.disable_availability_zones('mine', ['sample-zone'])
        self.assertEqual(disabled, ['sample-zone'])


DESCRIBE_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<DescribeLoadBalancersResponse xmlns="http://elasticloadbalancing.amazonaws.com/doc/2012-06-01/">
  <DescribeLoadBalancersResult>
    <LoadBalancerDescriptions>
      <member>
        <SecurityGroups/>
        <CreatedTime>2013-07-09T19:18:00.520Z</CreatedTime>
        <LoadBalancerName>elb-boto-unit-test</LoadBalancerName>
        <HealthCheck/>
        <ListenerDescriptions>
          <member>
            <PolicyNames/>
            <Listener/>
          </member>
        </ListenerDescriptions>
        <Instances/>
        <Policies>
          <AppCookieStickinessPolicies/>
          <OtherPolicies>
            <member>AWSConsole-SSLNegotiationPolicy-my-test-loadbalancer</member>
            <member>EnableProxyProtocol</member>
          </OtherPolicies>
          <LBCookieStickinessPolicies/>
        </Policies>
        <AvailabilityZones>
          <member>us-east-1a</member>
        </AvailabilityZones>
        <CanonicalHostedZoneName>elb-boto-unit-test-408121642.us-east-1.elb.amazonaws.com</CanonicalHostedZoneName>
        <CanonicalHostedZoneNameID>Z3DZXE0Q79N41H</CanonicalHostedZoneNameID>
        <Scheme>internet-facing</Scheme>
        <SourceSecurityGroup>
          <OwnerAlias>amazon-elb</OwnerAlias>
          <GroupName>amazon-elb-sg</GroupName>
        </SourceSecurityGroup>
        <DNSName>elb-boto-unit-test-408121642.us-east-1.elb.amazonaws.com</DNSName>
        <BackendServerDescriptions>
          <member>
            <PolicyNames>
              <member>EnableProxyProtocol</member>
            </PolicyNames>
            <InstancePort>80</InstancePort>
          </member>
        </BackendServerDescriptions>
        <Subnets/>
      </member>
    </LoadBalancerDescriptions>
    <Marker>1234</Marker>
  </DescribeLoadBalancersResult>
  <ResponseMetadata>
    <RequestId>5763d932-e8cc-11e2-a940-11136cceffb8</RequestId>
  </ResponseMetadata>
</DescribeLoadBalancersResponse>
"""


class TestDescribeLoadBalancers(unittest.TestCase):
    def test_other_policy(self):
        elb = ELBConnection(aws_access_key_id='aws_access_key_id',
                            aws_secret_access_key='aws_secret_access_key')
        mock_response = mock.Mock()
        mock_response.read.return_value = DESCRIBE_RESPONSE
        mock_response.status = 200
        elb.make_request = mock.Mock(return_value=mock_response)
        load_balancers = elb.get_all_load_balancers()
        self.assertEqual(len(load_balancers), 1)

        lb = load_balancers[0]
        self.assertEqual(len(lb.policies.other_policies), 2)
        self.assertEqual(lb.policies.other_policies[0].policy_name,
                         'AWSConsole-SSLNegotiationPolicy-my-test-loadbalancer')
        self.assertEqual(lb.policies.other_policies[1].policy_name,
                         'EnableProxyProtocol')

        self.assertEqual(len(lb.backends), 1)
        self.assertEqual(len(lb.backends[0].policies), 1)
        self.assertEqual(lb.backends[0].policies[0].policy_name,
                         'EnableProxyProtocol')
        self.assertEqual(lb.backends[0].instance_port, 80)

    def test_request_with_marker(self):
        elb = ELBConnection(aws_access_key_id='aws_access_key_id',
                            aws_secret_access_key='aws_secret_access_key')
        mock_response = mock.Mock()
        mock_response.read.return_value = DESCRIBE_RESPONSE
        mock_response.status = 200
        elb.make_request = mock.Mock(return_value=mock_response)
        load_balancers1 = elb.get_all_load_balancers()
        self.assertEqual('1234', load_balancers1.marker)
        load_balancers2 = elb.get_all_load_balancers(marker=load_balancers1.marker)
        self.assertEqual(len(load_balancers2), 1)


DETACH_RESPONSE = r"""<?xml version="1.0" encoding="UTF-8"?>
<DetachLoadBalancerFromSubnets xmlns="http://ec2.amazonaws.com/doc/2013-02-01/">
    <requestId>3be1508e-c444-4fef-89cc-0b1223c4f02fEXAMPLE</requestId>
</DetachLoadBalancerFromSubnets>
"""


class TestDetachSubnets(unittest.TestCase):
    def test_detach_subnets(self):
        elb = ELBConnection(aws_access_key_id='aws_access_key_id',
                            aws_secret_access_key='aws_secret_access_key')
        lb = LoadBalancer(elb, "mylb")

        mock_response = mock.Mock()
        mock_response.read.return_value = DETACH_RESPONSE
        mock_response.status = 200
        elb.make_request = mock.Mock(return_value=mock_response)
        lb.detach_subnets("s-xxx")

if __name__ == '__main__':
    unittest.main()
