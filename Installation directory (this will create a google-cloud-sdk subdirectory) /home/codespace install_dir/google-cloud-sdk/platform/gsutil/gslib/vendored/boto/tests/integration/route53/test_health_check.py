# Copyright (c) 2014 Tellybug, Matt Millar
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

from tests.integration.route53 import Route53TestCase

from boto.compat import six
from boto.route53.healthcheck import HealthCheck
from boto.route53.record import ResourceRecordSets


class TestRoute53HealthCheck(Route53TestCase):
    def test_create_health_check(self):
        hc = HealthCheck(ip_addr="54.217.7.118", port=80, hc_type="HTTP", resource_path="/testing")
        result = self.conn.create_health_check(hc)
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'Type'], 'HTTP')
        self.assertEquals(result[u'CreateHealthCheckResponse'][
                          u'HealthCheck'][u'HealthCheckConfig'][u'IPAddress'], '54.217.7.118')
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'Port'], '80')
        self.assertEquals(result[u'CreateHealthCheckResponse'][
                          u'HealthCheck'][u'HealthCheckConfig'][u'ResourcePath'], '/testing')
        self.conn.delete_health_check(result['CreateHealthCheckResponse']['HealthCheck']['Id'])

    def test_create_https_health_check(self):
        hc = HealthCheck(ip_addr="54.217.7.118", port=443, hc_type="HTTPS", resource_path="/testing")
        result = self.conn.create_health_check(hc)
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'Type'], 'HTTPS')
        self.assertEquals(result[u'CreateHealthCheckResponse'][
                          u'HealthCheck'][u'HealthCheckConfig'][u'IPAddress'], '54.217.7.118')
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'Port'], '443')
        self.assertEquals(result[u'CreateHealthCheckResponse'][
                          u'HealthCheck'][u'HealthCheckConfig'][u'ResourcePath'], '/testing')
        self.assertFalse('FullyQualifiedDomainName' in result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'])
        self.conn.delete_health_check(result['CreateHealthCheckResponse']['HealthCheck']['Id'])

    def test_create_https_health_check_fqdn(self):
        hc = HealthCheck(ip_addr=None, port=443, hc_type="HTTPS", resource_path="/", fqdn="google.com")
        result = self.conn.create_health_check(hc)
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'Type'], 'HTTPS')
        self.assertEquals(result[u'CreateHealthCheckResponse'][
                          u'HealthCheck'][u'HealthCheckConfig'][u'FullyQualifiedDomainName'], 'google.com')
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'Port'], '443')
        self.assertEquals(result[u'CreateHealthCheckResponse'][
                          u'HealthCheck'][u'HealthCheckConfig'][u'ResourcePath'], '/')
        self.assertFalse('IPAddress' in result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'])
        self.conn.delete_health_check(result['CreateHealthCheckResponse']['HealthCheck']['Id'])

    def test_create_and_list_health_check(self):
        hc = HealthCheck(ip_addr="54.217.7.118", port=80, hc_type="HTTP", resource_path="/testing")
        result1 = self.conn.create_health_check(hc)
        hc = HealthCheck(ip_addr="54.217.7.119", port=80, hc_type="HTTP", resource_path="/testing")
        result2 = self.conn.create_health_check(hc)
        result = self.conn.get_list_health_checks()
        self.assertTrue(len(result['ListHealthChecksResponse']['HealthChecks']) > 1)
        self.conn.delete_health_check(result1['CreateHealthCheckResponse']['HealthCheck']['Id'])
        self.conn.delete_health_check(result2['CreateHealthCheckResponse']['HealthCheck']['Id'])

    def test_delete_health_check(self):
        hc = HealthCheck(ip_addr="54.217.7.118", port=80, hc_type="HTTP", resource_path="/testing")
        result = self.conn.create_health_check(hc)
        hc_id = result['CreateHealthCheckResponse']['HealthCheck']['Id']
        result = self.conn.get_list_health_checks()
        found = False
        for hc in result['ListHealthChecksResponse']['HealthChecks']:
            if hc['Id'] == hc_id:
                found = True
                break
        self.assertTrue(found)
        result = self.conn.delete_health_check(hc_id)
        result = self.conn.get_list_health_checks()
        for hc in result['ListHealthChecksResponse']['HealthChecks']:
            self.assertFalse(hc['Id'] == hc_id)

    def test_create_health_check_string_match(self):
        hc = HealthCheck(ip_addr="54.217.7.118", port=80, hc_type="HTTP_STR_MATCH", resource_path="/testing", string_match="test")
        result = self.conn.create_health_check(hc)
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'Type'], 'HTTP_STR_MATCH')
        self.assertEquals(result[u'CreateHealthCheckResponse'][
                          u'HealthCheck'][u'HealthCheckConfig'][u'IPAddress'], '54.217.7.118')
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'Port'], '80')
        self.assertEquals(result[u'CreateHealthCheckResponse'][
                          u'HealthCheck'][u'HealthCheckConfig'][u'ResourcePath'], '/testing')
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'SearchString'], 'test')
        self.conn.delete_health_check(result['CreateHealthCheckResponse']['HealthCheck']['Id'])

    def test_create_health_check_https_string_match(self):
        hc = HealthCheck(ip_addr="54.217.7.118", port=80, hc_type="HTTPS_STR_MATCH", resource_path="/testing", string_match="test")
        result = self.conn.create_health_check(hc)
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'Type'], 'HTTPS_STR_MATCH')
        self.assertEquals(result[u'CreateHealthCheckResponse'][
                          u'HealthCheck'][u'HealthCheckConfig'][u'IPAddress'], '54.217.7.118')
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'Port'], '80')
        self.assertEquals(result[u'CreateHealthCheckResponse'][
                          u'HealthCheck'][u'HealthCheckConfig'][u'ResourcePath'], '/testing')
        self.assertEquals(result[u'CreateHealthCheckResponse'][u'HealthCheck'][u'HealthCheckConfig'][u'SearchString'], 'test')
        self.conn.delete_health_check(result['CreateHealthCheckResponse']['HealthCheck']['Id'])

    def test_create_resource_record_set(self):
        hc = HealthCheck(ip_addr="54.217.7.118", port=80, hc_type="HTTP", resource_path="/testing")
        result = self.conn.create_health_check(hc)
        records = ResourceRecordSets(
            connection=self.conn, hosted_zone_id=self.zone.id, comment='Create DNS entry for test')
        change = records.add_change('CREATE', 'unittest.%s.' % self.base_domain, 'A', ttl=30, identifier='test',
                                    weight=1, health_check=result['CreateHealthCheckResponse']['HealthCheck']['Id'])
        change.add_value("54.217.7.118")
        records.commit()

        records = ResourceRecordSets(self.conn, self.zone.id)
        deleted = records.add_change('DELETE', "unittest.%s." % self.base_domain, "A", ttl=30, identifier='test',
                                     weight=1, health_check=result['CreateHealthCheckResponse']['HealthCheck']['Id'])
        deleted.add_value('54.217.7.118')
        records.commit()

    def test_create_health_check_invalid_request_interval(self):
        """Test that health checks cannot be created with an invalid
        'request_interval'.

        """
        self.assertRaises(AttributeError, lambda: HealthCheck(**self.health_check_params(request_interval=5)))

    def test_create_health_check_invalid_failure_threshold(self):
        """
        Test that health checks cannot be created with an invalid
        'failure_threshold'.
        """
        self.assertRaises(AttributeError, lambda: HealthCheck(**self.health_check_params(failure_threshold=0)))
        self.assertRaises(AttributeError, lambda: HealthCheck(**self.health_check_params(failure_threshold=11)))

    def test_create_health_check_request_interval(self):
        hc_params = self.health_check_params(request_interval=10)
        hc = HealthCheck(**hc_params)
        result = self.conn.create_health_check(hc)
        hc_config = (result[u'CreateHealthCheckResponse']
                     [u'HealthCheck'][u'HealthCheckConfig'])
        self.assertEquals(hc_config[u'RequestInterval'],
                          six.text_type(hc_params['request_interval']))
        self.conn.delete_health_check(result['CreateHealthCheckResponse']['HealthCheck']['Id'])

    def test_create_health_check_failure_threshold(self):
        hc_params = self.health_check_params(failure_threshold=1)
        hc = HealthCheck(**hc_params)
        result = self.conn.create_health_check(hc)
        hc_config = (result[u'CreateHealthCheckResponse']
                     [u'HealthCheck'][u'HealthCheckConfig'])
        self.assertEquals(hc_config[u'FailureThreshold'],
                          six.text_type(hc_params['failure_threshold']))
        self.conn.delete_health_check(result['CreateHealthCheckResponse']['HealthCheck']['Id'])

    def health_check_params(self, **kwargs):
        params = {
            'ip_addr': "54.217.7.118",
            'port': 80,
            'hc_type': 'HTTP',
            'resource_path': '/testing',
        }
        params.update(kwargs)
        return params
