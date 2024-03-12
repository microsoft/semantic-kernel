# Copyright (c) 2013 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.
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

import uuid

import boto
from boto.sqs.message import RawMessage
from boto.exception import SQSDecodeError


class BigMessage(RawMessage):
    """
    The BigMessage class provides large payloads (up to 5GB)
    by storing the payload itself in S3 and then placing a reference
    to the S3 object in the actual SQS message payload.

    To create a BigMessage, you should create a BigMessage object
    and pass in a file-like object as the ``body`` param and also
    pass in the an S3 URL specifying the bucket in which to store
    the message body::

        import boto.sqs
        from boto.sqs.bigmessage import BigMessage

        sqs = boto.sqs.connect_to_region('us-west-2')
        queue = sqs.get_queue('myqueue')
        fp = open('/path/to/bigmessage/data')
        msg = BigMessage(queue, fp, 's3://mybucket')
        queue.write(msg)

    Passing in a fully-qualified S3 URL (e.g. s3://mybucket/foo)
    is interpreted to mean that the body of the message is already
    stored in S3 and the that S3 URL is then used directly with no
    content uploaded by BigMessage.
    """

    def __init__(self, queue=None, body=None, s3_url=None):
        self.s3_url = s3_url
        super(BigMessage, self).__init__(queue, body)

    def _get_bucket_key(self, s3_url):
        bucket_name = key_name = None
        if s3_url:
            if s3_url.startswith('s3://'):
                # We need to split out the bucket from the key (if
                # supplied).  We also have to be aware that someone
                # may provide a trailing '/' character as in:
                # s3://foo/ and we want to handle that.
                s3_components = s3_url[5:].split('/', 1)
                bucket_name = s3_components[0]
                if len(s3_components) > 1:
                    if s3_components[1]:
                        key_name = s3_components[1]
            else:
                msg = 's3_url parameter should start with s3://'
                raise SQSDecodeError(msg, self)
        return bucket_name, key_name

    def encode(self, value):
        """
        :type value: file-like object
        :param value: A file-like object containing the content
            of the message.  The actual content will be stored
            in S3 and a link to the S3 object will be stored in
            the message body.
        """
        bucket_name, key_name = self._get_bucket_key(self.s3_url)
        if bucket_name and key_name:
            return self.s3_url
        key_name = uuid.uuid4()
        s3_conn = boto.connect_s3()
        s3_bucket = s3_conn.get_bucket(bucket_name)
        key = s3_bucket.new_key(key_name)
        key.set_contents_from_file(value)
        self.s3_url = 's3://%s/%s' % (bucket_name, key_name)
        return self.s3_url

    def _get_s3_object(self, s3_url):
        bucket_name, key_name = self._get_bucket_key(s3_url)
        if bucket_name and key_name:
            s3_conn = boto.connect_s3()
            s3_bucket = s3_conn.get_bucket(bucket_name)
            key = s3_bucket.get_key(key_name)
            return key
        else:
            msg = 'Unable to decode S3 URL: %s' % s3_url
            raise SQSDecodeError(msg, self)

    def decode(self, value):
        self.s3_url = value
        key = self._get_s3_object(value)
        return key.get_contents_as_string()

    def delete(self):
        # Delete the object in S3 first, then delete the SQS message
        if self.s3_url:
            key = self._get_s3_object(self.s3_url)
            key.delete()
        super(BigMessage, self).delete()

