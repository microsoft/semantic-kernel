from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.vpc import VPCConnection, InternetGateway


class TestDescribeInternetGateway(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DescribeInternetGatewaysResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <internetGatewaySet>
                  <item>
                     <internetGatewayId>igw-eaad4883EXAMPLE</internetGatewayId>
                     <attachmentSet>
                        <item>
                           <vpcId>vpc-11ad4878</vpcId>
                           <state>available</state>
                        </item>
                     </attachmentSet>
                     <tagSet/>
                  </item>
               </internetGatewaySet>
            </DescribeInternetGatewaysResponse>
        """

    def test_describe_internet_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.get_all_internet_gateways(
            'igw-eaad4883EXAMPLE', filters=[('attachment.state', ['available', 'pending'])])
        self.assert_request_parameters({
            'Action': 'DescribeInternetGateways',
            'InternetGatewayId.1': 'igw-eaad4883EXAMPLE',
            'Filter.1.Name': 'attachment.state',
            'Filter.1.Value.1': 'available',
            'Filter.1.Value.2': 'pending'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(len(api_response), 1)
        self.assertIsInstance(api_response[0], InternetGateway)
        self.assertEqual(api_response[0].id, 'igw-eaad4883EXAMPLE')


class TestCreateInternetGateway(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateInternetGatewayResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <internetGateway>
                  <internetGatewayId>igw-eaad4883</internetGatewayId>
                  <attachmentSet/>
                  <tagSet/>
               </internetGateway>
            </CreateInternetGatewayResponse>
        """

    def test_create_internet_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_internet_gateway()
        self.assert_request_parameters({
            'Action': 'CreateInternetGateway'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertIsInstance(api_response, InternetGateway)
        self.assertEqual(api_response.id, 'igw-eaad4883')


class TestDeleteInternetGateway(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteInternetGatewayResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </DeleteInternetGatewayResponse>
        """

    def test_delete_internet_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_internet_gateway('igw-eaad4883')
        self.assert_request_parameters({
            'Action': 'DeleteInternetGateway',
            'InternetGatewayId': 'igw-eaad4883'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


class TestAttachInternetGateway(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <AttachInternetGatewayResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </AttachInternetGatewayResponse>
        """

    def test_attach_internet_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.attach_internet_gateway(
            'igw-eaad4883', 'vpc-11ad4878')
        self.assert_request_parameters({
            'Action': 'AttachInternetGateway',
            'InternetGatewayId': 'igw-eaad4883',
            'VpcId': 'vpc-11ad4878'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)


class TestDetachInternetGateway(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DetachInternetGatewayResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </DetachInternetGatewayResponse>
        """

    def test_detach_internet_gateway(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.detach_internet_gateway(
            'igw-eaad4883', 'vpc-11ad4878')
        self.assert_request_parameters({
            'Action': 'DetachInternetGateway',
            'InternetGatewayId': 'igw-eaad4883',
            'VpcId': 'vpc-11ad4878'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEquals(api_response, True)

if __name__ == '__main__':
    unittest.main()
