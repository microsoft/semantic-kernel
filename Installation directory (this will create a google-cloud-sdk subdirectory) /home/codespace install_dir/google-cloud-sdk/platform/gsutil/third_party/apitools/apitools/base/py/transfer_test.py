# -*- coding: utf-8 -*-
#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for transfer.py."""
import string
import unittest

import httplib2
import json
import mock
import six
from six.moves import http_client

from apitools.base.py import base_api
from apitools.base.py import exceptions
from apitools.base.py import gzip
from apitools.base.py import http_wrapper
from apitools.base.py import transfer


class TransferTest(unittest.TestCase):

    def assertRangeAndContentRangeCompatible(self, request, response):
        request_prefix = 'bytes='
        self.assertIn('range', request.headers)
        self.assertTrue(request.headers['range'].startswith(request_prefix))
        request_range = request.headers['range'][len(request_prefix):]

        response_prefix = 'bytes '
        self.assertIn('content-range', response.info)
        response_header = response.info['content-range']
        self.assertTrue(response_header.startswith(response_prefix))
        response_range = (
            response_header[len(response_prefix):].partition('/')[0])

        msg = ('Request range ({0}) not a prefix of '
               'response_range ({1})').format(
                   request_range, response_range)
        self.assertTrue(response_range.startswith(request_range), msg=msg)

    def testComputeEndByte(self):
        total_size = 100
        chunksize = 10
        download = transfer.Download.FromStream(
            six.StringIO(), chunksize=chunksize, total_size=total_size)
        self.assertEqual(chunksize - 1,
                         download._Download__ComputeEndByte(0, end=50))

    def testComputeEndByteReturnNone(self):
        download = transfer.Download.FromStream(six.StringIO())
        self.assertIsNone(
            download._Download__ComputeEndByte(0, use_chunks=False))

    def testComputeEndByteNoChunks(self):
        total_size = 100
        download = transfer.Download.FromStream(
            six.StringIO(), chunksize=10, total_size=total_size)
        for end in (None, 1000):
            self.assertEqual(
                total_size - 1,
                download._Download__ComputeEndByte(0, end=end,
                                                   use_chunks=False),
                msg='Failed on end={0}'.format(end))

    def testComputeEndByteNoTotal(self):
        download = transfer.Download.FromStream(six.StringIO())
        default_chunksize = download.chunksize
        for chunksize in (100, default_chunksize):
            download.chunksize = chunksize
            for start in (0, 10):
                self.assertEqual(
                    download.chunksize + start - 1,
                    download._Download__ComputeEndByte(start),
                    msg='Failed on start={0}, chunksize={1}'.format(
                        start, chunksize))

    def testComputeEndByteSmallTotal(self):
        total_size = 100
        download = transfer.Download.FromStream(six.StringIO(),
                                                total_size=total_size)
        for start in (0, 10):
            self.assertEqual(total_size - 1,
                             download._Download__ComputeEndByte(start),
                             msg='Failed on start={0}'.format(start))

    def testDownloadThenStream(self):
        bytes_http = object()
        http = object()
        download_stream = six.StringIO()
        download = transfer.Download.FromStream(download_stream,
                                                total_size=26)
        download.bytes_http = bytes_http
        base_url = 'https://part.one/'
        with mock.patch.object(http_wrapper, 'MakeRequest',
                               autospec=True) as make_request:
            make_request.return_value = http_wrapper.Response(
                info={
                    'content-range': 'bytes 0-25/26',
                    'status': http_client.OK,
                },
                content=string.ascii_lowercase,
                request_url=base_url,
            )
            request = http_wrapper.Request(url='https://part.one/')
            download.InitializeDownload(request, http=http)
            self.assertEqual(1, make_request.call_count)
            received_request = make_request.call_args[0][1]
            self.assertEqual(base_url, received_request.url)
            self.assertRangeAndContentRangeCompatible(
                received_request, make_request.return_value)

        with mock.patch.object(http_wrapper, 'MakeRequest',
                               autospec=True) as make_request:
            make_request.return_value = http_wrapper.Response(
                info={
                    'status': http_client.REQUESTED_RANGE_NOT_SATISFIABLE,
                },
                content='error',
                request_url=base_url,
            )
            download.StreamInChunks()
            self.assertEqual(1, make_request.call_count)
            received_request = make_request.call_args[0][1]
            self.assertEqual('bytes=26-', received_request.headers['range'])

    def testGetRange(self):
        for (start_byte, end_byte) in [(0, 25), (5, 15), (0, 0), (25, 25)]:
            bytes_http = object()
            http = object()
            download_stream = six.StringIO()
            download = transfer.Download.FromStream(download_stream,
                                                    total_size=26,
                                                    auto_transfer=False)
            download.bytes_http = bytes_http
            base_url = 'https://part.one/'
            with mock.patch.object(http_wrapper, 'MakeRequest',
                                   autospec=True) as make_request:
                make_request.return_value = http_wrapper.Response(
                    info={
                        'content-range': 'bytes %d-%d/26' %
                                         (start_byte, end_byte),
                        'status': http_client.OK,
                    },
                    content=string.ascii_lowercase[start_byte:end_byte + 1],
                    request_url=base_url,
                )
                request = http_wrapper.Request(url='https://part.one/')
                download.InitializeDownload(request, http=http)
                download.GetRange(start_byte, end_byte)
                self.assertEqual(1, make_request.call_count)
                received_request = make_request.call_args[0][1]
                self.assertEqual(base_url, received_request.url)
                self.assertRangeAndContentRangeCompatible(
                    received_request, make_request.return_value)

    def testNonChunkedDownload(self):
        bytes_http = object()
        http = object()
        download_stream = six.StringIO()
        download = transfer.Download.FromStream(download_stream, total_size=52)
        download.bytes_http = bytes_http
        base_url = 'https://part.one/'

        with mock.patch.object(http_wrapper, 'MakeRequest',
                               autospec=True) as make_request:
            make_request.return_value = http_wrapper.Response(
                info={
                    'content-range': 'bytes 0-51/52',
                    'status': http_client.OK,
                },
                content=string.ascii_lowercase * 2,
                request_url=base_url,
            )
            request = http_wrapper.Request(url='https://part.one/')
            download.InitializeDownload(request, http=http)
            self.assertEqual(1, make_request.call_count)
            received_request = make_request.call_args[0][1]
            self.assertEqual(base_url, received_request.url)
            self.assertRangeAndContentRangeCompatible(
                received_request, make_request.return_value)
            download_stream.seek(0)
            self.assertEqual(string.ascii_lowercase * 2,
                             download_stream.getvalue())

    def testChunkedDownload(self):
        bytes_http = object()
        http = object()
        download_stream = six.StringIO()
        download = transfer.Download.FromStream(
            download_stream, chunksize=26, total_size=52)
        download.bytes_http = bytes_http

        # Setting autospec on a mock with an iterable side_effect is
        # currently broken (http://bugs.python.org/issue17826), so
        # instead we write a little function.
        def _ReturnBytes(unused_http, http_request,
                         *unused_args, **unused_kwds):
            url = http_request.url
            if url == 'https://part.one/':
                return http_wrapper.Response(
                    info={
                        'content-location': 'https://part.two/',
                        'content-range': 'bytes 0-25/52',
                        'status': http_client.PARTIAL_CONTENT,
                    },
                    content=string.ascii_lowercase,
                    request_url='https://part.one/',
                )
            elif url == 'https://part.two/':
                return http_wrapper.Response(
                    info={
                        'content-range': 'bytes 26-51/52',
                        'status': http_client.OK,
                    },
                    content=string.ascii_uppercase,
                    request_url='https://part.two/',
                )
            else:
                self.fail('Unknown URL requested: %s' % url)

        with mock.patch.object(http_wrapper, 'MakeRequest',
                               autospec=True) as make_request:
            make_request.side_effect = _ReturnBytes
            request = http_wrapper.Request(url='https://part.one/')
            download.InitializeDownload(request, http=http)
            self.assertEqual(2, make_request.call_count)
            for call in make_request.call_args_list:
                self.assertRangeAndContentRangeCompatible(
                    call[0][1], _ReturnBytes(*call[0]))
            download_stream.seek(0)
            self.assertEqual(string.ascii_lowercase + string.ascii_uppercase,
                             download_stream.getvalue())

    # @mock.patch.object(transfer.Upload, 'RefreshResumableUploadState',
    #                    new=mock.Mock())
    def testFinalizesTransferUrlIfClientPresent(self):
        """Tests download's enforcement of client custom endpoints."""
        mock_client = mock.Mock()
        fake_json_data = json.dumps({
            'auto_transfer': False,
            'progress': 0,
            'total_size': 0,
            'url': 'url',
        })
        transfer.Download.FromData(six.BytesIO(), fake_json_data,
                                   client=mock_client)
        mock_client.FinalizeTransferUrl.assert_called_once_with('url')

    def testMultipartEncoding(self):
        # This is really a table test for various issues we've seen in
        # the past; see notes below for particular histories.

        test_cases = [
            # Python's mime module by default encodes lines that start
            # with "From " as ">From ", which we need to make sure we
            # don't run afoul of when sending content that isn't
            # intended to be so encoded. This test calls out that we
            # get this right. We test for both the multipart and
            # non-multipart case.
            'line one\nFrom \nline two',

            # We had originally used a `six.StringIO` to hold the http
            # request body in the case of a multipart upload; for
            # bytes being uploaded in Python3, however, this causes
            # issues like this:
            # https://github.com/GoogleCloudPlatform/gcloud-python/issues/1760
            # We test below to ensure that we don't end up mangling
            # the body before sending.
            u'name,main_ingredient\nRäksmörgås,Räkor\nBaguette,Bröd',
        ]

        for upload_contents in test_cases:
            multipart_body = '{"body_field_one": 7}'
            upload_bytes = upload_contents.encode('ascii', 'backslashreplace')
            upload_config = base_api.ApiUploadInfo(
                accept=['*/*'],
                max_size=None,
                resumable_multipart=True,
                resumable_path=u'/resumable/upload',
                simple_multipart=True,
                simple_path=u'/upload',
            )
            url_builder = base_api._UrlBuilder('http://www.uploads.com')

            # Test multipart: having a body argument in http_request forces
            # multipart here.
            upload = transfer.Upload.FromStream(
                six.BytesIO(upload_bytes),
                'text/plain',
                total_size=len(upload_bytes))
            http_request = http_wrapper.Request(
                'http://www.uploads.com',
                headers={'content-type': 'text/plain'},
                body=multipart_body)
            upload.ConfigureRequest(upload_config, http_request, url_builder)
            self.assertEqual(
                'multipart', url_builder.query_params['uploadType'])
            rewritten_upload_contents = b'\n'.join(
                http_request.body.split(b'--')[2].splitlines()[1:])
            self.assertTrue(rewritten_upload_contents.endswith(upload_bytes))

            # Test non-multipart (aka media): no body argument means this is
            # sent as media.
            upload = transfer.Upload.FromStream(
                six.BytesIO(upload_bytes),
                'text/plain',
                total_size=len(upload_bytes))
            http_request = http_wrapper.Request(
                'http://www.uploads.com',
                headers={'content-type': 'text/plain'})
            upload.ConfigureRequest(upload_config, http_request, url_builder)
            self.assertEqual(url_builder.query_params['uploadType'], 'media')
            rewritten_upload_contents = http_request.body
            self.assertTrue(rewritten_upload_contents.endswith(upload_bytes))


class UploadTest(unittest.TestCase):

    def setUp(self):
        # Sample highly compressible data.
        self.sample_data = b'abc' * 200
        # Stream of the sample data.
        self.sample_stream = six.BytesIO(self.sample_data)
        # Sample url_builder.
        self.url_builder = base_api._UrlBuilder('http://www.uploads.com')
        # Sample request.
        self.request = http_wrapper.Request(
            'http://www.uploads.com',
            headers={'content-type': 'text/plain'})
        # Sample successful response.
        self.response = http_wrapper.Response(
            info={'status': http_client.OK,
                  'location': 'http://www.uploads.com'},
            content='',
            request_url='http://www.uploads.com',)
        # Sample failure response.
        self.fail_response = http_wrapper.Response(
            info={'status': http_client.SERVICE_UNAVAILABLE,
                  'location': 'http://www.uploads.com'},
            content='',
            request_url='http://www.uploads.com',)

    def testStreamInChunksCompressed(self):
        """Test that StreamInChunks will handle compression correctly."""
        # Create and configure the upload object.
        upload = transfer.Upload(
            stream=self.sample_stream,
            mime_type='text/plain',
            total_size=len(self.sample_data),
            close_stream=False,
            gzip_encoded=True)
        upload.strategy = transfer.RESUMABLE_UPLOAD
        # Set the chunk size so the entire stream is uploaded.
        upload.chunksize = len(self.sample_data)
        # Mock the upload to return the sample response.
        with mock.patch.object(transfer.Upload,
                               '_Upload__SendMediaRequest') as mock_result, \
                mock.patch.object(http_wrapper,
                                  'MakeRequest') as make_request:
            mock_result.return_value = self.response
            make_request.return_value = self.response

            # Initialization.
            upload.InitializeUpload(self.request, 'http')
            upload.StreamInChunks()
            # Get the uploaded request and end position of the stream.
            (request, _), _ = mock_result.call_args_list[0]
            # Ensure the mock was called.
            self.assertTrue(mock_result.called)
            # Ensure the correct content encoding was set.
            self.assertEqual(request.headers['Content-Encoding'], 'gzip')
            # Ensure the stream was compresed.
            self.assertLess(len(request.body), len(self.sample_data))

    def testStreamMediaCompressedFail(self):
        """Test that non-chunked uploads raise an exception.

        Ensure uploads with the compressed and resumable flags set called from
        StreamMedia raise an exception. Those uploads are unsupported.
        """
        # Create the upload object.
        upload = transfer.Upload(
            stream=self.sample_stream,
            mime_type='text/plain',
            total_size=len(self.sample_data),
            close_stream=False,
            auto_transfer=True,
            gzip_encoded=True)
        upload.strategy = transfer.RESUMABLE_UPLOAD
        # Mock the upload to return the sample response.
        with mock.patch.object(http_wrapper,
                               'MakeRequest') as make_request:
            make_request.return_value = self.response

            # Initialization.
            upload.InitializeUpload(self.request, 'http')
            # Ensure stream media raises an exception when the upload is
            # compressed. Compression is not supported on non-chunked uploads.
            with self.assertRaises(exceptions.InvalidUserInputError):
                upload.StreamMedia()

    def testAutoTransferCompressed(self):
        """Test that automatic transfers are compressed.

        Ensure uploads with the compressed, resumable, and automatic transfer
        flags set call StreamInChunks. StreamInChunks is tested in an earlier
        test.
        """
        # Create the upload object.
        upload = transfer.Upload(
            stream=self.sample_stream,
            mime_type='text/plain',
            total_size=len(self.sample_data),
            close_stream=False,
            gzip_encoded=True)
        upload.strategy = transfer.RESUMABLE_UPLOAD
        # Mock the upload to return the sample response.
        with mock.patch.object(transfer.Upload,
                               'StreamInChunks') as mock_result, \
                mock.patch.object(http_wrapper,
                                  'MakeRequest') as make_request:
            mock_result.return_value = self.response
            make_request.return_value = self.response

            # Initialization.
            upload.InitializeUpload(self.request, 'http')
            # Ensure the mock was called.
            self.assertTrue(mock_result.called)

    def testMultipartCompressed(self):
        """Test that multipart uploads are compressed."""
        # Create the multipart configuration.
        upload_config = base_api.ApiUploadInfo(
            accept=['*/*'],
            max_size=None,
            simple_multipart=True,
            simple_path=u'/upload',)
        # Create the upload object.
        upload = transfer.Upload(
            stream=self.sample_stream,
            mime_type='text/plain',
            total_size=len(self.sample_data),
            close_stream=False,
            gzip_encoded=True)
        # Set a body to trigger multipart configuration.
        self.request.body = '{"body_field_one": 7}'
        # Configure the request.
        upload.ConfigureRequest(upload_config, self.request, self.url_builder)
        # Ensure the request is a multipart request now.
        self.assertEqual(
            self.url_builder.query_params['uploadType'], 'multipart')
        # Ensure the request is gzip encoded.
        self.assertEqual(self.request.headers['Content-Encoding'], 'gzip')
        # Ensure data is compressed
        self.assertLess(len(self.request.body), len(self.sample_data))
        # Ensure uncompressed data includes the sample data.
        with gzip.GzipFile(fileobj=six.BytesIO(self.request.body)) as f:
            original = f.read()
            self.assertTrue(self.sample_data in original)

    def testMediaCompressed(self):
        """Test that media uploads are compressed."""
        # Create the media configuration.
        upload_config = base_api.ApiUploadInfo(
            accept=['*/*'],
            max_size=None,
            simple_multipart=True,
            simple_path=u'/upload',)
        # Create the upload object.
        upload = transfer.Upload(
            stream=self.sample_stream,
            mime_type='text/plain',
            total_size=len(self.sample_data),
            close_stream=False,
            gzip_encoded=True)
        # Configure the request.
        upload.ConfigureRequest(upload_config, self.request, self.url_builder)
        # Ensure the request is a media request now.
        self.assertEqual(self.url_builder.query_params['uploadType'], 'media')
        # Ensure the request is gzip encoded.
        self.assertEqual(self.request.headers['Content-Encoding'], 'gzip')
        # Ensure data is compressed
        self.assertLess(len(self.request.body), len(self.sample_data))
        # Ensure uncompressed data includes the sample data.
        with gzip.GzipFile(fileobj=six.BytesIO(self.request.body)) as f:
            original = f.read()
            self.assertTrue(self.sample_data in original)

    def HttpRequestSideEffect(self, responses=None):
        responses = [(response.info, response.content)
                     for response in responses]

        def _side_effect(uri, **kwargs):  # pylint: disable=unused-argument
            body = kwargs['body']
            read_func = getattr(body, 'read', None)
            if read_func:
                # If the body is a stream, consume the stream.
                body = read_func()
            self.assertEqual(int(kwargs['headers']['content-length']),
                             len(body))
            return responses.pop(0)
        return _side_effect

    def testRetryRequestChunks(self):
        """Test that StreamInChunks will retry correctly."""
        refresh_response = http_wrapper.Response(
            info={'status': http_wrapper.RESUME_INCOMPLETE,
                  'location': 'http://www.uploads.com'},
            content='',
            request_url='http://www.uploads.com',)

        # Create and configure the upload object.
        bytes_http = httplib2.Http()
        upload = transfer.Upload(
            stream=self.sample_stream,
            mime_type='text/plain',
            total_size=len(self.sample_data),
            close_stream=False,
            http=bytes_http)

        upload.strategy = transfer.RESUMABLE_UPLOAD
        # Set the chunk size so the entire stream is uploaded.
        upload.chunksize = len(self.sample_data)
        # Mock the upload to return the sample response.
        with mock.patch.object(bytes_http,
                               'request') as make_request:
            # This side effect also checks the request body.
            responses = [
                self.response,  # Initial request in InitializeUpload().
                self.fail_response,  # 503 status code from server.
                refresh_response,  # Refresh upload progress.
                self.response,  # Successful request.
            ]
            make_request.side_effect = self.HttpRequestSideEffect(responses)

            # Initialization.
            upload.InitializeUpload(self.request, bytes_http)
            upload.StreamInChunks()

            # Ensure the mock was called the correct number of times.
            self.assertEquals(make_request.call_count, len(responses))

    def testStreamInChunks(self):
        """Test StreamInChunks."""
        resume_incomplete_responses = [http_wrapper.Response(
            info={'status': http_wrapper.RESUME_INCOMPLETE,
                  'location': 'http://www.uploads.com',
                  'range': '0-{}'.format(end)},
            content='',
            request_url='http://www.uploads.com',) for end in [199, 399, 599]]
        responses = [
            self.response  # Initial request in InitializeUpload().
        ] + resume_incomplete_responses + [
            self.response,  # Successful request.
        ]
        # Create and configure the upload object.
        bytes_http = httplib2.Http()
        upload = transfer.Upload(
            stream=self.sample_stream,
            mime_type='text/plain',
            total_size=len(self.sample_data),
            close_stream=False,
            http=bytes_http)

        upload.strategy = transfer.RESUMABLE_UPLOAD
        # Set the chunk size so the entire stream is uploaded.
        upload.chunksize = 200
        # Mock the upload to return the sample response.
        with mock.patch.object(bytes_http,
                               'request') as make_request:
            # This side effect also checks the request body.
            make_request.side_effect = self.HttpRequestSideEffect(responses)

            # Initialization.
            upload.InitializeUpload(self.request, bytes_http)
            upload.StreamInChunks()

            # Ensure the mock was called the correct number of times.
            self.assertEquals(make_request.call_count, len(responses))

    @mock.patch.object(transfer.Upload, 'RefreshResumableUploadState',
                       new=mock.Mock())
    def testFinalizesTransferUrlIfClientPresent(self):
        """Tests upload's enforcement of client custom endpoints."""
        mock_client = mock.Mock()
        mock_http = mock.Mock()
        fake_json_data = json.dumps({
            'auto_transfer': False,
            'mime_type': '',
            'total_size': 0,
            'url': 'url',
        })
        transfer.Upload.FromData(self.sample_stream, fake_json_data, mock_http,
                                 client=mock_client)
        mock_client.FinalizeTransferUrl.assert_called_once_with('url')
