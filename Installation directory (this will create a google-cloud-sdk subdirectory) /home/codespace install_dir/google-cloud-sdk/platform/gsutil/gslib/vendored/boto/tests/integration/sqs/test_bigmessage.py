# Copyright (c) 2006-2010 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
# All rights reserved.
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

"""
Some unit tests for the SQSConnection
"""
import time
from threading import Timer
from tests.unit import unittest

import boto
from boto.compat import StringIO
from boto.sqs.bigmessage import BigMessage
from boto.exception import SQSError


class TestBigMessage(unittest.TestCase):

    sqs = True

    def test_1_basic(self):
        c = boto.connect_sqs()

        # create a queue so we can test BigMessage
        queue_name = 'test%d' % int(time.time())
        timeout = 60
        queue = c.create_queue(queue_name, timeout)
        self.addCleanup(c.delete_queue, queue, True)
        queue.set_message_class(BigMessage)

        # create a bucket with the same name to store the message in
        s3 = boto.connect_s3()
        bucket = s3.create_bucket(queue_name)
        self.addCleanup(s3.delete_bucket, queue_name)
        time.sleep(30)

        # now add a message
        msg_body = 'This is a test of the big message'
        fp = StringIO(msg_body)
        s3_url = 's3://%s' % queue_name
        message = queue.new_message(fp, s3_url=s3_url)

        queue.write(message)
        time.sleep(30)

        s3_object_name = message.s3_url.split('/')[-1]

        # Make sure msg body is in bucket
        self.assertTrue(bucket.lookup(s3_object_name))

        m = queue.read()
        self.assertEqual(m.get_body().decode('utf-8'), msg_body)

        m.delete()
        time.sleep(30)

        # Make sure msg is deleted from bucket
        self.assertIsNone(bucket.lookup(s3_object_name))
