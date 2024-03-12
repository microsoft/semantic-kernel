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

from tests.unit import unittest
from boto.sts.connection import STSConnection
from tests.unit import AWSMockServiceTestCase


class TestSecurityToken(AWSMockServiceTestCase):
    connection_class = STSConnection

    def create_service_connection(self, **kwargs):
        kwargs['security_token'] = 'token'

        return super(TestSecurityToken, self).create_service_connection(**kwargs)

    def test_security_token(self):
        self.assertEqual('token',
                         self.service_connection.provider.security_token)

class TestSTSConnection(AWSMockServiceTestCase):
    connection_class = STSConnection

    def setUp(self):
        super(TestSTSConnection, self).setUp()

    def default_body(self):
        return b"""
            <AssumeRoleResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
              <AssumeRoleResult>
                <AssumedRoleUser>
                  <Arn>arn:role</Arn>
                  <AssumedRoleId>roleid:myrolesession</AssumedRoleId>
                </AssumedRoleUser>
                <Credentials>
                  <SessionToken>session_token</SessionToken>
                  <SecretAccessKey>secretkey</SecretAccessKey>
                  <Expiration>2012-10-18T10:18:14.789Z</Expiration>
                  <AccessKeyId>accesskey</AccessKeyId>
                </Credentials>
              </AssumeRoleResult>
              <ResponseMetadata>
                <RequestId>8b7418cb-18a8-11e2-a706-4bd22ca68ab7</RequestId>
              </ResponseMetadata>
            </AssumeRoleResponse>
        """

    def test_assume_role(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.assume_role('arn:role', 'mysession')
        self.assert_request_parameters(
            {'Action': 'AssumeRole',
             'RoleArn': 'arn:role',
             'RoleSessionName': 'mysession'},
            ignore_params_values=['Version'])
        self.assertEqual(response.credentials.access_key, 'accesskey')
        self.assertEqual(response.credentials.secret_key, 'secretkey')
        self.assertEqual(response.credentials.session_token, 'session_token')
        self.assertEqual(response.user.arn, 'arn:role')
        self.assertEqual(response.user.assume_role_id, 'roleid:myrolesession')

    def test_assume_role_with_mfa(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.assume_role(
            'arn:role',
            'mysession',
            mfa_serial_number='GAHT12345678',
            mfa_token='abc123'
        )
        self.assert_request_parameters(
            {'Action': 'AssumeRole',
             'RoleArn': 'arn:role',
             'RoleSessionName': 'mysession',
             'SerialNumber': 'GAHT12345678',
             'TokenCode': 'abc123'},
            ignore_params_values=['Version'])
        self.assertEqual(response.credentials.access_key, 'accesskey')
        self.assertEqual(response.credentials.secret_key, 'secretkey')
        self.assertEqual(response.credentials.session_token, 'session_token')
        self.assertEqual(response.user.arn, 'arn:role')
        self.assertEqual(response.user.assume_role_id, 'roleid:myrolesession')


class TestSTSWebIdentityConnection(AWSMockServiceTestCase):
    connection_class = STSConnection

    def setUp(self):
        super(TestSTSWebIdentityConnection, self).setUp()

    def default_body(self):
        return b"""
<AssumeRoleWithWebIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
  <AssumeRoleWithWebIdentityResult>
    <SubjectFromWebIdentityToken>
      amzn1.account.AF6RHO7KZU5XRVQJGXK6HB56KR2A
    </SubjectFromWebIdentityToken>
    <AssumedRoleUser>
      <Arn>
        arn:aws:sts::000240903217:assumed-role/FederatedWebIdentityRole/app1
      </Arn>
      <AssumedRoleId>
        AROACLKWSDQRAOFQC3IDI:app1
      </AssumedRoleId>
    </AssumedRoleUser>
    <Credentials>
      <SessionToken>
        AQoDYXdzEE0a8ANXXXXXXXXNO1ewxE5TijQyp+IPfnyowF
      </SessionToken>
      <SecretAccessKey>
        secretkey
      </SecretAccessKey>
      <Expiration>
        2013-05-14T23:00:23Z
      </Expiration>
      <AccessKeyId>
        accesskey
      </AccessKeyId>
    </Credentials>
  </AssumeRoleWithWebIdentityResult>
  <ResponseMetadata>
    <RequestId>ad4156e9-bce1-11e2-82e6-6b6ef249e618</RequestId>
  </ResponseMetadata>
</AssumeRoleWithWebIdentityResponse>
        """

    def test_assume_role_with_web_identity(self):
        arn = 'arn:aws:iam::000240903217:role/FederatedWebIdentityRole'
        wit = 'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'

        self.set_http_response(status_code=200)
        response = self.service_connection.assume_role_with_web_identity(
            role_arn=arn,
            role_session_name='guestuser',
            web_identity_token=wit,
            provider_id='www.amazon.com',
        )
        self.assert_request_parameters({
          'RoleSessionName': 'guestuser',
          'RoleArn': arn,
          'WebIdentityToken': wit,
          'ProviderId': 'www.amazon.com',
          'Action': 'AssumeRoleWithWebIdentity'
        }, ignore_params_values=[
          'Version'
        ])
        self.assertEqual(
          response.credentials.access_key.strip(),
          'accesskey'
        )
        self.assertEqual(
          response.credentials.secret_key.strip(),
          'secretkey'
        )
        self.assertEqual(
          response.credentials.session_token.strip(),
          'AQoDYXdzEE0a8ANXXXXXXXXNO1ewxE5TijQyp+IPfnyowF'
        )
        self.assertEqual(
          response.user.arn.strip(),
          'arn:aws:sts::000240903217:assumed-role/FederatedWebIdentityRole/app1'
        )
        self.assertEqual(
          response.user.assume_role_id.strip(),
          'AROACLKWSDQRAOFQC3IDI:app1'
        )


class TestSTSSAMLConnection(AWSMockServiceTestCase):
    connection_class = STSConnection

    def setUp(self):
        super(TestSTSSAMLConnection, self).setUp()

    def default_body(self):
        return b"""
<AssumeRoleWithSAMLResponse xmlns="https://sts.amazonaws.com/doc/
2011-06-15/">
  <AssumeRoleWithSAMLResult>
    <Credentials>
      <SessionToken>session_token</SessionToken>
      <SecretAccessKey>secretkey</SecretAccessKey>
      <Expiration>2011-07-15T23:28:33.359Z</Expiration>
      <AccessKeyId>accesskey</AccessKeyId>
    </Credentials>
    <AssumedRoleUser>
      <Arn>arn:role</Arn>
      <AssumedRoleId>roleid:myrolesession</AssumedRoleId>
    </AssumedRoleUser>
    <PackedPolicySize>6</PackedPolicySize>
  </AssumeRoleWithSAMLResult>
  <ResponseMetadata>
    <RequestId>c6104cbe-af31-11e0-8154-cbc7ccf896c7</RequestId>
  </ResponseMetadata>
</AssumeRoleWithSAMLResponse>
"""

    def test_assume_role_with_saml(self):
        arn = 'arn:aws:iam::000240903217:role/Test'
        principal = 'arn:aws:iam::000240903217:role/Principal'
        assertion = 'test'

        self.set_http_response(status_code=200)
        response = self.service_connection.assume_role_with_saml(
            role_arn=arn,
            principal_arn=principal,
            saml_assertion=assertion
        )
        self.assert_request_parameters({
          'RoleArn': arn,
          'PrincipalArn': principal,
          'SAMLAssertion': assertion,
          'Action': 'AssumeRoleWithSAML'
        }, ignore_params_values=[
          'Version'
        ])
        self.assertEqual(response.credentials.access_key, 'accesskey')
        self.assertEqual(response.credentials.secret_key, 'secretkey')
        self.assertEqual(response.credentials.session_token, 'session_token')
        self.assertEqual(response.user.arn, 'arn:role')
        self.assertEqual(response.user.assume_role_id, 'roleid:myrolesession')


if __name__ == '__main__':
    unittest.main()
