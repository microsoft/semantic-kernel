#!/usr/bin/env python
# Copyright (c) 2015 Shaun Brady.  All Rights Reserved
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


from boto.compat import json
from boto.iam.connection import IAMConnection
from tests.unit import AWSMockServiceTestCase


class TestCreatePolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<CreatePolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <CreatePolicyResult>
    <Policy>
      <PolicyName>S3-read-only-example-bucket</PolicyName>
      <DefaultVersionId>v1</DefaultVersionId>
      <PolicyId>AGPACKCEVSQ6C2EXAMPLE</PolicyId>
      <Path>/</Path>
      <Arn>arn:aws:iam::123456789012:policy/S3-read-only-example-bucket</Arn>
      <AttachmentCount>0</AttachmentCount>
      <CreateDate>2014-09-15T17:36:14.673Z</CreateDate>
      <UpdateDate>2014-09-15T17:36:14.673Z</UpdateDate>
    </Policy>
  </CreatePolicyResult>
  <ResponseMetadata>
    <RequestId>ca64c9e1-3cfe-11e4-bfad-8d1c6EXAMPLE</RequestId>
  </ResponseMetadata>
</CreatePolicyResponse>
        """

    def test_create_policy(self):
        self.set_http_response(status_code=200)
        policy_doc = """
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1430948004000",
            "Effect": "Deny",
            "Action": [
                "s3:*"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
        """
        response = self.service_connection.create_policy(
                'S3-read-only-example-bucket',
                policy_doc)

        self.assert_request_parameters(
            {'Action': 'CreatePolicy',
             'PolicyDocument': policy_doc,
             'Path': '/',
             'PolicyName': 'S3-read-only-example-bucket'},
            ignore_params_values=['Version'])

        self.assertEqual(response['create_policy_response']
                                 ['create_policy_result']
                                 ['policy']
                                 ['policy_name'],
                         'S3-read-only-example-bucket')


class TestCreatePolicyVersion(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<CreatePolicyVersionResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <CreatePolicyVersionResult>
    <PolicyVersion>
      <IsDefaultVersion>true</IsDefaultVersion>
      <VersionId>v2</VersionId>
      <CreateDate>2014-09-15T19:58:59.430Z</CreateDate>
    </PolicyVersion>
  </CreatePolicyVersionResult>
  <ResponseMetadata>
    <RequestId>bb551b92-3d12-11e4-bfad-8d1c6EXAMPLE</RequestId>
  </ResponseMetadata>
</CreatePolicyVersionResponse>
        """

    def test_create_policy_version(self):
        self.set_http_response(status_code=200)
        policy_doc = """
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1430948004000",
            "Effect": "Deny",
            "Action": [
                "s3:*"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
        """
        response = self.service_connection.create_policy_version(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
                policy_doc,
                set_as_default=True)

        self.assert_request_parameters(
            {'Action': 'CreatePolicyVersion',
             'PolicyDocument': policy_doc,
             'SetAsDefault': 'true',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket'},
            ignore_params_values=['Version'])

        self.assertEqual(response['create_policy_version_response']
                                 ['create_policy_version_result']
                                 ['policy_version']
                                 ['is_default_version'],
                         'true')


class TestDeletePolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<DeletePolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ResponseMetadata>
    <RequestId>4706281b-3d19-11e4-a4a0-cffb9EXAMPLE</RequestId>
  </ResponseMetadata>
</DeletePolicyResponse>
        """

    def test_delete_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.delete_policy(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket')

        self.assert_request_parameters(
            {'Action': 'DeletePolicy',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket'},
            ignore_params_values=['Version'])

        self.assertEqual('request_id' in response['delete_policy_response']
                                                 ['response_metadata'],
                         True)


class TestDeletePolicyVersion(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<DeletePolicyVersionResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ResponseMetadata>
    <RequestId>268e1556-3d19-11e4-a4a0-cffb9EXAMPLE</RequestId>
  </ResponseMetadata>
</DeletePolicyVersionResponse>
        """

    def test_delete_policy_version(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.delete_policy_version(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
                'v1')

        self.assert_request_parameters(
            {'Action': 'DeletePolicyVersion',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
             'VersionId': 'v1'},
            ignore_params_values=['Version'])

        self.assertEqual('request_id' in response['delete_policy_version_response']
                                                 ['response_metadata'],
                         True)


class TestGetPolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<GetPolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <GetPolicyResult>
    <Policy>
      <PolicyName>S3-read-only-example-bucket</PolicyName>
      <DefaultVersionId>v1</DefaultVersionId>
      <PolicyId>AGPACKCEVSQ6C2EXAMPLE</PolicyId>
      <Path>/</Path>
      <Arn>arn:aws:iam::123456789012:policy/S3-read-only-example-bucket</Arn>
      <AttachmentCount>9</AttachmentCount>
      <CreateDate>2014-09-15T17:36:14Z</CreateDate>
      <UpdateDate>2014-09-15T20:31:47Z</UpdateDate>
      <Description>My Awesome Policy</Description>
    </Policy>
  </GetPolicyResult>
  <ResponseMetadata>
    <RequestId>684f0917-3d22-11e4-a4a0-cffb9EXAMPLE</RequestId>
  </ResponseMetadata>
</GetPolicyResponse>
        """

    def test_get_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_policy(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket')

        self.assert_request_parameters(
            {'Action': 'GetPolicy',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket'},
            ignore_params_values=['Version'])

        self.assertEqual(response['get_policy_response']
                                 ['get_policy_result']
                                 ['policy']
                                 ['arn'],
                         'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket')

        self.assertEqual(response['get_policy_response']
                                 ['get_policy_result']
                                 ['policy']
                                 ['description'],
                         'My Awesome Policy')


class TestGetPolicyVersion(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<GetPolicyVersionResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <GetPolicyVersionResult>
    <PolicyVersion>
      <Document>
      {"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:Get*","s3:List*"],
      "Resource":["arn:aws:s3:::EXAMPLE-BUCKET","arn:aws:s3:::EXAMPLE-BUCKET/*"]}]}
      </Document>
      <IsDefaultVersion>true</IsDefaultVersion>
      <VersionId>v1</VersionId>
      <CreateDate>2014-09-15T20:31:47Z</CreateDate>
    </PolicyVersion>
  </GetPolicyVersionResult>
  <ResponseMetadata>
    <RequestId>d472f28e-3d23-11e4-a4a0-cffb9EXAMPLE</RequestId>
  </ResponseMetadata>
</GetPolicyVersionResponse>
        """

    def test_get_policy_version(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_policy_version(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
                'v1')

        self.assert_request_parameters(
            {'Action': 'GetPolicyVersion',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
             'VersionId': 'v1'},
            ignore_params_values=['Version'])

        self.assertEqual(response['get_policy_version_response']
                                 ['get_policy_version_result']
                                 ['policy_version']
                                 ['version_id'],
                         'v1')


class TestListPolicies(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<ListPoliciesResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ListPoliciesResult>
    <IsTruncated>true</IsTruncated>
    <Marker>EXAMPLEkakv9BCuUNFDtxWSyfzetYwEx2ADc8dnzfvERF5S6YMvXKx41t6gCl/eeaCX3Jo94/bKqezEAg8TEVS99EKFLxm3jtbpl25FDWEXAMPLE
    </Marker>
    <Policies>
      <member>
        <PolicyName>ExamplePolicy</PolicyName>
        <DefaultVersionId>v1</DefaultVersionId>
        <PolicyId>AGPACKCEVSQ6C2EXAMPLE</PolicyId>
        <Path>/</Path>
        <Arn>arn:aws:iam::123456789012:policy/ExamplePolicy</Arn>
        <AttachmentCount>2</AttachmentCount>
        <CreateDate>2014-09-15T17:36:14Z</CreateDate>
        <UpdateDate>2014-09-15T20:31:47Z</UpdateDate>
      </member>
      <member>
        <PolicyName>PowerUserAccess</PolicyName>
        <DefaultVersionId>v1</DefaultVersionId>
        <PolicyId>AGPACKCEVSQ6C2EXAMPLE</PolicyId>
        <Path>/</Path>
        <Arn>arn:aws:iam::aws:policy/PowerUserAccess</Arn>
        <AttachmentCount>0</AttachmentCount>
        <CreateDate>2014-08-21T20:25:01Z</CreateDate>
        <UpdateDate>2014-08-21T20:25:01Z</UpdateDate>
      </member>
      <member>
        <PolicyName>AdministratorAccess</PolicyName>
        <DefaultVersionId>v1</DefaultVersionId>
        <PolicyId>AGPACKCEVSQ6C2EXAMPLE</PolicyId>
        <Path>/</Path>
        <Arn>arn:aws:iam::aws:policy/AdministratorAccess</Arn>
        <AttachmentCount>1</AttachmentCount>
        <CreateDate>2014-08-21T20:11:25Z</CreateDate>
        <UpdateDate>2014-08-21T20:11:25Z</UpdateDate>
      </member>
      <member>
        <PolicyName>ReadOnlyAccess</PolicyName>
        <DefaultVersionId>v1</DefaultVersionId>
        <PolicyId>AGPACKCEVSQ6C2EXAMPLE</PolicyId>
        <Path>/</Path>
        <Arn>arn:aws:iam::aws:policy/ReadOnlyAccess</Arn>
        <AttachmentCount>6</AttachmentCount>
        <CreateDate>2014-08-21T20:31:44Z</CreateDate>
        <UpdateDate>2014-08-21T20:31:44Z</UpdateDate>
      </member>
    </Policies>
  </ListPoliciesResult>
  <ResponseMetadata>
    <RequestId>6207e832-3eb7-11e4-9d0d-6f969EXAMPLE</RequestId>
  </ResponseMetadata>
</ListPoliciesResponse>
        """

    def test_list_policies(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.list_policies(
            max_items=4)
        self.assert_request_parameters(
            {'Action': 'ListPolicies',
             'MaxItems': 4},
            ignore_params_values=['Version'])

        self.assertEqual(len(response['list_policies_response']
                                     ['list_policies_result']
                                     ['policies']),
                         4)

        self.assertEqual(response['list_policies_response']
                                 ['list_policies_result']
                                 ['is_truncated'],
                         'true')


class TestListPolicyVersions(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<ListPolicyVersionsResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ListPolicyVersionsResult>
    <Versions>
      <member>
        <IsDefaultVersion>false</IsDefaultVersion>
        <VersionId>v3</VersionId>
        <CreateDate>2014-09-17T22:32:43Z</CreateDate>
      </member>
      <member>
        <IsDefaultVersion>true</IsDefaultVersion>
        <VersionId>v2</VersionId>
        <CreateDate>2014-09-15T20:31:47Z</CreateDate>
      </member>
      <member>
        <IsDefaultVersion>false</IsDefaultVersion>
        <VersionId>v1</VersionId>
        <CreateDate>2014-09-15T17:36:14Z</CreateDate>
      </member>
    </Versions>
    <IsTruncated>false</IsTruncated>
  </ListPolicyVersionsResult>
  <ResponseMetadata>
    <RequestId>a31d1a86-3eba-11e4-9d0d-6f969EXAMPLE</RequestId>
  </ResponseMetadata>
</ListPolicyVersionsResponse>
        """

    def test_list_policy_versions(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.list_policy_versions(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
                max_items=3)

        self.assert_request_parameters(
            {'Action': 'ListPolicyVersions',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
             'MaxItems': 3},
            ignore_params_values=['Version'])

        self.assertEqual(len(response['list_policy_versions_response']
                                     ['list_policy_versions_result']
                                     ['versions']),
                         3)


class TestSetDefaultPolicyVersion(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<SetDefaultPolicyVersionResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ResponseMetadata>
    <RequestId>35f241af-3ebc-11e4-9d0d-6f969EXAMPLE</RequestId>
  </ResponseMetadata>
</SetDefaultPolicyVersionResponse>
        """

    def test_set_default_policy_version(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.set_default_policy_version(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
                'v1')

        self.assert_request_parameters(
            {'Action': 'SetDefaultPolicyVersion',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
             'VersionId': 'v1'},
            ignore_params_values=['Version'])

        self.assertEqual('request_id' in response['set_default_policy_version_response']
                                                 ['response_metadata'],
                         True)


class TestListEntitiesForPolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<ListEntitiesForPolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ListEntitiesForPolicyResult>
    <PolicyRoles>
      <member>
        <RoleName>DevRole</RoleName>
      </member>
    </PolicyRoles>
    <PolicyGroups>
      <member>
        <GroupName>Dev</GroupName>
      </member>
    </PolicyGroups>
    <IsTruncated>false</IsTruncated>
    <PolicyUsers>
      <member>
        <UserName>Alice</UserName>
      </member>
      <member>
        <UserName>Bob</UserName>
      </member>
    </PolicyUsers>
  </ListEntitiesForPolicyResult>
  <ResponseMetadata>
    <RequestId>eb358e22-9d1f-11e4-93eb-190ecEXAMPLE</RequestId>
  </ResponseMetadata>
</ListEntitiesForPolicyResponse>
        """

    def test_list_entities_for_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.list_entities_for_policy(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket')

        self.assert_request_parameters(
            {'Action': 'ListEntitiesForPolicy',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket'},
            ignore_params_values=['Version'])

        self.assertEqual(len(response['list_entities_for_policy_response']
                                     ['list_entities_for_policy_result']
                                     ['policy_roles']),
                         1)

        self.assertEqual(len(response['list_entities_for_policy_response']
                                     ['list_entities_for_policy_result']
                                     ['policy_groups']),
                         1)

        self.assertEqual(len(response['list_entities_for_policy_response']
                                     ['list_entities_for_policy_result']
                                     ['policy_users']),
                         2)

        self.assertEqual({'user_name': 'Alice'} in response['list_entities_for_policy_response']
                                                           ['list_entities_for_policy_result']
                                                           ['policy_users'],
                         True)


class TestAttachGroupPolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<AttachGroupPolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ResponseMetadata>
    <RequestId>f8a7b7b9-3d01-11e4-bfad-8d1c6EXAMPLE</RequestId>
  </ResponseMetadata>
</AttachGroupPolicyResponse>
        """

    def test_attach_group_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.attach_group_policy(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
                'Dev')

        self.assert_request_parameters(
            {'Action': 'AttachGroupPolicy',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
             'GroupName': 'Dev'},
            ignore_params_values=['Version'])

        self.assertEqual('request_id' in response['attach_group_policy_response']
                                                 ['response_metadata'],
                         True)


class TestAttachRolePolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<AttachRolePolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ResponseMetadata>
    <RequestId>37a87673-3d07-11e4-bfad-8d1c6EXAMPLE</RequestId>
  </ResponseMetadata>
</AttachRolePolicyResponse>
        """

    def test_attach_role_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.attach_role_policy(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
                'DevRole')

        self.assert_request_parameters(
            {'Action': 'AttachRolePolicy',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
             'RoleName': 'DevRole'},
            ignore_params_values=['Version'])

        self.assertEqual('request_id' in response['attach_role_policy_response']
                                                 ['response_metadata'],
                         True)


class TestAttachUserPolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<AttachUserPolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ResponseMetadata>
    <RequestId>ed7e72d3-3d07-11e4-bfad-8d1c6EXAMPLE</RequestId>
  </ResponseMetadata>
</AttachUserPolicyResponse>
        """

    def test_attach_user_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.attach_user_policy(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
                'Alice')

        self.assert_request_parameters(
            {'Action': 'AttachUserPolicy',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
             'UserName': 'Alice'},
            ignore_params_values=['Version'])

        self.assertEqual('request_id' in response['attach_user_policy_response']
                                                 ['response_metadata'],
                         True)


class TestDetachGroupPolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<DetachGroupPolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ResponseMetadata>
    <RequestId>d4faa7aa-3d1d-11e4-a4a0-cffb9EXAMPLE</RequestId>
  </ResponseMetadata>
</DetachGroupPolicyResponse>
        """

    def test_detach_group_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.detach_group_policy(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
                'Dev')

        self.assert_request_parameters(
            {'Action': 'DetachGroupPolicy',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
             'GroupName': 'Dev'},
            ignore_params_values=['Version'])

        self.assertEqual('request_id' in response['detach_group_policy_response']
                                                 ['response_metadata'],
                         True)


class TestDetachRolePolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<DetachRolePolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ResponseMetadata>
    <RequestId>4c80ccf4-3d1e-11e4-a4a0-cffb9EXAMPLE</RequestId>
  </ResponseMetadata>
</DetachRolePolicyResponse>
        """

    def test_detach_role_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.detach_role_policy(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
                'DevRole')

        self.assert_request_parameters(
            {'Action': 'DetachRolePolicy',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
             'RoleName': 'DevRole'},
            ignore_params_values=['Version'])

        self.assertEqual('request_id' in response['detach_role_policy_response']
                                                 ['response_metadata'],
                         True)


class TestDetachUserPolicy(AWSMockServiceTestCase):
    connection_class = IAMConnection

    def default_body(self):
        return b"""
<DetachUserPolicyResponse xmlns="https://iam.amazonaws.com/doc/2010-05-08/">
  <ResponseMetadata>
    <RequestId>85ba31fa-3d1f-11e4-a4a0-cffb9EXAMPLE</RequestId>
  </ResponseMetadata>
</DetachUserPolicyResponse>
        """

    def test_detach_user_policy(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.detach_user_policy(
                'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
                'Alice')

        self.assert_request_parameters(
            {'Action': 'DetachUserPolicy',
             'PolicyArn': 'arn:aws:iam::123456789012:policy/S3-read-only-example-bucket',
             'UserName': 'Alice'},
            ignore_params_values=['Version'])

        self.assertEqual('request_id' in response['detach_user_policy_response']
                                                 ['response_metadata'],
                         True)
