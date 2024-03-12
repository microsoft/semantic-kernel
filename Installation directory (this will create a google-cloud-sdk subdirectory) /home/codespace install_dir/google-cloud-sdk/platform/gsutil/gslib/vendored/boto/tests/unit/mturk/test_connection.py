# -*- coding: utf-8 -*-

from tests.unit import AWSMockServiceTestCase

from boto.mturk.connection import MTurkConnection


GET_FILE_UPLOAD_URL = b"""
<GetFileUploadURLResult>
  <Request>
    <IsValid>True</IsValid>
  </Request>
  <FileUploadURL>http://s3.amazonaws.com/myawsbucket/puppy.jpg</FileUploadURL>
</GetFileUploadURLResult>"""


class TestMTurkConnection(AWSMockServiceTestCase):
    connection_class = MTurkConnection

    def setUp(self):
        super(TestMTurkConnection, self).setUp()

    def test_get_file_upload_url_success(self):
        self.set_http_response(status_code=200, body=GET_FILE_UPLOAD_URL)
        rset = self.service_connection.get_file_upload_url('aid', 'qid')
        self.assertEquals(len(rset), 1)
        self.assertEquals(rset[0].FileUploadURL,
                          'http://s3.amazonaws.com/myawsbucket/puppy.jpg')
