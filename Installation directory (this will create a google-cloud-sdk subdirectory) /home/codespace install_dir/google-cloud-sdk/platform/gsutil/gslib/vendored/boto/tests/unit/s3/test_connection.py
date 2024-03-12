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
from tests.compat import unittest
from tests.unit import AWSMockServiceTestCase
from tests.unit import MockServiceWithConfigTestCase

from boto.connection import AWSAuthConnection
from boto.s3.connection import S3Connection, HostRequiredError
from boto.s3.connection import S3ResponseError, Bucket


class TestSignatureAlteration(AWSMockServiceTestCase):
    connection_class = S3Connection

    def test_unchanged(self):
        self.assertEqual(
            self.service_connection._required_auth_capability(),
            ['hmac-v4-s3']
        )

    def test_switched(self):
        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            host='s3.cn-north-1.amazonaws.com.cn'
        )
        self.assertEqual(
            conn._required_auth_capability(),
            ['hmac-v4-s3']
        )


class TestAnon(MockServiceWithConfigTestCase):
    connection_class = S3Connection

    def test_generate_url(self):
        conn = self.connection_class(
            anon=True,
            host='s3.amazonaws.com'
        )
        url = conn.generate_url(0, 'GET', bucket='examplebucket', key='test.txt')
        self.assertNotIn('Signature=', url)

    def test_anon_default_taken_from_config_opt(self):
        self.config = {
            's3': {
                # Value must be a string for `config.getbool` to not crash.
                'no_sign_request': 'True',
            }
        }

        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            host='s3.amazonaws.com',
        )
        url = conn.generate_url(
            0, 'GET', bucket='examplebucket', key='test.txt')
        self.assertNotIn('Signature=', url)

    def test_explicit_anon_arg_overrides_config_value(self):
        self.config = {
            's3': {
                # Value must be a string for `config.getbool` to not crash.
                'no_sign_request': 'True',
            }
        }

        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            host='s3.amazonaws.com',
            anon=False
        )
        url = conn.generate_url(
            0, 'GET', bucket='examplebucket', key='test.txt')
        self.assertIn('Signature=', url)


class TestPresigned(MockServiceWithConfigTestCase):
    connection_class = S3Connection

    def test_presign_respect_query_auth(self):
        self.config = {
            's3': {
                'use-sigv4': False,
            }
        }

        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            host='s3.amazonaws.com'
        )

        url_enabled = conn.generate_url(86400, 'GET', bucket='examplebucket',
                                        key='test.txt', query_auth=True)

        url_disabled = conn.generate_url(86400, 'GET', bucket='examplebucket',
                                         key='test.txt', query_auth=False)
        self.assertIn('Signature=', url_enabled)
        self.assertNotIn('Signature=', url_disabled)


class TestSigV4HostError(MockServiceWithConfigTestCase):
    connection_class = S3Connection

    def test_historical_behavior(self):
        self.assertEqual(
            self.service_connection._required_auth_capability(),
            ['hmac-v4-s3']
        )
        self.assertEqual(self.service_connection.host, 's3.amazonaws.com')

    def test_sigv4_opt_in(self):
        host_value = 's3.cn-north-1.amazonaws.com.cn'

        # Switch it at the config, so we can check to see how the host is
        # handled.
        self.config = {
            's3': {
                'use-sigv4': True,
            }
        }

        # Ensure passing a ``host`` in the connection args still works.
        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            host=host_value
        )
        self.assertEqual(
            conn._required_auth_capability(),
            ['hmac-v4-s3']
        )
        self.assertEqual(
            conn.host,
            host_value
        )

        # Ensure that the host is populated from our config if one is not
        # provided when creating a connection.
        self.config = {
            's3': {
                'host': host_value,
                'use-sigv4': True,
            }
        }
        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more'
        )
        self.assertEqual(
            conn._required_auth_capability(),
            ['hmac-v4-s3']
        )
        self.assertEqual(
            conn.host,
            host_value
        )


class TestSigV4Presigned(MockServiceWithConfigTestCase):
    connection_class = S3Connection

    def test_sigv4_presign(self):
        self.config = {
            's3': {
                'use-sigv4': True,
            }
        }

        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            host='s3.amazonaws.com'
        )

        # Here we force an input iso_date to ensure we always get the
        # same signature.
        url = conn.generate_url_sigv4(86400, 'GET', bucket='examplebucket',
                                      key='test.txt',
                                      iso_date='20140625T000000Z')

        self.assertIn(
            'a937f5fbc125d98ac8f04c49e0204ea1526a7b8ca058000a54c192457be05b7d',
            url)

    def test_sigv4_presign_respects_is_secure(self):
        self.config = {
            's3': {
                'use-sigv4': True,
            }
        }

        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            host='s3.amazonaws.com',
            is_secure=True,
        )

        url = conn.generate_url_sigv4(86400, 'GET', bucket='examplebucket',
                                      key='test.txt')
        self.assertTrue(url.startswith(
            'https://examplebucket.s3.amazonaws.com/test.txt?'))

        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            host='s3.amazonaws.com',
            is_secure=False,
        )

        url = conn.generate_url_sigv4(86400, 'GET', bucket='examplebucket',
                                      key='test.txt')
        self.assertTrue(url.startswith(
            'http://examplebucket.s3.amazonaws.com/test.txt?'))

    def test_sigv4_presign_optional_params(self):
        self.config = {
            's3': {
                'use-sigv4': True,
            }
        }

        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            security_token='token',
            host='s3.amazonaws.com'
        )

        url = conn.generate_url_sigv4(86400, 'GET', bucket='examplebucket',
                                      key='test.txt', version_id=2)

        self.assertIn('VersionId=2', url)
        self.assertIn('X-Amz-Security-Token=token', url)

    def test_sigv4_presign_respect_query_auth(self):
        self.config = {
            's3': {
                'use-sigv4': True,
            }
        }

        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            host='s3.amazonaws.com'
        )

        url_enabled = conn.generate_url(86400, 'GET', bucket='examplebucket',
                                        key='test.txt', query_auth=True)

        url_disabled = conn.generate_url(86400, 'GET', bucket='examplebucket',
                                         key='test.txt', query_auth=False)
        self.assertIn('Signature=', url_enabled)
        self.assertNotIn('Signature=', url_disabled)

    def test_sigv4_presign_headers(self):
        self.config = {
            's3': {
                'use-sigv4': True,
            }
        }

        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            host='s3.amazonaws.com'
        )

        headers = {'x-amz-meta-key': 'val'}
        url = conn.generate_url_sigv4(86400, 'GET', bucket='examplebucket',
                                      key='test.txt', headers=headers)

        self.assertIn('host', url)
        self.assertIn('x-amz-meta-key', url)

    def test_sigv4_presign_response_headers(self):
        self.config = {
            's3': {
                'use-sigv4': True,
            }
        }

        conn = self.connection_class(
            aws_access_key_id='less',
            aws_secret_access_key='more',
            host='s3.amazonaws.com'
        )

        response_headers = {'response-content-disposition': 'attachment; filename="file.ext"'}
        url = conn.generate_url_sigv4(86400, 'GET', bucket='examplebucket',
                                      key='test.txt', response_headers=response_headers)

        self.assertIn('host', url)
        self.assertIn('response-content-disposition', url)


class TestUnicodeCallingFormat(AWSMockServiceTestCase):
    connection_class = S3Connection

    def default_body(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
<ListAllMyBucketsResult xmlns="http://doc.s3.amazonaws.com/2006-03-01">
  <Owner>
    <ID>bcaf1ffd86f461ca5fb16fd081034f</ID>
    <DisplayName>webfile</DisplayName>
  </Owner>
  <Buckets>
    <Bucket>
      <Name>quotes</Name>
      <CreationDate>2006-02-03T16:45:09.000Z</CreationDate>
    </Bucket>
    <Bucket>
      <Name>samples</Name>
      <CreationDate>2006-02-03T16:41:58.000Z</CreationDate>
    </Bucket>
  </Buckets>
</ListAllMyBucketsResult>"""

    def create_service_connection(self, **kwargs):
        kwargs['calling_format'] = u'boto.s3.connection.OrdinaryCallingFormat'
        return super(TestUnicodeCallingFormat,
                     self).create_service_connection(**kwargs)

    def test_unicode_calling_format(self):
        self.set_http_response(status_code=200)
        self.service_connection.get_all_buckets()


class TestHeadBucket(AWSMockServiceTestCase):
    connection_class = S3Connection

    def default_body(self):
        # HEAD requests always have an empty body.
        return ""

    def test_head_bucket_success(self):
        self.set_http_response(status_code=200)
        buck = self.service_connection.head_bucket('my-test-bucket')
        self.assertTrue(isinstance(buck, Bucket))
        self.assertEqual(buck.name, 'my-test-bucket')

    def test_head_bucket_forbidden(self):
        self.set_http_response(status_code=403)

        with self.assertRaises(S3ResponseError) as cm:
            self.service_connection.head_bucket('cant-touch-this')

        err = cm.exception
        self.assertEqual(err.status, 403)
        self.assertEqual(err.error_code, 'AccessDenied')
        self.assertEqual(err.message, 'Access Denied')

    def test_head_bucket_notfound(self):
        self.set_http_response(status_code=404)

        with self.assertRaises(S3ResponseError) as cm:
            self.service_connection.head_bucket('totally-doesnt-exist')

        err = cm.exception
        self.assertEqual(err.status, 404)
        self.assertEqual(err.error_code, 'NoSuchBucket')
        self.assertEqual(err.message, 'The specified bucket does not exist')

    def test_head_bucket_other(self):
        self.set_http_response(status_code=405)

        with self.assertRaises(S3ResponseError) as cm:
            self.service_connection.head_bucket('you-broke-it')

        err = cm.exception
        self.assertEqual(err.status, 405)
        # We don't have special-cases for this error status.
        self.assertEqual(err.error_code, None)
        self.assertEqual(err.message, '')

RETRY_REGION_BYTES = b'us-east-2'

AUTHORIZATION_HEADER_MALFORMED=(
    b'<Error><Code>AuthorizationHeaderMalformed</Code><Message>The '
    b'authorization header is malformed; the region \'us-east-1\' '
    b'is wrong; expecting \'%s\'</Message>'
    b'<Region>us-east-2</Region><RequestId>asdf</RequestId>'
    b'<HostId>asdf</HostId></Error>'
) % RETRY_REGION_BYTES

ILLEGAL_LOCATION_CONSTRAINT_SPECIFIED_REGION = (
    b'<Error><Code>IllegalLocationConstraintException</Code>'
    b'<Message>The %s location constraint is incompatible '
    b'for the region specific endpoint this request was sent to.'
    b'</Message><RequestId>asdf</RequestId>'
    b'<HostId>asdf</HostId></Error>'
) % RETRY_REGION_BYTES

PERMANENT_REDIRECT = (
    b'<Error><Code>PermanentRedirect</Code><Message>The bucket you '
    b'are attempting to access must be addressed using the '
    b'specified endpoint. Please send all future requests to this '
    b'endpoint.</Message><Endpoint>'
    b'bucket.s3.%s.amazonaws.com</Endpoint>'
    b'<Bucket>bucket</Bucket><RequestId>asdf</RequestId>'
    b'<HostId>asdf</HostId></Error>'
) % RETRY_REGION_BYTES

ILLEGAL_LOCATION_CONSTRAINT_UNSPECIFIED_REGION = (
    b'<Error><Code>IllegalLocationConstraintException</Code>'
    b'<Message>The unspecified location constraint is incompatible '
    b'for the region specific endpoint this request was sent to.'
    b'</Message><RequestId>asdf</RequestId>'
    b'<HostId>asdf</HostId></Error>'
)

# This output cannot come from the API, but it's here to test
# that strings not matching the regex handling this error are
# handled gracefully.
ILLEGAL_LOCATION_CONSTRAINT_MALFORMED = (
    b'<Error><Code>IllegalLocationConstraintException</Code>'
    b'<Message>Some random string.</Message><RequestId>asdf</RequestId>'
    b'<HostId>asdf</HostId></Error>'
)

ERRORS_WITH_REGION_IN_BODY = (
    (400, AUTHORIZATION_HEADER_MALFORMED),
    (400, ILLEGAL_LOCATION_CONSTRAINT_SPECIFIED_REGION),
    (301, PERMANENT_REDIRECT)
)

ERRORS_WITHOUT_REGION_IN_BODY = (
    (400, ILLEGAL_LOCATION_CONSTRAINT_UNSPECIFIED_REGION),
    (400, ILLEGAL_LOCATION_CONSTRAINT_MALFORMED)
)


class TestMakeRequestRetriesWithCorrectHost(AWSMockServiceTestCase):

    def setUp(self):
        self.connection = AWSAuthConnection('s3.amazonaws.com')

        self.non_retriable_code = 404
        self.retry_status_codes = [301, 400]
        self.success_response = self.create_response(200)

        self.default_host = 'bucket.s3.amazonaws.com'
        self.retry_region = RETRY_REGION_BYTES.decode('utf-8')
        self.default_retried_host = (
            'bucket.s3.%s.amazonaws.com' % self.retry_region
        )
        self.test_headers = [('x-amz-bucket-region', self.retry_region)]

    def test_non_retriable_status_returns_original_response(self):
        with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
            error_response = self.create_response(self.non_retriable_code)
            mocked_mexe.side_effect = [error_response]

            response = self.connection.make_request(
                'HEAD', '/', host=self.default_host)

            self.assertEqual(response, error_response)
            # called_once_with does not compare equality correctly with
            # HTTPResponse objects.
            self.assertEqual(mocked_mexe.call_count, 1)
            self.assertEqual(
                mocked_mexe.call_args[0][0].host,
                self.default_host
            )


    def test_non_retriable_host_returns_original_response(self):
        for code in self.retry_status_codes:
            with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
                error_response = self.create_response(code)
                mocked_mexe.side_effect = [error_response]

                other_host = 'bucket.some-other-provider.com'
                response = self.connection.make_request(
                    'HEAD', '/', host=other_host)

                self.assertEqual(response, error_response)
                self.assertEqual(mocked_mexe.call_count, 1)
                self.assertEqual(
                    mocked_mexe.call_args[0][0].host,
                    other_host
                )

    def test_non_retriable_status_raises_original_exception(self):
        with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
            error_response = S3ResponseError(self.non_retriable_code, 'reason')
            mocked_mexe.side_effect = [error_response]

            with self.assertRaises(S3ResponseError) as cm:
                self.connection.make_request(
                    'HEAD', '/', host=self.default_host)

            self.assertEqual(cm.exception, error_response)
            self.assertEqual(mocked_mexe.call_count, 1)
            self.assertEqual(
                mocked_mexe.call_args[0][0].host,
                self.default_host
            )

    def test_non_retriable_host_raises_original_exception(self):
        with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
            error_response = S3ResponseError(self.non_retriable_code, 'reason')
            mocked_mexe.side_effect = [error_response]

            other_host = 'bucket.some-other-provider.com'
            with self.assertRaises(S3ResponseError) as cm:
                self.connection.make_request(
                    'HEAD', '/', host=other_host)

            self.assertEqual(cm.exception, error_response)
            self.assertEqual(mocked_mexe.call_count, 1)
            self.assertEqual(
                mocked_mexe.call_args[0][0].host,
                other_host
            )

    def test_response_retries_from_callable_headers(self):
        for code in self.retry_status_codes:
            with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
                mocked_mexe.side_effect = [
                    self.create_response(code, header=self.test_headers),
                    self.success_response
                ]

                response = self.connection.make_request(
                    'HEAD', '/', host=self.default_host)

                self.assertEqual(response, self.success_response)
                self.assertEqual(mocked_mexe.call_count, 2)
                self.assertEqual(
                    mocked_mexe.call_args[0][0].host,
                    self.default_retried_host
                )

    def test_retry_changes_host_with_region(self):
        with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
            # Assume 400 with callable headers results uses the same url
            # manipulation as all of the other successful cases.
            mocked_mexe.side_effect = [
                self.create_response(400, header=self.test_headers),
                self.success_response
            ]

            response = self.connection.make_request(
                'HEAD', '/', host=self.default_host)

            self.assertEqual(response, self.success_response)
            self.assertEqual(mocked_mexe.call_count, 2)
            self.assertEqual(
                mocked_mexe.call_args[0][0].host,
                self.default_retried_host
            )

    def test_retry_changes_host_with_multiple_s3_occurrences(self):
        with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
            # Assume 400 with callable headers results uses the same url
            # manipulation as all of the other successful cases.
            mocked_mexe.side_effect = [
                self.create_response(400, header=self.test_headers),
                self.success_response
            ]

            response = self.connection.make_request(
                'HEAD', '/', host='a.s3.a.s3.amazonaws.com')

            self.assertEqual(response, self.success_response)
            self.assertEqual(mocked_mexe.call_count, 2)
            self.assertEqual(
                mocked_mexe.call_args[0][0].host,
                'a.s3.a.s3.us-east-2.amazonaws.com'
            )

    def test_retry_changes_host_with_s3_in_region(self):
        with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
            # Assume 400 with callable headers results uses the same url
            # manipulation as all of the other successful cases.
            mocked_mexe.side_effect = [
                self.create_response(400, header=self.test_headers),
                self.success_response
            ]

            response = self.connection.make_request(
                'HEAD', '/', host='bucket.s3.asdf-s3.amazonaws.com')

            self.assertEqual(response, self.success_response)
            self.assertEqual(mocked_mexe.call_count, 2)
            self.assertEqual(
                mocked_mexe.call_args[0][0].host,
                self.default_retried_host
            )

    def test_response_body_parsed_for_region(self):
        for code, body in ERRORS_WITH_REGION_IN_BODY:
            with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
                mocked_mexe.side_effect = [
                    self.create_response(code, body=body),
                    self.success_response
                ]

                response = self.connection.make_request(
                    'HEAD', '/', host=self.default_host)

                self.assertEqual(response, self.success_response)
                self.assertEqual(mocked_mexe.call_count, 2)
                self.assertEqual(
                    mocked_mexe.call_args[0][0].host,
                    self.default_retried_host
                )

    def test_error_body_parsed_for_region(self):
        for code, body in ERRORS_WITH_REGION_IN_BODY:
            with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
                mocked_mexe.side_effect = [
                    S3ResponseError(code, 'reason', body=body),
                    self.success_response
                ]

                response = self.connection.make_request(
                    'HEAD', '/', host=self.default_host)

                self.assertEqual(response, self.success_response)
                self.assertEqual(mocked_mexe.call_count, 2)
                self.assertEqual(
                    mocked_mexe.call_args[0][0].host,
                    self.default_retried_host
                )

    def test_response_without_region_header_retries_from_bucket_head(self):
        for code in self.retry_status_codes:
            with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
                mocked_mexe.side_effect = [
                    self.create_response(code),
                    self.create_response(200, header=self.test_headers),
                    self.success_response
                ]

                response = self.connection.make_request(
                    'HEAD', '/', host=self.default_host)

                self.assertEqual(response, self.success_response)
                self.assertEqual(mocked_mexe.call_count, 3)
                self.assertEqual(
                    mocked_mexe.call_args[0][0].host,
                    self.default_retried_host
                )

    def test_response_body_without_region_sends_bucket_head(self):
        for code, body in ERRORS_WITHOUT_REGION_IN_BODY:
            with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
                mocked_mexe.side_effect = [
                    self.create_response(code, body=body),
                    self.create_response(200, header=self.test_headers),
                    self.success_response
                ]

                response = self.connection.make_request(
                    'HEAD', '/', host=self.default_host)

                self.assertEqual(response, self.success_response)
                self.assertEqual(mocked_mexe.call_count, 3)
                self.assertEqual(
                    mocked_mexe.call_args[0][0].host,
                    self.default_retried_host
                )

    def test_error_body_without_region_retries_from_bucket_head_request(self):
        for code, body in ERRORS_WITHOUT_REGION_IN_BODY:
            with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
                mocked_mexe.side_effect = [
                    S3ResponseError(code, 'reason', body=body),
                    self.create_response(200, header=self.test_headers),
                    self.success_response
                ]

                response = self.connection.make_request(
                    'HEAD', '/', host=self.default_host)

                self.assertEqual(response, self.success_response)
                self.assertEqual(mocked_mexe.call_count, 3)
                self.assertEqual(
                    mocked_mexe.call_args[0][0].host,
                    self.default_retried_host
                )

    def test_retry_head_request_lacks_region_returns_original_response(self):
        for code in self.retry_status_codes:
            with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
                error_response = self.create_response(code)
                mocked_mexe.side_effect = [
                    error_response,
                    self.create_response(200, header=[])  # no region in header.
                ]

                response = self.connection.make_request(
                    'HEAD', '/', host=self.default_host)

                self.assertEqual(response, error_response)
                self.assertEqual(mocked_mexe.call_count, 2)
                self.assertEqual(
                    mocked_mexe.call_args[0][0].host,
                    self.default_host
                )

    def test_retry_head_request_lacks_region_raises_original_exception(self):
        for code in self.retry_status_codes:
            with mock.patch.object(self.connection, '_mexe') as mocked_mexe:
                error_response = S3ResponseError(code, 'reason')
                mocked_mexe.side_effect = [
                    error_response,
                    self.create_response(200, header=[])
                ]

                with self.assertRaises(S3ResponseError) as cm:
                    response = self.connection.make_request(
                        'HEAD', '/', host=self.default_host)

                self.assertEqual(cm.exception, error_response)
                self.assertEqual(mocked_mexe.call_count, 2)
                self.assertEqual(
                    mocked_mexe.call_args[0][0].host,
                    self.default_host
                )


if __name__ == "__main__":
    unittest.main()
