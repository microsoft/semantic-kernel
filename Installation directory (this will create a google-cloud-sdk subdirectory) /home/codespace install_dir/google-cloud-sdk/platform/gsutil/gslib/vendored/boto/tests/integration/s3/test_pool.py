# Copyright (c) 2011 Brian Beach
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
Some multi-threading tests of boto in a greenlet environment.
"""
from __future__ import print_function

import boto
import time
import uuid

from threading import Thread

def spawn(function, *args, **kwargs):
    """
    Spawns a new thread.  API is the same as
    gevent.greenlet.Greenlet.spawn.
    """
    t = Thread(target = function, args = args, kwargs = kwargs)
    t.start()
    return t

def put_object(bucket, name):
    bucket.new_key(name).set_contents_from_string(name)

def get_object(bucket, name):
    assert bucket.get_key(name).get_contents_as_string().decode('utf-8') == name

def test_close_connections():
    """
    A test that exposes the problem where connections are returned to the
    connection pool (and closed) before the caller reads the response.
    
    I couldn't think of a way to test it without greenlets, so this test
    doesn't run as part of the standard test suite.  That way, no more
    dependencies are added to the test suite.
    """
    
    print("Running test_close_connections")

    # Connect to S3
    s3 = boto.connect_s3()

    # Clean previous tests.
    for b in s3.get_all_buckets():
        if b.name.startswith('test-'):
            for key in b.get_all_keys():
                key.delete()
            b.delete()

    # Make a test bucket
    bucket = s3.create_bucket('test-%d' % int(time.time()))

    # Create 30 threads that each create an object in S3.  The number
    # 30 is chosen because it is larger than the connection pool size
    # (20). 
    names = [str(uuid.uuid4) for _ in range(30)]
    threads = [
        spawn(put_object, bucket, name)
        for name in names
        ]
    for t in threads:
        t.join()

    # Create 30 threads to read the contents of the new objects.  This
    # is where closing the connection early is a problem, because
    # there is a response that needs to be read, and it can't be read
    # if the connection has already been closed.
    threads = [
        spawn(get_object, bucket, name)
        for name in names
        ]
    for t in threads:
        t.join()

# test_reuse_connections needs to read a file that is big enough that
# one read() call on the socket won't read the whole thing.  
BIG_SIZE = 10000

class WriteAndCount(object):

    """
    A file-like object that counts the number of characters written.
    """

    def __init__(self):
        self.size = 0

    def write(self, data):
        self.size += len(data)
        time.sleep(0) # yield to other threads

def read_big_object(s3, bucket, name, count):
    for _ in range(count):
        key = bucket.get_key(name)
        out = WriteAndCount()
        key.get_contents_to_file(out)
        if out.size != BIG_SIZE:
            print(out.size, BIG_SIZE)
        assert out.size == BIG_SIZE
        print("    pool size:", s3._pool.size())

class LittleQuerier(object):

    """
    An object that manages a thread that keeps pulling down small
    objects from S3 and checking the answers until told to stop.
    """

    def __init__(self, bucket, small_names):
        self.running = True
        self.bucket = bucket
        self.small_names = small_names
        self.thread = spawn(self.run)

    def stop(self):
        self.running = False
        self.thread.join()

    def run(self):
        count = 0
        while self.running:
            i = count % 4
            key = self.bucket.get_key(self.small_names[i])
            expected = str(i)
            rh = { 'response-content-type' : 'small/' + str(i) }
            actual = key.get_contents_as_string(response_headers = rh).decode('utf-8')
            if expected != actual:
                print("AHA:", repr(expected), repr(actual))
            assert expected == actual
            count += 1

def test_reuse_connections():
    """
    This test is an attempt to expose problems because of the fact
    that boto returns connections to the connection pool before
    reading the response.  The strategy is to start a couple big reads
    from S3, where it will take time to read the response, and then
    start other requests that will reuse the same connection from the
    pool while the big response is still being read.

    The test passes because of an interesting combination of factors.
    I was expecting that it would fail because two threads would be
    reading the same connection at the same time.  That doesn't happen
    because httplib catches the problem before it happens and raises
    an exception.

    Here's the sequence of events:

       - Thread 1: Send a request to read a big S3 object.
       - Thread 1: Returns connection to pool.
       - Thread 1: Start reading the body if the response.

       - Thread 2: Get the same connection from the pool.
       - Thread 2: Send another request on the same connection.
       - Thread 2: Try to read the response, but
                   HTTPConnection.get_response notices that the
                   previous response isn't done reading yet, and
                   raises a ResponseNotReady exception.
       - Thread 2: _mexe catches the exception, does not return the
                   connection to the pool, gets a new connection, and
                   retries.

       - Thread 1: Finish reading the body of its response.
       
       - Server:   Gets the second request on the connection, and
                   sends a response.  This response is ignored because
                   the connection has been dropped on the client end.

    If you add a print statement in HTTPConnection.get_response at the
    point where it raises ResponseNotReady, and then run this test,
    you can see that it's happening.
    """

    print("Running test_reuse_connections")

    # Connect to S3
    s3 = boto.connect_s3()

    # Make a test bucket
    bucket = s3.create_bucket('test-%d' % int(time.time()))

    # Create some small objects in S3.
    small_names = [str(uuid.uuid4()) for _ in range(4)]
    for (i, name) in enumerate(small_names):
        bucket.new_key(name).set_contents_from_string(str(i))

    # Wait, clean the connection pool, and make sure it's empty.
    print("    waiting for all connections to become stale")
    time.sleep(s3._pool.STALE_DURATION + 1)
    s3._pool.clean()
    assert s3._pool.size() == 0
    print("    pool is empty")
    
    # Create a big object in S3.
    big_name = str(uuid.uuid4())
    contents = "-" * BIG_SIZE
    bucket.new_key(big_name).set_contents_from_string(contents)

    # Start some threads to read it and check that they are reading
    # the correct thing.  Each thread will read the object 40 times.
    threads = [
        spawn(read_big_object, s3, bucket, big_name, 20)
        for _ in range(5)
        ]

    # Do some other things that may (incorrectly) re-use the same
    # connections while the big objects are being read.
    queriers = [
        LittleQuerier(bucket, small_names)
        for _ in range(5)
        ]

    # Clean up.
    for t in threads:
        t.join()
    for q in queriers:
        q.stop()

def main():
    test_close_connections()
    test_reuse_connections()

if __name__ == '__main__':
    main()
