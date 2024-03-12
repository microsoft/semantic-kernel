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
from tests.compat import mock
import re
import xml.dom.minidom
from boto.exception import BotoServerError
from boto.route53.connection import Route53Connection
from boto.route53.exception import DNSServerError
from boto.route53.healthcheck import HealthCheck
from boto.route53.record import ResourceRecordSets, Record
from boto.route53.zone import Zone

from nose.plugins.attrib import attr
from tests.unit import AWSMockServiceTestCase
from boto.compat import six
urllib = six.moves.urllib


@attr(route53=True)
class TestRoute53Connection(AWSMockServiceTestCase):
    connection_class = Route53Connection

    def setUp(self):
        super(TestRoute53Connection, self).setUp()
        self.calls = {
            'count': 0,
        }

    def default_body(self):
        return b"""<Route53Result>
    <Message>It failed.</Message>
</Route53Result>
"""

    def test_typical_400(self):
        self.set_http_response(status_code=400, header=[
            ['Code', 'AccessDenied'],
        ])

        with self.assertRaises(DNSServerError) as err:
            self.service_connection.get_all_hosted_zones()

        self.assertTrue('It failed.' in str(err.exception))

    def test_retryable_400_prior_request_not_complete(self):
        # Test ability to retry on ``PriorRequestNotComplete``.
        self.set_http_response(status_code=400, body="""<?xml version="1.0"?>
<ErrorResponse xmlns="https://route53.amazonaws.com/doc/2013-04-01/"><Error><Type>Sender</Type><Code>PriorRequestNotComplete</Code><Message>The request was rejected because Route 53 was still processing a prior request.</Message></Error><RequestId>12d222a0-f3d9-11e4-a611-c321a3a00f9c</RequestId></ErrorResponse>
""")
        self.do_retry_handler()

    def test_retryable_400_throttling(self):
        # Test ability to rety on ``Throttling``.
        self.set_http_response(status_code=400, body="""<?xml version="1.0"?>
<ErrorResponse xmlns="https://route53.amazonaws.com/doc/2013-04-01/"><Error><Type>Sender</Type><Code>Throttling</Code><Message>Rate exceeded</Message></Error><RequestId>19d0a9a0-f3d9-11e4-a611-c321a3a00f9c</RequestId></ErrorResponse>
""")
        self.do_retry_handler()

    @mock.patch('time.sleep')
    def do_retry_handler(self, sleep_mock):

        def incr_retry_handler(func):
            def _wrapper(*args, **kwargs):
                self.calls['count'] += 1
                return func(*args, **kwargs)
            return _wrapper

        # Patch.
        orig_retry = self.service_connection._retry_handler
        self.service_connection._retry_handler = incr_retry_handler(
            orig_retry
        )
        self.assertEqual(self.calls['count'], 0)

        # Retries get exhausted.
        with self.assertRaises(BotoServerError):
            self.service_connection.get_all_hosted_zones()

        self.assertEqual(self.calls['count'], 7)

        # Unpatch.
        self.service_connection._retry_handler = orig_retry

    def test_private_zone_invalid_vpc_400(self):
        self.set_http_response(status_code=400, header=[
            ['Code', 'InvalidVPCId'],
        ])

        with self.assertRaises(DNSServerError) as err:
            self.service_connection.create_hosted_zone("example.com.",
                                                       private_zone=True)
        self.assertTrue('It failed.' in str(err.exception))


@attr(route53=True)
class TestCreateZoneRoute53(AWSMockServiceTestCase):
    connection_class = Route53Connection

    def setUp(self):
        super(TestCreateZoneRoute53, self).setUp()

    def default_body(self):
        return b"""
<CreateHostedZoneResponse xmlns="https://route53.amazonaws.com/doc/2012-02-29/">
    <HostedZone>
        <Id>/hostedzone/Z11111</Id>
        <Name>example.com.</Name>
        <CallerReference>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</CallerReference>
        <Config>
            <Comment></Comment>
            <PrivateZone>false</PrivateZone>
        </Config>
        <ResourceRecordSetCount>2</ResourceRecordSetCount>
    </HostedZone>
    <ChangeInfo>
        <Id>/change/C1111111111111</Id>
        <Status>PENDING</Status>
        <SubmittedAt>2014-02-02T10:19:29.928Z</SubmittedAt>
    </ChangeInfo>
    <DelegationSet>
        <NameServers>
            <NameServer>ns-100.awsdns-01.com</NameServer>
            <NameServer>ns-1000.awsdns-01.co.uk</NameServer>
            <NameServer>ns-1000.awsdns-01.org</NameServer>
            <NameServer>ns-900.awsdns-01.net</NameServer>
        </NameServers>
    </DelegationSet>
</CreateHostedZoneResponse>
        """

    def test_create_zone(self):
        self.set_http_response(status_code=201)
        response = self.service_connection.create_zone("example.com.")

        self.assertTrue(isinstance(response, Zone))
        self.assertEqual(response.id, "Z11111")
        self.assertEqual(response.name, "example.com.")

    def test_create_hosted_zone(self):
        self.set_http_response(status_code=201)
        response = self.service_connection.create_hosted_zone("example.com.",
                                                              "my_ref",
                                                              "a comment")

        self.assertEqual(response['CreateHostedZoneResponse']
                                 ['DelegationSet']['NameServers'],
                                 ['ns-100.awsdns-01.com',
                                  'ns-1000.awsdns-01.co.uk',
                                  'ns-1000.awsdns-01.org',
                                  'ns-900.awsdns-01.net'])

        self.assertEqual(response['CreateHostedZoneResponse']
                                 ['HostedZone']['Config']['PrivateZone'],
                         u'false')


@attr(route53=True)
class TestCreatePrivateZoneRoute53(AWSMockServiceTestCase):
    connection_class = Route53Connection

    def setUp(self):
        super(TestCreatePrivateZoneRoute53, self).setUp()

    def default_body(self):
        return b"""
<CreateHostedZoneResponse xmlns="https://route53.amazonaws.com/doc/2012-02-29/">
    <HostedZone>
        <Id>/hostedzone/Z11111</Id>
        <Name>example.com.</Name>
        <VPC>
           <VPCId>vpc-1a2b3c4d</VPCId>
           <VPCRegion>us-east-1</VPCRegion>
        </VPC>
        <CallerReference>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</CallerReference>
        <Config>
            <Comment></Comment>
            <PrivateZone>true</PrivateZone>
        </Config>
        <ResourceRecordSetCount>2</ResourceRecordSetCount>
    </HostedZone>
    <ChangeInfo>
        <Id>/change/C1111111111111</Id>
        <Status>PENDING</Status>
        <SubmittedAt>2014-02-02T10:19:29.928Z</SubmittedAt>
    </ChangeInfo>
    <DelegationSet>
        <NameServers>
            <NameServer>ns-100.awsdns-01.com</NameServer>
            <NameServer>ns-1000.awsdns-01.co.uk</NameServer>
            <NameServer>ns-1000.awsdns-01.org</NameServer>
            <NameServer>ns-900.awsdns-01.net</NameServer>
        </NameServers>
    </DelegationSet>
</CreateHostedZoneResponse>
        """

    def test_create_private_zone(self):
        self.set_http_response(status_code=201)
        r = self.service_connection.create_hosted_zone("example.com.",
                                                       private_zone=True,
                                                       vpc_id='vpc-1a2b3c4d',
                                                       vpc_region='us-east-1'
                                                       )

        self.assertEqual(r['CreateHostedZoneResponse']['HostedZone']
                          ['Config']['PrivateZone'], u'true')
        self.assertEqual(r['CreateHostedZoneResponse']['HostedZone']
                          ['VPC']['VPCId'], u'vpc-1a2b3c4d')
        self.assertEqual(r['CreateHostedZoneResponse']['HostedZone']
                          ['VPC']['VPCRegion'], u'us-east-1')


@attr(route53=True)
class TestGetZoneRoute53(AWSMockServiceTestCase):
    connection_class = Route53Connection

    def setUp(self):
        super(TestGetZoneRoute53, self).setUp()

    def default_body(self):
        return b"""
<ListHostedZonesResponse xmlns="https://route53.amazonaws.com/doc/2012-02-29/">
    <HostedZones>
        <HostedZone>
            <Id>/hostedzone/Z1111</Id>
            <Name>example2.com.</Name>
            <CallerReference>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</CallerReference>
            <Config/>
            <ResourceRecordSetCount>3</ResourceRecordSetCount>
        </HostedZone>
        <HostedZone>
            <Id>/hostedzone/Z2222</Id>
            <Name>example1.com.</Name>
            <CallerReference>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeef</CallerReference>
            <Config/>
            <ResourceRecordSetCount>6</ResourceRecordSetCount>
        </HostedZone>
        <HostedZone>
            <Id>/hostedzone/Z3333</Id>
            <Name>example.com.</Name>
            <CallerReference>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeeg</CallerReference>
            <Config/>
            <ResourceRecordSetCount>6</ResourceRecordSetCount>
        </HostedZone>
    </HostedZones>
    <IsTruncated>false</IsTruncated>
    <MaxItems>100</MaxItems>
</ListHostedZonesResponse>
        """

    def test_list_zones(self):
        self.set_http_response(status_code=201)
        response = self.service_connection.get_all_hosted_zones()

        domains = ['example2.com.', 'example1.com.', 'example.com.']
        print(response['ListHostedZonesResponse']['HostedZones'][0])
        for d in response['ListHostedZonesResponse']['HostedZones']:
            print("Removing: %s" % d['Name'])
            domains.remove(d['Name'])

        self.assertEqual(domains, [])

    def test_get_zone(self):
        self.set_http_response(status_code=201)
        response = self.service_connection.get_zone('example.com.')

        self.assertTrue(isinstance(response, Zone))
        self.assertEqual(response.name, "example.com.")


@attr(route53=True)
class TestGetHostedZoneRoute53(AWSMockServiceTestCase):
    connection_class = Route53Connection

    def setUp(self):
        super(TestGetHostedZoneRoute53, self).setUp()

    def default_body(self):
        return b"""
<GetHostedZoneResponse xmlns="https://route53.amazonaws.com/doc/2012-02-29/">
    <HostedZone>
        <Id>/hostedzone/Z1111</Id>
        <Name>example.com.</Name>
        <CallerReference>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</CallerReference>
        <Config/>
        <ResourceRecordSetCount>3</ResourceRecordSetCount>
    </HostedZone>
    <DelegationSet>
        <NameServers>
            <NameServer>ns-1000.awsdns-40.org</NameServer>
            <NameServer>ns-200.awsdns-30.com</NameServer>
            <NameServer>ns-900.awsdns-50.net</NameServer>
            <NameServer>ns-1000.awsdns-00.co.uk</NameServer>
        </NameServers>
    </DelegationSet>
</GetHostedZoneResponse>
"""

    def test_list_zones(self):
        self.set_http_response(status_code=201)
        response = self.service_connection.get_hosted_zone("Z1111")

        self.assertEqual(response['GetHostedZoneResponse']
                                 ['HostedZone']['Id'],
                         '/hostedzone/Z1111')
        self.assertEqual(response['GetHostedZoneResponse']
                                 ['HostedZone']['Name'],
                         'example.com.')
        self.assertEqual(response['GetHostedZoneResponse']
                                 ['DelegationSet']['NameServers'],
                         ['ns-1000.awsdns-40.org', 'ns-200.awsdns-30.com',
                          'ns-900.awsdns-50.net', 'ns-1000.awsdns-00.co.uk'])


@attr(route53=True)
class TestGetAllRRSetsRoute53(AWSMockServiceTestCase):
    connection_class = Route53Connection

    def setUp(self):
        super(TestGetAllRRSetsRoute53, self).setUp()

    def default_body(self):
        return b"""
<ListResourceRecordSetsResponse xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
    <ResourceRecordSets>
        <ResourceRecordSet>
            <Name>test.example.com.</Name>
            <Type>A</Type>
            <TTL>60</TTL>
            <ResourceRecords>
                <ResourceRecord>
                    <Value>10.0.0.1</Value>
                </ResourceRecord>
            </ResourceRecords>
        </ResourceRecordSet>
        <ResourceRecordSet>
            <Name>www.example.com.</Name>
            <Type>A</Type>
            <TTL>60</TTL>
            <ResourceRecords>
                <ResourceRecord>
                    <Value>10.0.0.2</Value>
                </ResourceRecord>
            </ResourceRecords>
        </ResourceRecordSet>
        <ResourceRecordSet>
            <Name>us-west-2-evaluate-health.example.com.</Name>
            <Type>A</Type>
            <SetIdentifier>latency-example-us-west-2-evaluate-health</SetIdentifier>
            <Region>us-west-2</Region>
            <AliasTarget>
                <HostedZoneId>ABCDEFG123456</HostedZoneId>
                <EvaluateTargetHealth>true</EvaluateTargetHealth>
                <DNSName>example-123456-evaluate-health.us-west-2.elb.amazonaws.com.</DNSName>
            </AliasTarget>
            <HealthCheckId>abcdefgh-abcd-abcd-abcd-abcdefghijkl</HealthCheckId>
        </ResourceRecordSet>
        <ResourceRecordSet>
            <Name>us-west-2-no-evaluate-health.example.com.</Name>
            <Type>A</Type>
            <SetIdentifier>latency-example-us-west-2-no-evaluate-health</SetIdentifier>
            <Region>us-west-2</Region>
            <AliasTarget>
                <HostedZoneId>ABCDEFG567890</HostedZoneId>
                <EvaluateTargetHealth>false</EvaluateTargetHealth>
                <DNSName>example-123456-no-evaluate-health.us-west-2.elb.amazonaws.com.</DNSName>
            </AliasTarget>
            <HealthCheckId>abcdefgh-abcd-abcd-abcd-abcdefghijkl</HealthCheckId>
        </ResourceRecordSet>
        <ResourceRecordSet>
            <Name>failover.example.com.</Name>
            <Type>A</Type>
            <SetIdentifier>failover-primary</SetIdentifier>
            <Failover>PRIMARY</Failover>
            <TTL>60</TTL>
            <ResourceRecords>
                <ResourceRecord>
                    <Value>10.0.0.4</Value>
                </ResourceRecord>
            </ResourceRecords>
        </ResourceRecordSet>
        <ResourceRecordSet>
            <Name>us-west-2-evaluate-health-healthcheck.example.com.</Name>
            <Type>A</Type>
            <SetIdentifier>latency-example-us-west-2-evaluate-health-healthcheck</SetIdentifier>
            <Region>us-west-2</Region>
            <AliasTarget>
                <HostedZoneId>ABCDEFG123456</HostedZoneId>
                <EvaluateTargetHealth>true</EvaluateTargetHealth>
                <DNSName>example-123456-evaluate-health-healthcheck.us-west-2.elb.amazonaws.com.</DNSName>
            </AliasTarget>
            <HealthCheckId>076a32f8-86f7-4c9e-9fa2-c163d5be67d9</HealthCheckId>
        </ResourceRecordSet>
    </ResourceRecordSets>
    <IsTruncated>false</IsTruncated>
    <MaxItems>100</MaxItems>
</ListResourceRecordSetsResponse>
        """

    def test_get_all_rr_sets(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_all_rrsets("Z1111",
                                                          "A",
                                                          "example.com.")

        self.assertIn(self.actual_request.path,
                      ("/2013-04-01/hostedzone/Z1111/rrset?type=A&name=example.com.",
                       "/2013-04-01/hostedzone/Z1111/rrset?name=example.com.&type=A"))

        self.assertTrue(isinstance(response, ResourceRecordSets))
        self.assertEqual(response.hosted_zone_id, "Z1111")
        self.assertTrue(isinstance(response[0], Record))

        self.assertTrue(response[0].name, "test.example.com.")
        self.assertTrue(response[0].ttl, "60")
        self.assertTrue(response[0].type, "A")

        evaluate_record = response[2]
        self.assertEqual(evaluate_record.name, 'us-west-2-evaluate-health.example.com.')
        self.assertEqual(evaluate_record.type, 'A')
        self.assertEqual(evaluate_record.identifier, 'latency-example-us-west-2-evaluate-health')
        self.assertEqual(evaluate_record.region, 'us-west-2')
        self.assertEqual(evaluate_record.alias_hosted_zone_id, 'ABCDEFG123456')
        self.assertTrue(evaluate_record.alias_evaluate_target_health)
        self.assertEqual(evaluate_record.alias_dns_name, 'example-123456-evaluate-health.us-west-2.elb.amazonaws.com.')
        evaluate_xml = evaluate_record.to_xml()
        self.assertTrue(evaluate_record.health_check, 'abcdefgh-abcd-abcd-abcd-abcdefghijkl')
        self.assertTrue('<EvaluateTargetHealth>true</EvaluateTargetHealth>' in evaluate_xml)

        no_evaluate_record = response[3]
        self.assertEqual(no_evaluate_record.name, 'us-west-2-no-evaluate-health.example.com.')
        self.assertEqual(no_evaluate_record.type, 'A')
        self.assertEqual(no_evaluate_record.identifier, 'latency-example-us-west-2-no-evaluate-health')
        self.assertEqual(no_evaluate_record.region, 'us-west-2')
        self.assertEqual(no_evaluate_record.alias_hosted_zone_id, 'ABCDEFG567890')
        self.assertFalse(no_evaluate_record.alias_evaluate_target_health)
        self.assertEqual(no_evaluate_record.alias_dns_name, 'example-123456-no-evaluate-health.us-west-2.elb.amazonaws.com.')
        no_evaluate_xml = no_evaluate_record.to_xml()
        self.assertTrue(no_evaluate_record.health_check, 'abcdefgh-abcd-abcd-abcd-abcdefghijkl')
        self.assertTrue('<EvaluateTargetHealth>false</EvaluateTargetHealth>' in no_evaluate_xml)

        failover_record = response[4]
        self.assertEqual(failover_record.name, 'failover.example.com.')
        self.assertEqual(failover_record.type, 'A')
        self.assertEqual(failover_record.identifier, 'failover-primary')
        self.assertEqual(failover_record.failover, 'PRIMARY')
        self.assertEqual(failover_record.ttl, '60')

        healthcheck_record = response[5]
        self.assertEqual(healthcheck_record.health_check, '076a32f8-86f7-4c9e-9fa2-c163d5be67d9')
        self.assertEqual(healthcheck_record.name, 'us-west-2-evaluate-health-healthcheck.example.com.')
        self.assertEqual(healthcheck_record.identifier, 'latency-example-us-west-2-evaluate-health-healthcheck')
        self.assertEqual(healthcheck_record.alias_dns_name, 'example-123456-evaluate-health-healthcheck.us-west-2.elb.amazonaws.com.')


@attr(route53=True)
class TestTruncatedGetAllRRSetsRoute53(AWSMockServiceTestCase):
    connection_class = Route53Connection

    def setUp(self):
        super(TestTruncatedGetAllRRSetsRoute53, self).setUp()

    def default_body(self):
        return b"""
<ListResourceRecordSetsResponse xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
  <ResourceRecordSets>
    <ResourceRecordSet>
      <Name>example.com.</Name>
      <Type>NS</Type>
      <TTL>900</TTL>
      <ResourceRecords>
        <ResourceRecord>
          <Value>ns-91.awsdns-41.co.uk.</Value>
        </ResourceRecord>
        <ResourceRecord>
          <Value>ns-1929.awsdns-93.net.</Value>
        </ResourceRecord>
        <ResourceRecord>
          <Value>ns-12.awsdns-21.org.</Value>
        </ResourceRecord>
        <ResourceRecord>
          <Value>ns-102.awsdns-96.com.</Value>
        </ResourceRecord>
      </ResourceRecords>
    </ResourceRecordSet>
    <ResourceRecordSet>
      <Name>example.com.</Name>
      <Type>SOA</Type>
      <TTL>1800</TTL>
      <ResourceRecords>
        <ResourceRecord>
          <Value>ns-1929.awsdns-93.net. hostmaster.awsdns.net. 1 10800 3600 604800 1800</Value>
        </ResourceRecord>
      </ResourceRecords>
    </ResourceRecordSet>
    <ResourceRecordSet>
      <Name>wrr.example.com.</Name>
      <Type>A</Type>
      <SetIdentifier>primary</SetIdentifier>
      <Weight>100</Weight>
      <TTL>300</TTL>
      <ResourceRecords>
        <ResourceRecord><Value>127.0.0.1</Value></ResourceRecord>
      </ResourceRecords>
    </ResourceRecordSet>
  </ResourceRecordSets>
  <IsTruncated>true</IsTruncated>
  <NextRecordName>wrr.example.com.</NextRecordName>
  <NextRecordType>A</NextRecordType>
  <NextRecordIdentifier>secondary</NextRecordIdentifier>
  <MaxItems>3</MaxItems>
</ListResourceRecordSetsResponse>"""

    def paged_body(self):
        return b"""
<ListResourceRecordSetsResponse xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
  <ResourceRecordSets>
    <ResourceRecordSet>
      <Name>wrr.example.com.</Name>
      <Type>A</Type>
      <SetIdentifier>secondary</SetIdentifier>
      <Weight>50</Weight>
      <TTL>300</TTL>
      <ResourceRecords>
        <ResourceRecord><Value>127.0.0.2</Value></ResourceRecord>
      </ResourceRecords>
    </ResourceRecordSet>
  </ResourceRecordSets>
  <IsTruncated>false</IsTruncated>
  <MaxItems>3</MaxItems>
</ListResourceRecordSetsResponse>"""


    def test_get_all_rr_sets(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_all_rrsets("Z1111", maxitems=3)

        # made first request
        self.assertEqual(self.actual_request.path, '/2013-04-01/hostedzone/Z1111/rrset?maxitems=3')

        # anticipate a second request when we page it
        self.set_http_response(status_code=200, body=self.paged_body())

        # this should trigger another call to get_all_rrsets
        self.assertEqual(len(list(response)), 4)

        url_parts = urllib.parse.urlparse(self.actual_request.path)
        self.assertEqual(url_parts.path, '/2013-04-01/hostedzone/Z1111/rrset')
        self.assertEqual(urllib.parse.parse_qs(url_parts.query),
                         dict(type=['A'], name=['wrr.example.com.'], identifier=['secondary']))


@attr(route53=True)
class TestCreateHealthCheckRoute53IpAddress(AWSMockServiceTestCase):
    connection_class = Route53Connection

    def setUp(self):
        super(TestCreateHealthCheckRoute53IpAddress, self).setUp()

    def default_body(self):
        return b"""
<CreateHealthCheckResponse xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
   <HealthCheck>
      <Id>34778cf8-e31e-4974-bad0-b108bd1623d3</Id>
      <CallerReference>2fa48c8f-76ef-4253-9874-8bcb2b0d7694</CallerReference>
      <HealthCheckConfig>
         <IPAddress>74.125.228.81</IPAddress>
         <Port>443</Port>
         <Type>HTTPS_STR_MATCH</Type>
         <SearchString>OK</SearchString>
         <ResourcePath>/health_check</ResourcePath>
         <RequestInterval>30</RequestInterval>
         <FailureThreshold>3</FailureThreshold>
      </HealthCheckConfig>
   </HealthCheck>
</CreateHealthCheckResponse>
        """

    def test_create_health_check_ip_address(self):
        self.set_http_response(status_code=201)
        hc = HealthCheck(ip_addr='74.125.228.81', port=443, hc_type='HTTPS_STR_MATCH', resource_path='/health_check', string_match='OK')
        hc_xml = hc.to_xml()
        self.assertFalse('<FullyQualifiedDomainName>' in hc_xml)
        self.assertTrue('<IPAddress>' in hc_xml)

        response = self.service_connection.create_health_check(hc)
        hc_resp = response['CreateHealthCheckResponse']['HealthCheck']['HealthCheckConfig']
        self.assertEqual(hc_resp['IPAddress'], '74.125.228.81')
        self.assertEqual(hc_resp['ResourcePath'], '/health_check')
        self.assertEqual(hc_resp['Type'], 'HTTPS_STR_MATCH')
        self.assertEqual(hc_resp['Port'], '443')
        self.assertEqual(hc_resp['ResourcePath'], '/health_check')
        self.assertEqual(hc_resp['SearchString'], 'OK')
        self.assertEqual(response['CreateHealthCheckResponse']['HealthCheck']['Id'], '34778cf8-e31e-4974-bad0-b108bd1623d3')


@attr(route53=True)
class TestGetCheckerIpRanges(AWSMockServiceTestCase):
    connection_class = Route53Connection

    def default_body(self):
        return b"""
<GetCheckerIpRangesResponse xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
   <CheckerIpRanges>
      <member>54.183.255.128/26</member>
      <member>54.228.16.0/26</member>
      <member>54.232.40.64/26</member>
      <member>177.71.207.128/26</member>
      <member>176.34.159.192/26</member>
   </CheckerIpRanges>
</GetCheckerIpRangesResponse>
        """

    def test_get_checker_ip_ranges(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_checker_ip_ranges()
        ip_ranges = response['GetCheckerIpRangesResponse']['CheckerIpRanges']

        self.assertEqual(len(ip_ranges), 5)
        self.assertIn('54.183.255.128/26', ip_ranges)
        self.assertIn('54.228.16.0/26', ip_ranges)
        self.assertIn('54.232.40.64/26', ip_ranges)
        self.assertIn('177.71.207.128/26', ip_ranges)
        self.assertIn('176.34.159.192/26', ip_ranges)


@attr(route53=True)
class TestCreateHealthCheckRoute53FQDN(AWSMockServiceTestCase):
    connection_class = Route53Connection

    def setUp(self):
        super(TestCreateHealthCheckRoute53FQDN, self).setUp()

    def default_body(self):
        return b"""
<CreateHealthCheckResponse xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
   <HealthCheck>
      <Id>f9abfe10-8d2a-4bbd-8f35-796f0f8572f2</Id>
      <CallerReference>3246ac17-b651-4295-a5c8-c132a59693d7</CallerReference>
      <HealthCheckConfig>
         <Port>443</Port>
         <Type>HTTPS</Type>
         <ResourcePath>/health_check</ResourcePath>
         <FullyQualifiedDomainName>example.com</FullyQualifiedDomainName>
         <RequestInterval>30</RequestInterval>
         <FailureThreshold>3</FailureThreshold>
      </HealthCheckConfig>
   </HealthCheck>
</CreateHealthCheckResponse>
        """

    def test_create_health_check_fqdn(self):
        self.set_http_response(status_code=201)
        hc = HealthCheck(ip_addr='', port=443, hc_type='HTTPS', resource_path='/health_check', fqdn='example.com')
        hc_xml = hc.to_xml()
        self.assertTrue('<FullyQualifiedDomainName>' in hc_xml)
        self.assertFalse('<IPAddress>' in hc_xml)

        response = self.service_connection.create_health_check(hc)
        hc_resp = response['CreateHealthCheckResponse']['HealthCheck']['HealthCheckConfig']
        self.assertEqual(hc_resp['FullyQualifiedDomainName'], 'example.com')
        self.assertEqual(hc_resp['ResourcePath'], '/health_check')
        self.assertEqual(hc_resp['Type'], 'HTTPS')
        self.assertEqual(hc_resp['Port'], '443')
        self.assertEqual(hc_resp['ResourcePath'], '/health_check')
        self.assertEqual(response['CreateHealthCheckResponse']['HealthCheck']['Id'], 'f9abfe10-8d2a-4bbd-8f35-796f0f8572f2')


@attr(route53=True)
class TestChangeResourceRecordSetsRoute53(AWSMockServiceTestCase):
    connection_class = Route53Connection

    def setUp(self):
        super(TestChangeResourceRecordSetsRoute53, self).setUp()

    def default_body(self):
        return b"""
<ChangeResourceRecordSetsResponse xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
    <ChangeInfo>
        <Id>/change/C1111111111111</Id>
        <Status>PENDING</Status>
        <SubmittedAt>2014-05-05T10:11:12.123Z</SubmittedAt>
    </ChangeInfo>
</ChangeResourceRecordSetsResponse>
        """

    def test_record_commit(self):
        rrsets = ResourceRecordSets(self.service_connection)
        rrsets.add_change_record('CREATE', Record('vanilla.example.com', 'A', 60, ['1.2.3.4']))
        rrsets.add_change_record('CREATE', Record('alias.example.com', 'AAAA', alias_hosted_zone_id='Z123OTHER', alias_dns_name='target.other', alias_evaluate_target_health=True))
        rrsets.add_change_record('CREATE', Record('wrr.example.com', 'CNAME', 60, ['cname.target'], weight=10, identifier='weight-1'))
        rrsets.add_change_record('CREATE', Record('lbr.example.com', 'TXT', 60, ['text record'], region='us-west-2', identifier='region-1'))
        rrsets.add_change_record('CREATE', Record('failover.example.com', 'A', 60, ['2.2.2.2'], health_check='hc-1234', failover='PRIMARY', identifier='primary'))

        changes_xml = rrsets.to_xml()

        # the whitespacing doesn't match exactly, so we'll pretty print and drop all new lines
        # not the best, but
        actual_xml = re.sub(r"\s*[\r\n]+", "\n", xml.dom.minidom.parseString(changes_xml).toprettyxml())
        expected_xml = re.sub(r"\s*[\r\n]+", "\n", xml.dom.minidom.parseString(b"""
<ChangeResourceRecordSetsRequest xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
    <ChangeBatch>
        <Comment>None</Comment>
        <Changes>
            <Change>
                <Action>CREATE</Action>
                <ResourceRecordSet>
                    <Name>vanilla.example.com</Name>
                    <Type>A</Type>
                    <TTL>60</TTL>
                    <ResourceRecords>
                        <ResourceRecord>
                            <Value>1.2.3.4</Value>
                        </ResourceRecord>
                    </ResourceRecords>
                </ResourceRecordSet>
            </Change>
            <Change>
                <Action>CREATE</Action>
                <ResourceRecordSet>
                    <Name>alias.example.com</Name>
                    <Type>AAAA</Type>
                    <AliasTarget>
                        <HostedZoneId>Z123OTHER</HostedZoneId>
                        <DNSName>target.other</DNSName>
                        <EvaluateTargetHealth>true</EvaluateTargetHealth>
                    </AliasTarget>
                </ResourceRecordSet>
            </Change>
            <Change>
                <Action>CREATE</Action>
                <ResourceRecordSet>
                    <Name>wrr.example.com</Name>
                    <Type>CNAME</Type>
                    <SetIdentifier>weight-1</SetIdentifier>
                    <Weight>10</Weight>
                    <TTL>60</TTL>
                    <ResourceRecords>
                        <ResourceRecord>
                            <Value>cname.target</Value>
                        </ResourceRecord>
                    </ResourceRecords>
                </ResourceRecordSet>
            </Change>
            <Change>
                <Action>CREATE</Action>
                <ResourceRecordSet>
                    <Name>lbr.example.com</Name>
                    <Type>TXT</Type>
                    <SetIdentifier>region-1</SetIdentifier>
                    <Region>us-west-2</Region>
                    <TTL>60</TTL>
                    <ResourceRecords>
                        <ResourceRecord>
                            <Value>text record</Value>
                        </ResourceRecord>
                    </ResourceRecords>
                </ResourceRecordSet>
            </Change>
            <Change>
                <Action>CREATE</Action>
                <ResourceRecordSet>
                    <Name>failover.example.com</Name>
                    <Type>A</Type>
                    <SetIdentifier>primary</SetIdentifier>
                    <Failover>PRIMARY</Failover>
                    <TTL>60</TTL>
                    <ResourceRecords>
                        <ResourceRecord>
                            <Value>2.2.2.2</Value>
                        </ResourceRecord>
                    </ResourceRecords>
                    <HealthCheckId>hc-1234</HealthCheckId>
                </ResourceRecordSet>
            </Change>
        </Changes>
    </ChangeBatch>
</ChangeResourceRecordSetsRequest>
        """).toprettyxml())

        # Note: the alias XML should not include the TTL, even if it's specified in the object model
        self.assertEqual(actual_xml, expected_xml)
