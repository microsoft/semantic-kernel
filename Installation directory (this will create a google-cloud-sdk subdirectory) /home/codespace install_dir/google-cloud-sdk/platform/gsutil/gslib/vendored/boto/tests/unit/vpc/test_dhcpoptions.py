from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.vpc import VPCConnection, DhcpOptions


class TestDescribeDhcpOptions(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DescribeDhcpOptionsResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
              <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
              <dhcpOptionsSet>
                <item>
                  <dhcpOptionsId>dopt-7a8b9c2d</dhcpOptionsId>
                  <dhcpConfigurationSet>
                    <item>
                      <key>domain-name</key>
                      <valueSet>
                        <item>
                          <value>example.com</value>
                        </item>
                      </valueSet>
                    </item>
                    <item>
                      <key>domain-name-servers</key>
                      <valueSet>
                        <item>
                          <value>10.2.5.1</value>
                      </item>
                      </valueSet>
                    </item>
                    <item>
                      <key>domain-name-servers</key>
                      <valueSet>
                        <item>
                          <value>10.2.5.2</value>
                          </item>
                      </valueSet>
                    </item>
                  </dhcpConfigurationSet>
                  <tagSet/>
                </item>
              </dhcpOptionsSet>
            </DescribeDhcpOptionsResponse>
        """

    def test_get_all_dhcp_options(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.get_all_dhcp_options(['dopt-7a8b9c2d'],
                                                                    [('key', 'domain-name')])
        self.assert_request_parameters({
            'Action': 'DescribeDhcpOptions',
            'DhcpOptionsId.1': 'dopt-7a8b9c2d',
            'Filter.1.Name': 'key',
            'Filter.1.Value.1': 'domain-name'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(len(api_response), 1)
        self.assertIsInstance(api_response[0], DhcpOptions)
        self.assertEquals(api_response[0].id, 'dopt-7a8b9c2d')
        self.assertEquals(api_response[0].options['domain-name'], ['example.com'])
        self.assertEquals(api_response[0].options['domain-name-servers'], ['10.2.5.1', '10.2.5.2'])


class TestCreateDhcpOptions(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateDhcpOptionsResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
              <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
              <dhcpOptions>
                  <dhcpOptionsId>dopt-7a8b9c2d</dhcpOptionsId>
                  <dhcpConfigurationSet>
                    <item>
                      <key>domain-name</key>
                      <valueSet>
                        <item>
                          <value>example.com</value>
                        </item>
                      </valueSet>
                    </item>
                    <item>
                      <key>domain-name-servers</key>
                      <valueSet>
                        <item>
                          <value>10.2.5.1</value>
                        </item>
                        <item>
                          <value>10.2.5.2</value>
                        </item>
                      </valueSet>
                    </item>
                    <item>
                      <key>ntp-servers</key>
                      <valueSet>
                        <item>
                          <value>10.12.12.1</value>
                        </item>
                        <item>
                          <value>10.12.12.2</value>
                        </item>
                      </valueSet>
                    </item>
                    <item>
                      <key>netbios-name-servers</key>
                      <valueSet>
                        <item>
                          <value>10.20.20.1</value>
                        </item>
                      </valueSet>
                    </item>
                    <item>
                      <key>netbios-node-type</key>
                      <valueSet>
                        <item>
                          <value>2</value>
                        </item>
                      </valueSet>
                    </item>
                  </dhcpConfigurationSet>
                  <tagSet/>
              </dhcpOptions>
            </CreateDhcpOptionsResponse>
        """

    def test_create_dhcp_options(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_dhcp_options(
            domain_name='example.com', domain_name_servers=['10.2.5.1', '10.2.5.2'],
            ntp_servers=('10.12.12.1', '10.12.12.2'),
            netbios_name_servers='10.20.20.1',
            netbios_node_type='2')
        self.assert_request_parameters({
            'Action': 'CreateDhcpOptions',
            'DhcpConfiguration.1.Key': 'domain-name',
            'DhcpConfiguration.1.Value.1': 'example.com',
            'DhcpConfiguration.2.Key': 'domain-name-servers',
            'DhcpConfiguration.2.Value.1': '10.2.5.1',
            'DhcpConfiguration.2.Value.2': '10.2.5.2',
            'DhcpConfiguration.3.Key': 'ntp-servers',
            'DhcpConfiguration.3.Value.1': '10.12.12.1',
            'DhcpConfiguration.3.Value.2': '10.12.12.2',
            'DhcpConfiguration.4.Key': 'netbios-name-servers',
            'DhcpConfiguration.4.Value.1': '10.20.20.1',
            'DhcpConfiguration.5.Key': 'netbios-node-type',
            'DhcpConfiguration.5.Value.1': '2'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertIsInstance(api_response, DhcpOptions)
        self.assertEquals(api_response.id, 'dopt-7a8b9c2d')
        self.assertEquals(api_response.options['domain-name'], ['example.com'])
        self.assertEquals(api_response.options['domain-name-servers'], ['10.2.5.1', '10.2.5.2'])
        self.assertEquals(api_response.options['ntp-servers'], ['10.12.12.1', '10.12.12.2'])
        self.assertEquals(api_response.options['netbios-name-servers'], ['10.20.20.1'])
        self.assertEquals(api_response.options['netbios-node-type'], ['2'])


class TestDeleteDhcpOptions(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteDhcpOptionsResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <return>true</return>
            </DeleteDhcpOptionsResponse>
        """

    def test_delete_dhcp_options(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_dhcp_options('dopt-7a8b9c2d')
        self.assert_request_parameters({
            'Action': 'DeleteDhcpOptions',
            'DhcpOptionsId': 'dopt-7a8b9c2d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


class TestAssociateDhcpOptions(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <AssociateDhcpOptionsResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
               <return>true</return>
            </AssociateDhcpOptionsResponse>
        """

    def test_associate_dhcp_options(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.associate_dhcp_options(
            'dopt-7a8b9c2d', 'vpc-1a2b3c4d')
        self.assert_request_parameters({
            'Action': 'AssociateDhcpOptions',
            'DhcpOptionsId': 'dopt-7a8b9c2d',
            'VpcId': 'vpc-1a2b3c4d'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

if __name__ == '__main__':
    unittest.main()
