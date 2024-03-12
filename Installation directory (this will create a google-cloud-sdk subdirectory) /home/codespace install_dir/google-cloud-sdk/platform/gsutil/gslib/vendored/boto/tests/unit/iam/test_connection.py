#!/usr/bin/env python
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

from base64 import b64decode
from boto.compat import json
from boto.iam.connection import IAMConnection
from tests.unit import AWSMockServiceTestCase


class TestCreateSamlProvider(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
            <CreateSAMLProviderResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
              <CreateSAMLProviderResult>
                <SAMLProviderArn>arn</SAMLProviderArn>
              </CreateSAMLProviderResult>
              <ResponseMetadata>
                <RequestId>29f47818-99f5-11e1-a4c3-27EXAMPLE804</RequestId>
              </ResponseMetadata>
            </CreateSAMLProviderResponse>
        """

    def test_create_saml_provider(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.create_saml_provider('document', 'name')

        self.assert_request_parameters(
            {'Action': 'CreateSAMLProvider',
             'SAMLMetadataDocument': 'document',
             'Name': 'name'},
            ignore_params_values=['Version'])

        self.assertEqual(response['create_saml_provider_response']
                                 ['create_saml_provider_result']
                                 ['saml_provider_arn'], 'arn')


class TestListSamlProviders(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
            <ListSAMLProvidersResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
              <ListSAMLProvidersResult>
                <SAMLProviderList>
                  <member>
                    <Arn>arn:aws:iam::123456789012:instance-profile/application_abc/component_xyz/Database</Arn>
                    <ValidUntil>2032-05-09T16:27:11Z</ValidUntil>
                    <CreateDate>2012-05-09T16:27:03Z</CreateDate>
                  </member>
                  <member>
                    <Arn>arn:aws:iam::123456789012:instance-profile/application_abc/component_xyz/Webserver</Arn>
                    <ValidUntil>2015-03-11T13:11:02Z</ValidUntil>
                    <CreateDate>2012-05-09T16:27:11Z</CreateDate>
                  </member>
                </SAMLProviderList>
              </ListSAMLProvidersResult>
              <ResponseMetadata>
                <RequestId>fd74fa8d-99f3-11e1-a4c3-27EXAMPLE804</RequestId>
              </ResponseMetadata>
            </ListSAMLProvidersResponse>
        """

    def test_list_saml_providers(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.list_saml_providers()

        self.assert_request_parameters(
            {'Action': 'ListSAMLProviders'},
            ignore_params_values=['Version'])
        self.assertEqual(response.saml_provider_list, [
            {'arn': 'arn:aws:iam::123456789012:instance-profile/application_abc/component_xyz/Database',
             'valid_until': '2032-05-09T16:27:11Z',
             'create_date': '2012-05-09T16:27:03Z'},
            {'arn': 'arn:aws:iam::123456789012:instance-profile/application_abc/component_xyz/Webserver',
             'valid_until': '2015-03-11T13:11:02Z',
             'create_date': '2012-05-09T16:27:11Z'}])


class TestGetSamlProvider(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
            <GetSAMLProviderResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
              <GetSAMLProviderResult>
                <CreateDate>2012-05-09T16:27:11Z</CreateDate>
                <ValidUntil>2015-12-31T211:59:59Z</ValidUntil>
                <SAMLMetadataDocument>Pd9fexDssTkRgGNqs...DxptfEs==</SAMLMetadataDocument>
              </GetSAMLProviderResult>
              <ResponseMetadata>
                <RequestId>29f47818-99f5-11e1-a4c3-27EXAMPLE804</RequestId>
              </ResponseMetadata>
            </GetSAMLProviderResponse>
        """

    def test_get_saml_provider(self):
        self.set_http_response(status_code=200)
        self.service_connection.get_saml_provider('arn')

        self.assert_request_parameters(
            {
                'Action': 'GetSAMLProvider',
                'SAMLProviderArn': 'arn'
            },
            ignore_params_values=['Version'])


class TestUpdateSamlProvider(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
            <UpdateSAMLProviderResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
              <UpdateSAMLProviderResult>
                <SAMLProviderArn>arn:aws:iam::123456789012:saml-metadata/MyUniversity</SAMLProviderArn>
              </UpdateSAMLProviderResult>
              <ResponseMetadata>
                <RequestId>29f47818-99f5-11e1-a4c3-27EXAMPLE804</RequestId>
              </ResponseMetadata>
            </UpdateSAMLProviderResponse>
        """

    def test_update_saml_provider(self):
        self.set_http_response(status_code=200)
        self.service_connection.update_saml_provider('arn', 'doc')

        self.assert_request_parameters(
            {
                'Action': 'UpdateSAMLProvider',
                'SAMLMetadataDocument': 'doc',
                'SAMLProviderArn': 'arn'
            },
            ignore_params_values=['Version'])


class TestDeleteSamlProvider(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return ""

    def test_delete_saml_provider(self):
        self.set_http_response(status_code=200)
        self.service_connection.delete_saml_provider('arn')

        self.assert_request_parameters(
            {
                'Action': 'DeleteSAMLProvider',
                'SAMLProviderArn': 'arn'
            },
            ignore_params_values=['Version'])


class TestCreateRole(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
          <CreateRoleResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
            <CreateRoleResult>
              <Role>
                <Path>/application_abc/component_xyz/</Path>
                <Arn>arn:aws:iam::123456789012:role/application_abc/component_xyz/S3Access</Arn>
                <RoleName>S3Access</RoleName>
                <AssumeRolePolicyDocument>{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":["ec2.amazonaws.com"]},"Action":["sts:AssumeRole"]}]}</AssumeRolePolicyDocument>
                <CreateDate>2012-05-08T23:34:01.495Z</CreateDate>
                <RoleId>AROADBQP57FF2AEXAMPLE</RoleId>
              </Role>
            </CreateRoleResult>
            <ResponseMetadata>
              <RequestId>4a93ceee-9966-11e1-b624-b1aEXAMPLE7c</RequestId>
            </ResponseMetadata>
          </CreateRoleResponse>
        """

    def test_create_role_default(self):
        self.set_http_response(status_code=200)
        self.service_connection.create_role('a_name')

        self.assert_request_parameters(
            {'Action': 'CreateRole',
             'RoleName': 'a_name'},
            ignore_params_values=['Version', 'AssumeRolePolicyDocument'])
        self.assertDictEqual(json.loads(self.actual_request.params["AssumeRolePolicyDocument"]), {"Statement": [{"Action": ["sts:AssumeRole"], "Effect": "Allow", "Principal": {"Service": ["ec2.amazonaws.com"]}}]})

    def test_create_role_default_cn_north(self):
        self.set_http_response(status_code=200)
        self.service_connection.host = 'iam.cn-north-1.amazonaws.com.cn'
        self.service_connection.create_role('a_name')

        self.assert_request_parameters(
            {'Action': 'CreateRole',
             'RoleName': 'a_name'},
            ignore_params_values=['Version', 'AssumeRolePolicyDocument'])
        self.assertDictEqual(json.loads(self.actual_request.params["AssumeRolePolicyDocument"]), {"Statement": [{"Action": ["sts:AssumeRole"], "Effect": "Allow", "Principal": {"Service": ["ec2.amazonaws.com.cn"]}}]})

    def test_create_role_string_policy(self):
        self.set_http_response(status_code=200)
        self.service_connection.create_role(
            'a_name',
            # Historical usage.
            assume_role_policy_document='{"hello": "policy"}'
        )

        self.assert_request_parameters(
            {'Action': 'CreateRole',
             'AssumeRolePolicyDocument': '{"hello": "policy"}',
             'RoleName': 'a_name'},
            ignore_params_values=['Version'])

    def test_create_role_data_policy(self):
        self.set_http_response(status_code=200)
        self.service_connection.create_role(
            'a_name',
            # With plain data, we should dump it for them.
            assume_role_policy_document={"hello": "policy"}
        )

        self.assert_request_parameters(
            {'Action': 'CreateRole',
             'AssumeRolePolicyDocument': '{"hello": "policy"}',
             'RoleName': 'a_name'},
            ignore_params_values=['Version'])


class TestGetSigninURL(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
          <ListAccountAliasesResponse>
            <ListAccountAliasesResult>
              <IsTruncated>false</IsTruncated>
              <AccountAliases>
                <member>foocorporation</member>
                <member>anotherunused</member>
              </AccountAliases>
            </ListAccountAliasesResult>
            <ResponseMetadata>
              <RequestId>c5a076e9-f1b0-11df-8fbe-45274EXAMPLE</RequestId>
            </ResponseMetadata>
          </ListAccountAliasesResponse>
        """

    def test_get_signin_url_default(self):
        self.set_http_response(status_code=200)
        url = self.service_connection.get_signin_url()
        self.assertEqual(
            url,
            'https://foocorporation.signin.aws.amazon.com/console/ec2'
        )

    def test_get_signin_url_s3(self):
        self.set_http_response(status_code=200)
        url = self.service_connection.get_signin_url(service='s3')
        self.assertEqual(
            url,
            'https://foocorporation.signin.aws.amazon.com/console/s3'
        )

    def test_get_signin_url_cn_north(self):
        self.set_http_response(status_code=200)
        self.service_connection.host = 'iam.cn-north-1.amazonaws.com.cn'
        url = self.service_connection.get_signin_url()
        self.assertEqual(
            url,
            'https://foocorporation.signin.amazonaws.cn/console/ec2'
        )


class TestGetSigninURLNoAliases(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
          <ListAccountAliasesResponse>
            <ListAccountAliasesResult>
              <IsTruncated>false</IsTruncated>
              <AccountAliases></AccountAliases>
            </ListAccountAliasesResult>
            <ResponseMetadata>
              <RequestId>c5a076e9-f1b0-11df-8fbe-45274EXAMPLE</RequestId>
            </ResponseMetadata>
          </ListAccountAliasesResponse>
        """

    def test_get_signin_url_no_aliases(self):
        self.set_http_response(status_code=200)

        with self.assertRaises(Exception):
            self.service_connection.get_signin_url()


class TestGenerateCredentialReport(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
          <GenerateCredentialReportResponse>
            <GenerateCredentialReportResult>
              <State>COMPLETE</State>
            </GenerateCredentialReportResult>
            <ResponseMetadata>
              <RequestId>b62e22a3-0da1-11e4-ba55-0990EXAMPLE</RequestId>
            </ResponseMetadata>
          </GenerateCredentialReportResponse>
        """

    def test_generate_credential_report(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.generate_credential_report()
        self.assertEquals(response['generate_credential_report_response']
                                  ['generate_credential_report_result']
                                  ['state'], 'COMPLETE')


class TestGetCredentialReport(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
          <GetCredentialReportResponse>
            <ResponseMetadata>
              <RequestId>99e60e9a-0db5-11e4-94d4-b764EXAMPLE</RequestId>
            </ResponseMetadata>
            <GetCredentialReportResult>
              <Content>RXhhbXBsZQ==</Content>
              <ReportFormat>text/csv</ReportFormat>
              <GeneratedTime>2014-07-17T11:09:11Z</GeneratedTime>
            </GetCredentialReportResult>
          </GetCredentialReportResponse>
        """

    def test_get_credential_report(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_credential_report()
        b64decode(response['get_credential_report_response']
                          ['get_credential_report_result']
                          ['content'])

class TestCreateVirtualMFADevice(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
            <CreateVirtualMFADeviceResponse>
              <CreateVirtualMFADeviceResult>
                <VirtualMFADevice>
                  <SerialNumber>arn:aws:iam::123456789012:mfa/ExampleName</SerialNumber>
                  <Base32StringSeed>2K5K5XTLA7GGE75TQLYEXAMPLEEXAMPLEEXAMPLECHDFW4KJYZ6
                  UFQ75LL7COCYKM</Base32StringSeed>
                  <QRCodePNG>89504E470D0A1A0AASDFAHSDFKJKLJFKALSDFJASDF</QRCodePNG>
                </VirtualMFADevice>
              </CreateVirtualMFADeviceResult>
              <ResponseMetadata>
                <RequestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</RequestId>
              </ResponseMetadata>
            </CreateVirtualMFADeviceResponse>
        """

    def test_create_virtual_mfa_device(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.create_virtual_mfa_device('/', 'ExampleName')
        self.assert_request_parameters(
            {'Path': '/',
             'VirtualMFADeviceName': 'ExampleName',
             'Action': 'CreateVirtualMFADevice'},
            ignore_params_values=['Version'])
        self.assertEquals(response['create_virtual_mfa_device_response']
                                  ['create_virtual_mfa_device_result']
                                  ['virtual_mfa_device']
                                  ['serial_number'], 'arn:aws:iam::123456789012:mfa/ExampleName')

class TestGetAccountPasswordPolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
            <GetAccountPasswordPolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
              <GetAccountPasswordPolicyResult>
                <PasswordPolicy>
                  <AllowUsersToChangePassword>true</AllowUsersToChangePassword>
                  <RequireUppercaseCharacters>true</RequireUppercaseCharacters>
                  <RequireSymbols>true</RequireSymbols>
                  <ExpirePasswords>false</ExpirePasswords>
                  <PasswordReusePrevention>12</PasswordReusePrevention>
                  <RequireLowercaseCharacters>true</RequireLowercaseCharacters>
                  <MaxPasswordAge>90</MaxPasswordAge>
                  <HardExpiry>false</HardExpiry>
                  <RequireNumbers>true</RequireNumbers>
                  <MinimumPasswordLength>12</MinimumPasswordLength>
                </PasswordPolicy>
              </GetAccountPasswordPolicyResult>
              <ResponseMetadata>
                <RequestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</RequestId>
              </ResponseMetadata>
            </GetAccountPasswordPolicyResponse>
        """

    def test_get_account_password_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_account_password_policy()

        self.assert_request_parameters(
            {
                'Action': 'GetAccountPasswordPolicy',
            },
            ignore_params_values=['Version'])
        self.assertEquals(response['get_account_password_policy_response']
                          ['get_account_password_policy_result']['password_policy']
                          ['minimum_password_length'], '12')


class TestUpdateAccountPasswordPolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
            <UpdateAccountPasswordPolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
               <ResponseMetadata>
                  <RequestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</RequestId>
               </ResponseMetadata>
            </UpdateAccountPasswordPolicyResponse>
        """

    def test_update_account_password_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.update_account_password_policy(minimum_password_length=88)

        self.assert_request_parameters(
            {
                'Action': 'UpdateAccountPasswordPolicy',
                'MinimumPasswordLength': 88
            },
            ignore_params_values=['Version'])


class TestDeleteAccountPasswordPolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
            <DeleteAccountPasswordPolicyResponse>
              <ResponseMetadata>
                <RequestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</RequestId>
              </ResponseMetadata>
            </DeleteAccountPasswordPolicyResponse>
        """

    def test_delete_account_password_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.delete_account_password_policy()

        self.assert_request_parameters(
            {
                'Action': 'DeleteAccountPasswordPolicy'
            },
            ignore_params_values=['Version'])
