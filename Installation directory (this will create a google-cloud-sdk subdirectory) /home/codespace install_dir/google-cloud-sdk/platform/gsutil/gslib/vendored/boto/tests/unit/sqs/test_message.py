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
from tests.unit import unittest

from boto.sqs.message import MHMessage
from boto.sqs.message import RawMessage
from boto.sqs.message import Message
from boto.sqs.bigmessage import BigMessage
from boto.exception import SQSDecodeError

from nose.plugins.attrib import attr

class TestMHMessage(unittest.TestCase):

    @attr(sqs=True)
    def test_contains(self):
        msg = MHMessage()
        msg.update({'hello': 'world'})
        self.assertTrue('hello' in msg)


class DecodeExceptionRaisingMessage(RawMessage):

    @attr(sqs=True)
    def decode(self, message):
        raise SQSDecodeError('Sample decode error', self)

class TestEncodeMessage(unittest.TestCase):

    @attr(sqs=True)
    def test_message_id_available(self):
        import xml.sax
        from boto.resultset import ResultSet
        from boto.handler import XmlHandler
        sample_value = 'abcdef'
        body = """<?xml version="1.0"?>
            <ReceiveMessageResponse>
              <ReceiveMessageResult>
                <Message>
                  <Body>%s</Body>
                  <ReceiptHandle>%s</ReceiptHandle>
                  <MessageId>%s</MessageId>
                </Message>
              </ReceiveMessageResult>
            </ReceiveMessageResponse>""" % tuple([sample_value] * 3)
        rs = ResultSet([('Message', DecodeExceptionRaisingMessage)])
        h = XmlHandler(rs, None)
        with self.assertRaises(SQSDecodeError) as context:
            xml.sax.parseString(body.encode('utf-8'), h)
        message = context.exception.message
        self.assertEquals(message.id, sample_value)
        self.assertEquals(message.receipt_handle, sample_value)

    @attr(sqs=True)
    def test_encode_bytes_message(self):
        message = Message()
        body = b'\x00\x01\x02\x03\x04\x05'
        message.set_body(body)
        self.assertEqual(message.get_body_encoded(), 'AAECAwQF')

    @attr(sqs=True)
    def test_encode_string_message(self):
        message = Message()
        body = 'hello world'
        message.set_body(body)
        self.assertEqual(message.get_body_encoded(), 'aGVsbG8gd29ybGQ=')


class TestBigMessage(unittest.TestCase):

    @attr(sqs=True)
    def test_s3url_parsing(self):
        msg = BigMessage()
        # Try just a bucket name
        bucket, key = msg._get_bucket_key('s3://foo')
        self.assertEquals(bucket, 'foo')
        self.assertEquals(key, None)
        # Try just a bucket name with trailing "/"
        bucket, key = msg._get_bucket_key('s3://foo/')
        self.assertEquals(bucket, 'foo')
        self.assertEquals(key, None)
        # Try a bucket and a key
        bucket, key = msg._get_bucket_key('s3://foo/bar')
        self.assertEquals(bucket, 'foo')
        self.assertEquals(key, 'bar')
        # Try a bucket and a key with "/"
        bucket, key = msg._get_bucket_key('s3://foo/bar/fie/baz')
        self.assertEquals(bucket, 'foo')
        self.assertEquals(key, 'bar/fie/baz')
        # Try it with no s3:// prefix
        with self.assertRaises(SQSDecodeError) as context:
            bucket, key = msg._get_bucket_key('foo/bar')



if __name__ == '__main__':
    unittest.main()
