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

from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message
from boto.sqs.message import MHMessage
from boto.exception import SQSError


class SQSConnectionTest(unittest.TestCase):

    sqs = True

    def test_1_basic(self):
        print('--- running SQSConnection tests ---')
        c = SQSConnection()
        rs = c.get_all_queues()
        num_queues = 0
        for q in rs:
            num_queues += 1

        # try illegal name
        try:
            queue = c.create_queue('bad*queue*name')
            self.fail('queue name should have been bad')
        except SQSError:
            pass

        # now create one that should work and should be unique (i.e. a new one)
        queue_name = 'test%d' % int(time.time())
        timeout = 60
        queue_1 = c.create_queue(queue_name, timeout)
        self.addCleanup(c.delete_queue, queue_1, True)
        time.sleep(60)
        rs = c.get_all_queues()
        i = 0
        for q in rs:
            i += 1
        assert i == num_queues + 1
        assert queue_1.count_slow() == 0

        # check the visibility timeout
        t = queue_1.get_timeout()
        assert t == timeout, '%d != %d' % (t, timeout)

        # now try to get queue attributes
        a = q.get_attributes()
        assert 'ApproximateNumberOfMessages' in a
        assert 'VisibilityTimeout' in a
        a = q.get_attributes('ApproximateNumberOfMessages')
        assert 'ApproximateNumberOfMessages' in a
        assert 'VisibilityTimeout' not in a
        a = q.get_attributes('VisibilityTimeout')
        assert 'ApproximateNumberOfMessages' not in a
        assert 'VisibilityTimeout' in a

        # now change the visibility timeout
        timeout = 45
        queue_1.set_timeout(timeout)
        time.sleep(60)
        t = queue_1.get_timeout()
        assert t == timeout, '%d != %d' % (t, timeout)

        # now add a message
        message_body = 'This is a test\n'
        message = queue_1.new_message(message_body)
        queue_1.write(message)
        time.sleep(60)
        assert queue_1.count_slow() == 1
        time.sleep(90)

        # now read the message from the queue with a 10 second timeout
        message = queue_1.read(visibility_timeout=10)
        assert message
        assert message.get_body() == message_body

        # now immediately try another read, shouldn't find anything
        message = queue_1.read()
        assert message == None

        # now wait 30 seconds and try again
        time.sleep(30)
        message = queue_1.read()
        assert message

        # now delete the message
        queue_1.delete_message(message)
        time.sleep(30)
        assert queue_1.count_slow() == 0

        # try a batch write
        num_msgs = 10
        msgs = [(i, 'This is message %d' % i, 0) for i in range(num_msgs)]
        queue_1.write_batch(msgs)

        # try to delete all of the messages using batch delete
        deleted = 0
        while deleted < num_msgs:
            time.sleep(5)
            msgs = queue_1.get_messages(num_msgs)
            if msgs:
                br = queue_1.delete_message_batch(msgs)
                deleted += len(br.results)

        # try a batch write with message attributes
        num_msgs = 10
        attrs = {
            'foo': {
                'data_type': 'String',
                'string_value': 'Hello, World!'
            },
        }
        msgs = [(i, 'This is message %d' % i, 0, attrs) for i in range(num_msgs)]
        queue_1.write_batch(msgs)

        # create another queue so we can test force deletion
        # we will also test MHMessage with this queue
        queue_name = 'test%d' % int(time.time())
        timeout = 60
        queue_2 = c.create_queue(queue_name, timeout)
        self.addCleanup(c.delete_queue, queue_2, True)
        queue_2.set_message_class(MHMessage)
        time.sleep(30)

        # now add a couple of messages
        message = queue_2.new_message()
        message['foo'] = 'bar'
        queue_2.write(message)
        message_body = {'fie': 'baz', 'foo': 'bar'}
        message = queue_2.new_message(body=message_body)
        queue_2.write(message)
        time.sleep(30)

        m = queue_2.read()
        assert m['foo'] == 'bar'

        print('--- tests completed ---')

    def test_sqs_timeout(self):
        c = SQSConnection()
        queue_name = 'test_sqs_timeout_%s' % int(time.time())
        queue = c.create_queue(queue_name)
        self.addCleanup(c.delete_queue, queue, True)
        start = time.time()
        poll_seconds = 2
        response = queue.read(visibility_timeout=None,
                              wait_time_seconds=poll_seconds)
        total_time = time.time() - start
        self.assertTrue(total_time > poll_seconds,
                        "SQS queue did not block for at least %s seconds: %s" %
                        (poll_seconds, total_time))
        self.assertIsNone(response)

        # Now that there's an element in the queue, we should not block for 2
        # seconds.
        c.send_message(queue, 'test message')
        start = time.time()
        poll_seconds = 2
        message = c.receive_message(
            queue, number_messages=1,
            visibility_timeout=None, attributes=None,
            wait_time_seconds=poll_seconds)[0]
        total_time = time.time() - start
        self.assertTrue(total_time < poll_seconds,
                        "SQS queue blocked longer than %s seconds: %s" %
                        (poll_seconds, total_time))
        self.assertEqual(message.get_body(), 'test message')

        attrs = c.get_queue_attributes(queue, 'ReceiveMessageWaitTimeSeconds')
        self.assertEqual(attrs['ReceiveMessageWaitTimeSeconds'], '0')

    def test_sqs_longpoll(self):
        c = SQSConnection()
        queue_name = 'test_sqs_longpoll_%s' % int(time.time())
        queue = c.create_queue(queue_name)
        self.addCleanup(c.delete_queue, queue, True)
        messages = []

        # The basic idea is to spawn a timer thread that will put something
        # on the queue in 5 seconds and verify that our long polling client
        # sees the message after waiting for approximately that long.
        def send_message():
            messages.append(
                queue.write(queue.new_message('this is a test message')))

        t = Timer(5.0, send_message)
        t.start()
        self.addCleanup(t.join)

        start = time.time()
        response = queue.read(wait_time_seconds=10)
        end = time.time()

        t.join()
        self.assertEqual(response.id, messages[0].id)
        self.assertEqual(response.get_body(), messages[0].get_body())
        # The timer thread should send the message in 5 seconds, so
        # we're giving +- 1 second for the total time the queue
        # was blocked on the read call.
        self.assertTrue(4.0 <= (end - start) <= 6.0)

    def test_queue_deletion_affects_full_queues(self):
        conn = SQSConnection()
        initial_count = len(conn.get_all_queues())

        empty = conn.create_queue('empty%d' % int(time.time()))
        full = conn.create_queue('full%d' % int(time.time()))
        time.sleep(60)
        # Make sure they're both around.
        self.assertEqual(len(conn.get_all_queues()), initial_count + 2)

        # Put a message in the full queue.
        m1 = Message()
        m1.set_body('This is a test message.')
        full.write(m1)
        self.assertEqual(full.count(), 1)

        self.assertTrue(conn.delete_queue(empty))
        # Here's the regression for the docs. SQS will delete a queue with
        # messages in it, no ``force_deletion`` needed.
        self.assertTrue(conn.delete_queue(full))
        # Wait long enough for SQS to finally remove the queues.
        time.sleep(90)
        self.assertEqual(len(conn.get_all_queues()), initial_count)

    def test_get_messages_attributes(self):
        conn = SQSConnection()
        current_timestamp = int(time.time())
        test = self.create_temp_queue(conn)
        time.sleep(65)

        # Put a message in the queue.
        self.put_queue_message(test)
        self.assertEqual(test.count(), 1)

        # Check all attributes.
        msgs = test.get_messages(
            num_messages=1,
            attributes='All'
        )
        for msg in msgs:
            self.assertEqual(msg.attributes['ApproximateReceiveCount'], '1')
            first_rec = msg.attributes['ApproximateFirstReceiveTimestamp']
            first_rec = int(first_rec) / 1000
            self.assertTrue(first_rec >= current_timestamp)

        # Put another message in the queue.
        self.put_queue_message(test)
        self.assertEqual(test.count(), 1)

        # Check a specific attribute.
        msgs = test.get_messages(
            num_messages=1,
            attributes='ApproximateReceiveCount'
        )
        for msg in msgs:
            self.assertEqual(msg.attributes['ApproximateReceiveCount'], '1')
            with self.assertRaises(KeyError):
                msg.attributes['ApproximateFirstReceiveTimestamp']

    def test_queue_purge(self):
        conn = SQSConnection()
        test = self.create_temp_queue(conn)
        time.sleep(65)

        # Put some messages in the queue.
        for x in range(0, 4):
            self.put_queue_message(test)
        self.assertEqual(test.count(), 4)

        # Now purge the queue
        conn.purge_queue(test)

        # Now assert queue count is 0
        self.assertEqual(test.count(), 0)

    def create_temp_queue(self, conn):
        current_timestamp = int(time.time())
        queue_name = 'test%d' % int(time.time())
        test = conn.create_queue(queue_name)
        self.addCleanup(conn.delete_queue, test)

        return test

    def put_queue_message(self, queue):
        m1 = Message()
        m1.set_body('This is a test message.')
        queue.write(m1)
