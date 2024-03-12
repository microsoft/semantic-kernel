# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for media helper functions and classes for GCS JSON API."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import email
from gslib.gcs_json_media import BytesTransferredContainer
from gslib.gcs_json_media import HttpWithDownloadStream
from gslib.gcs_json_media import UploadCallbackConnectionClassFactory
import gslib.tests.testcase as testcase
import httplib2
import io
import six

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import http_client
from six.moves import mock

# Assigning string representations of the appropriate package, used for
# '@mock.patch` methods that take a string in the following format:
# "package.module.ClassName"
if six.PY2:
  https_connection = 'httplib.HTTPSConnection'
else:
  https_connection = 'http.client.HTTPSConnection'


class TestUploadCallbackConnection(testcase.GsUtilUnitTestCase):
  """Tests for the upload callback connection."""

  def setUp(self):
    super(TestUploadCallbackConnection, self).setUp()
    self.bytes_container = BytesTransferredContainer()
    self.class_factory = UploadCallbackConnectionClassFactory(
        self.bytes_container,
        buffer_size=50,
        total_size=100,
        progress_callback='Sample')
    self.instance = self.class_factory.GetConnectionClass()('host')

  @mock.patch(https_connection)
  def testHeaderDefaultBehavior(self, mock_conn):
    """Test the size modifier is correct under expected headers."""
    mock_conn.putheader.return_value = None
    self.instance.putheader('content-encoding', 'gzip')
    self.instance.putheader('content-length', '10')
    self.instance.putheader('content-range', 'bytes 0-104/*')
    # Ensure the modifier is as expected.
    self.assertAlmostEqual(self.instance.size_modifier, 10.5)

  @mock.patch(https_connection)
  def testHeaderIgnoreWithoutGzip(self, mock_conn):
    """Test that the gzip content-encoding is required to modify size."""
    mock_conn.putheader.return_value = None
    self.instance.putheader('content-length', '10')
    self.instance.putheader('content-range', 'bytes 0-99/*')
    # Ensure the modifier is unchanged.
    self.assertAlmostEqual(self.instance.size_modifier, 1.0)

  @mock.patch(https_connection)
  def testHeaderRangeFormatX_YSlashStar(self, mock_conn):
    """Test content-range header format X-Y/* """
    self.instance.putheader('content-encoding', 'gzip')
    self.instance.putheader('content-length', '10')
    self.instance.putheader('content-range', 'bytes 0-99/*')
    # Ensure the modifier is as expected.
    self.assertAlmostEqual(self.instance.size_modifier, 10.0)

  @mock.patch(https_connection)
  def testHeaderRangeFormatStarSlash100(self, mock_conn):
    """Test content-range header format */100 """
    self.instance.putheader('content-encoding', 'gzip')
    self.instance.putheader('content-length', '10')
    self.instance.putheader('content-range', 'bytes */100')
    # Ensure the modifier is as expected.
    self.assertAlmostEqual(self.instance.size_modifier, 1.0)

  @mock.patch(https_connection)
  def testHeaderRangeFormat0_99Slash100(self, mock_conn):
    """Test content-range header format 0-99/100 """
    self.instance.putheader('content-encoding', 'gzip')
    self.instance.putheader('content-length', '10')
    self.instance.putheader('content-range', 'bytes 0-99/100')
    # Ensure the modifier is as expected.
    self.assertAlmostEqual(self.instance.size_modifier, 10.0)

  @mock.patch(https_connection)
  def testHeaderParseFailure(self, mock_conn):
    """Test incorrect header values do not raise exceptions."""
    mock_conn.putheader.return_value = None
    self.instance.putheader('content-encoding', 'gzip')
    self.instance.putheader('content-length', 'bytes 10')
    self.instance.putheader('content-range', 'not a number')
    # Ensure the modifier is unchanged.
    self.assertAlmostEqual(self.instance.size_modifier, 1.0)

  @mock.patch('gslib.progress_callback.ProgressCallbackWithTimeout')
  @mock.patch('httplib2.HTTPSConnectionWithTimeout')
  def testSendDefaultBehavior(self, mock_conn, mock_callback):
    mock_conn.send.return_value = None
    self.instance.size_modifier = 2
    self.instance.processed_initial_bytes = True
    self.instance.callback_processor = mock_callback
    # Send 10 bytes of data.
    sample_data = b'0123456789'
    self.instance.send(sample_data)
    # Ensure the data is fully sent since the buffer size is 50 bytes.
    self.assertTrue(mock_conn.send.called)
    (_, sent_data), _ = mock_conn.send.call_args_list[0]
    self.assertEqual(sent_data, sample_data)
    # Ensure the progress callback is correctly scaled.
    self.assertTrue(mock_callback.Progress.called)
    [sent_bytes], _ = mock_callback.Progress.call_args_list[0]
    self.assertEqual(sent_bytes, 20)


class TestHttpWithDownloadStream(testcase.GsUtilUnitTestCase):

  def test_incomplete_download_sets_content_length_correctly(self):
    expected_content_length = 100
    bytes_returned_by_server = 'byte count less than content length'

    http_response = mock.Mock(spec=http_client.HTTPResponse)
    http_response.reason = 'reason'
    http_response.version = 'version'
    http_response.status = http_client.OK
    http_response.read.side_effect = [bytes_returned_by_server, '']

    http_response.getheaders.return_value = [('Content-Length',
                                              expected_content_length)]
    # This method is only called with content-length:
    http_response.getheader.return_value = expected_content_length

    headers_stream = io.BytesIO(b'Content-Length:%d' % expected_content_length)
    if six.PY2:
      http_response.msg = http_client.HTTPMessage(headers_stream)
    else:
      http_response.msg = http_client.parse_headers(headers_stream)

    mock_connection = mock.Mock(spec=http_client.HTTPConnection)
    mock_connection.getresponse.return_value = http_response

    http = HttpWithDownloadStream()
    http.stream = mock.Mock(spec=io.BufferedIOBase)
    http.stream.mode = 'wb'
    http._conn_request(mock_connection, 'uri', 'GET', 'body', 'headers')

    # To resume this download correctly, the response needs to have the number
    # of bytes we actually received, not the number of bytes in the original
    # content-length header.
    self.assertEqual(int(http_response.msg['content-length']),
                     len(bytes_returned_by_server))
