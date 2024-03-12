from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.cloudfront import CloudFrontConnection
from boto.cloudfront.distribution import Distribution, DistributionConfig, DistributionSummary
from boto.cloudfront.origin import CustomOrigin


class TestCloudFrontConnection(AWSMockServiceTestCase):
    connection_class = CloudFrontConnection

    def setUp(self):
        super(TestCloudFrontConnection, self).setUp()

    def test_get_all_distributions(self):
        body = b"""
        <DistributionList xmlns="http://cloudfront.amazonaws.com/doc/2010-11-01/">
            <Marker></Marker>
            <MaxItems>100</MaxItems>
            <IsTruncated>false</IsTruncated>
            <DistributionSummary>
                <Id>EEEEEEEEEEEEE</Id>
                <Status>InProgress</Status>
                <LastModifiedTime>2014-02-03T11:03:41.087Z</LastModifiedTime>
                <DomainName>abcdef12345678.cloudfront.net</DomainName>
                <CustomOrigin>
                    <DNSName>example.com</DNSName>
                    <HTTPPort>80</HTTPPort>
                    <HTTPSPort>443</HTTPSPort>
                    <OriginProtocolPolicy>http-only</OriginProtocolPolicy>
                </CustomOrigin>
                <CNAME>static.example.com</CNAME>
                <Enabled>true</Enabled>
            </DistributionSummary>
        </DistributionList>
        """
        self.set_http_response(status_code=200, body=body)
        response = self.service_connection.get_all_distributions()

        self.assertTrue(isinstance(response, list))
        self.assertEqual(len(response), 1)
        self.assertTrue(isinstance(response[0], DistributionSummary))
        self.assertEqual(response[0].id, "EEEEEEEEEEEEE")
        self.assertEqual(response[0].domain_name, "abcdef12345678.cloudfront.net")
        self.assertEqual(response[0].status, "InProgress")
        self.assertEqual(response[0].cnames, ["static.example.com"])
        self.assertEqual(response[0].enabled, True)
        self.assertTrue(isinstance(response[0].origin, CustomOrigin))
        self.assertEqual(response[0].origin.dns_name, "example.com")
        self.assertEqual(response[0].origin.http_port, 80)
        self.assertEqual(response[0].origin.https_port, 443)
        self.assertEqual(response[0].origin.origin_protocol_policy, 'http-only')

    def test_get_distribution_config(self):
        body = b"""
        <DistributionConfig xmlns="http://cloudfront.amazonaws.com/doc/2010-11-01/">
        <CustomOrigin>
            <DNSName>example.com</DNSName>
            <HTTPPort>80</HTTPPort>
            <HTTPSPort>443</HTTPSPort>
            <OriginProtocolPolicy>http-only</OriginProtocolPolicy>
        </CustomOrigin>
        <CallerReference>1234567890123</CallerReference>
        <CNAME>static.example.com</CNAME>
        <Enabled>true</Enabled>
        </DistributionConfig>
        """

        self.set_http_response(status_code=200, body=body, header={"Etag": "AABBCC"})
        response = self.service_connection.get_distribution_config('EEEEEEEEEEEEE')

        self.assertTrue(isinstance(response, DistributionConfig))
        self.assertTrue(isinstance(response.origin, CustomOrigin))
        self.assertEqual(response.origin.dns_name, "example.com")
        self.assertEqual(response.origin.http_port, 80)
        self.assertEqual(response.origin.https_port, 443)
        self.assertEqual(response.origin.origin_protocol_policy, "http-only")
        self.assertEqual(response.cnames, ["static.example.com"])
        self.assertTrue(response.enabled)
        self.assertEqual(response.etag, "AABBCC")

    def test_set_distribution_config(self):
        get_body = b"""
        <DistributionConfig xmlns="http://cloudfront.amazonaws.com/doc/2010-11-01/">
        <CustomOrigin>
            <DNSName>example.com</DNSName>
            <HTTPPort>80</HTTPPort>
            <HTTPSPort>443</HTTPSPort>
            <OriginProtocolPolicy>http-only</OriginProtocolPolicy>
        </CustomOrigin>
        <CallerReference>1234567890123</CallerReference>
        <CNAME>static.example.com</CNAME>
        <Enabled>true</Enabled>
        </DistributionConfig>
        """

        put_body = b"""
        <Distribution xmlns="http://cloudfront.amazonaws.com/doc/2010-11-01/">
            <Id>EEEEEE</Id>
            <Status>InProgress</Status>
            <LastModifiedTime>2014-02-04T10:47:53.493Z</LastModifiedTime>
            <InProgressInvalidationBatches>0</InProgressInvalidationBatches>
            <DomainName>d2000000000000.cloudfront.net</DomainName>
            <DistributionConfig>
                <CustomOrigin>
                    <DNSName>example.com</DNSName>
                    <HTTPPort>80</HTTPPort>
                    <HTTPSPort>443</HTTPSPort>
                    <OriginProtocolPolicy>match-viewer</OriginProtocolPolicy>
                </CustomOrigin>
                <CallerReference>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</CallerReference>
                <Comment>this is a comment</Comment>
                <Enabled>false</Enabled>
            </DistributionConfig>
        </Distribution>
        """

        self.set_http_response(status_code=200, body=get_body, header={"Etag": "AA"})
        conf = self.service_connection.get_distribution_config('EEEEEEE')

        self.set_http_response(status_code=200, body=put_body, header={"Etag": "AABBCCD"})
        conf.comment = 'this is a comment'
        response = self.service_connection.set_distribution_config('EEEEEEE', conf.etag, conf)

        self.assertEqual(response, "AABBCCD")

    def test_get_distribution_info(self):
        body = b"""
        <Distribution xmlns="http://cloudfront.amazonaws.com/doc/2010-11-01/">
            <Id>EEEEEEEEEEEEE</Id>
            <Status>InProgress</Status>
            <LastModifiedTime>2014-02-03T11:03:41.087Z</LastModifiedTime>
            <InProgressInvalidationBatches>0</InProgressInvalidationBatches>
            <DomainName>abcdef12345678.cloudfront.net</DomainName>
            <DistributionConfig>
                <CustomOrigin>
                    <DNSName>example.com</DNSName>
                    <HTTPPort>80</HTTPPort>
                    <HTTPSPort>443</HTTPSPort>
                    <OriginProtocolPolicy>http-only</OriginProtocolPolicy>
                </CustomOrigin>
                <CallerReference>1111111111111</CallerReference>
                <CNAME>static.example.com</CNAME>
                <Enabled>true</Enabled>
            </DistributionConfig>
        </Distribution>
        """

        self.set_http_response(status_code=200, body=body)
        response = self.service_connection.get_distribution_info('EEEEEEEEEEEEE')

        self.assertTrue(isinstance(response, Distribution))
        self.assertTrue(isinstance(response.config, DistributionConfig))
        self.assertTrue(isinstance(response.config.origin, CustomOrigin))
        self.assertEqual(response.config.origin.dns_name, "example.com")
        self.assertEqual(response.config.origin.http_port, 80)
        self.assertEqual(response.config.origin.https_port, 443)
        self.assertEqual(response.config.origin.origin_protocol_policy, "http-only")
        self.assertEqual(response.config.cnames, ["static.example.com"])
        self.assertTrue(response.config.enabled)
        self.assertEqual(response.id, "EEEEEEEEEEEEE")
        self.assertEqual(response.status, "InProgress")
        self.assertEqual(response.domain_name, "abcdef12345678.cloudfront.net")
        self.assertEqual(response.in_progress_invalidation_batches, 0)

    def test_create_distribution(self):
        body = b"""
        <Distribution xmlns="http://cloudfront.amazonaws.com/doc/2010-11-01/">
            <Id>EEEEEEEEEEEEEE</Id>
            <Status>InProgress</Status>
            <LastModifiedTime>2014-02-04T10:34:07.873Z</LastModifiedTime>
            <InProgressInvalidationBatches>0</InProgressInvalidationBatches>
            <DomainName>d2000000000000.cloudfront.net</DomainName>
            <DistributionConfig>
                <CustomOrigin>
                    <DNSName>example.com</DNSName>
                    <HTTPPort>80</HTTPPort>
                    <HTTPSPort>443</HTTPSPort>
                    <OriginProtocolPolicy>match-viewer</OriginProtocolPolicy>
                </CustomOrigin>
                <CallerReference>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</CallerReference>
                <Comment>example.com distribution</Comment>
                <Enabled>false</Enabled>
            </DistributionConfig>
        </Distribution>
        """

        self.set_http_response(status_code=201, body=body)
        origin = CustomOrigin("example.com", origin_protocol_policy="match_viewer")
        response = self.service_connection.create_distribution(origin, enabled=False, comment="example.com distribution")

        self.assertTrue(isinstance(response, Distribution))
        self.assertTrue(isinstance(response.config, DistributionConfig))
        self.assertTrue(isinstance(response.config.origin, CustomOrigin))
        self.assertEqual(response.config.origin.dns_name, "example.com")
        self.assertEqual(response.config.origin.http_port, 80)
        self.assertEqual(response.config.origin.https_port, 443)
        self.assertEqual(response.config.origin.origin_protocol_policy, "match-viewer")
        self.assertEqual(response.config.cnames, [])
        self.assertTrue(not response.config.enabled)
        self.assertEqual(response.id, "EEEEEEEEEEEEEE")
        self.assertEqual(response.status, "InProgress")
        self.assertEqual(response.domain_name, "d2000000000000.cloudfront.net")
        self.assertEqual(response.in_progress_invalidation_batches, 0)
