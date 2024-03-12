# -*- coding: utf-8 -*-
from mock import patch
import xml.dom.minidom

from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.exception import BotoClientError
from boto.s3.connection import Location, S3Connection
from boto.s3.bucket import Bucket
from boto.s3.deletemarker import DeleteMarker
from boto.s3.key import Key
from boto.s3.multipart import MultiPartUpload
from boto.s3.prefix import Prefix


class TestS3Bucket(AWSMockServiceTestCase):
    connection_class = S3Connection

    def setUp(self):
        super(TestS3Bucket, self).setUp()

    def test_bucket_create_bucket(self):
        self.set_http_response(status_code=200)
        bucket = self.service_connection.create_bucket('mybucket_create')
        self.assertEqual(bucket.name, 'mybucket_create')

    def test_bucket_create_eu_central_1_location(self):
        self.set_http_response(status_code=200)
        bucket = self.service_connection.create_bucket(
            'eu_central_1_bucket',
            location=Location.EUCentral1
        )
        self.assertEqual(bucket.name, 'eu_central_1_bucket')

    def test_bucket_constructor(self):
        self.set_http_response(status_code=200)
        bucket = Bucket(self.service_connection, 'mybucket_constructor')
        self.assertEqual(bucket.name, 'mybucket_constructor')

    def test_bucket_basics(self):
        self.set_http_response(status_code=200)
        bucket = self.service_connection.create_bucket('mybucket')
        self.assertEqual(bucket.__repr__(), '<Bucket: mybucket>')

    def test_bucket_new_key(self):
        self.set_http_response(status_code=200)
        bucket = self.service_connection.create_bucket('mybucket')
        key = bucket.new_key('mykey')

        self.assertEqual(key.bucket, bucket)
        self.assertEqual(key.key, 'mykey')

    def test_bucket_new_key_missing_name(self):
        self.set_http_response(status_code=200)
        bucket = self.service_connection.create_bucket('mybucket')

        with self.assertRaises(ValueError):
            key = bucket.new_key('')

    def test_bucket_delete_key_missing_name(self):
        self.set_http_response(status_code=200)
        bucket = self.service_connection.create_bucket('mybucket')

        with self.assertRaises(ValueError):
            key = bucket.delete_key('')

    def test_bucket_kwargs_misspelling(self):
        self.set_http_response(status_code=200)
        bucket = self.service_connection.create_bucket('mybucket')

        with self.assertRaises(TypeError):
            bucket.get_all_keys(delimeter='foo')

    def test__get_all_query_args(self):
        bukket = Bucket()

        # Default.
        qa = bukket._get_all_query_args({})
        self.assertEqual(qa, '')

        # Default with initial.
        qa = bukket._get_all_query_args({}, 'initial=1')
        self.assertEqual(qa, 'initial=1')

        # Single param.
        qa = bukket._get_all_query_args({
            'foo': 'true'
        })
        self.assertEqual(qa, 'foo=true')

        # Single param with initial.
        qa = bukket._get_all_query_args({
            'foo': 'true'
        }, 'initial=1')
        self.assertEqual(qa, 'initial=1&foo=true')

        # Multiple params with all the weird cases.
        multiple_params = {
            'foo': 'true',
            # Ensure Unicode chars get encoded.
            'bar': '☃',
            # Ensure unicode strings with non-ascii characters get encoded
            'baz': u'χ',
            # Underscores are bad, m'kay?
            'some_other': 'thing',
            # Change the variant of ``max-keys``.
            'maxkeys': 0,
            # ``None`` values get excluded.
            'notthere': None,
            # Empty values also get excluded.
            'notpresenteither': '',
        }
        qa = bukket._get_all_query_args(multiple_params)
        self.assertEqual(
            qa,
            'bar=%E2%98%83&baz=%CF%87&foo=true&max-keys=0&some-other=thing'
        )

        # Multiple params with initial.
        qa = bukket._get_all_query_args(multiple_params, 'initial=1')
        self.assertEqual(
            qa,
            'initial=1&bar=%E2%98%83&baz=%CF%87&foo=true&max-keys=0&some-other=thing'
        )

    @patch.object(S3Connection, 'head_bucket')
    def test_bucket_copy_key_no_validate(self, mock_head_bucket):
        self.set_http_response(status_code=200)
        bucket = self.service_connection.create_bucket('mybucket')

        self.assertFalse(mock_head_bucket.called)
        self.service_connection.get_bucket('mybucket', validate=True)
        self.assertTrue(mock_head_bucket.called)

        mock_head_bucket.reset_mock()
        self.assertFalse(mock_head_bucket.called)
        try:
            bucket.copy_key('newkey', 'srcbucket', 'srckey', preserve_acl=True)
        except:
            # Will throw because of empty response.
            pass
        self.assertFalse(mock_head_bucket.called)

    @patch.object(Bucket, '_get_all')
    def test_bucket_encoding(self, mock_get_all):
        self.set_http_response(status_code=200)
        bucket = self.service_connection.get_bucket('mybucket')

        # First, without the encoding.
        mock_get_all.reset_mock()
        bucket.get_all_keys()
        mock_get_all.assert_called_with(
            [
                ('Contents', Key),
                ('CommonPrefixes', Prefix)
            ], '', None
        )

        # Now the variants with the encoding.
        mock_get_all.reset_mock()
        bucket.get_all_keys(encoding_type='url')
        mock_get_all.assert_called_with(
            [
                ('Contents', Key),
                ('CommonPrefixes', Prefix)
            ], '', None,
            encoding_type='url'
        )

        mock_get_all.reset_mock()
        bucket.get_all_versions(encoding_type='url')
        mock_get_all.assert_called_with(
            [
                ('Version', Key),
                ('CommonPrefixes', Prefix),
                ('DeleteMarker', DeleteMarker),
            ], 'versions', None,
            encoding_type='url'
        )

        mock_get_all.reset_mock()
        bucket.get_all_multipart_uploads(encoding_type='url')
        mock_get_all.assert_called_with(
            [
                ('Upload', MultiPartUpload),
                ('CommonPrefixes', Prefix)
            ], 'uploads', None,
            encoding_type='url'
        )

    @patch.object(Bucket, 'get_all_keys')
    @patch.object(Bucket, '_get_key_internal')
    def test_bucket_get_key_no_validate(self, mock_gki, mock_gak):
        self.set_http_response(status_code=200)
        bucket = self.service_connection.get_bucket('mybucket')
        key = bucket.get_key('mykey', validate=False)

        self.assertEqual(len(mock_gki.mock_calls), 0)
        self.assertTrue(isinstance(key, Key))
        self.assertEqual(key.name, 'mykey')

        with self.assertRaises(BotoClientError):
            bucket.get_key(
                'mykey',
                version_id='something',
                validate=False
            )

    def acl_policy(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
        <AccessControlPolicy xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
          <Owner>
            <ID>owner_id</ID>
            <DisplayName>owner_display_name</DisplayName>
          </Owner>
          <AccessControlList>
            <Grant>
              <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                       xsi:type="CanonicalUser">
                <ID>grantee_id</ID>
                <DisplayName>grantee_display_name</DisplayName>
              </Grantee>
              <Permission>FULL_CONTROL</Permission>
            </Grant>
          </AccessControlList>
        </AccessControlPolicy>"""

    def test_bucket_acl_policy_namespace(self):
        self.set_http_response(status_code=200)
        bucket = self.service_connection.get_bucket('mybucket')

        self.set_http_response(status_code=200, body=self.acl_policy())
        policy = bucket.get_acl()

        xml_policy = policy.to_xml()
        document = xml.dom.minidom.parseString(xml_policy)
        namespace = document.documentElement.namespaceURI
        self.assertEqual(namespace, 'http://s3.amazonaws.com/doc/2006-03-01/')
