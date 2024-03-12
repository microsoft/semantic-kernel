# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
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
Represents an SQS Queue
"""
from boto.compat import urllib
from boto.sqs.message import Message


class Queue(object):

    def __init__(self, connection=None, url=None, message_class=Message):
        self.connection = connection
        self.url = url
        self.message_class = message_class
        self.visibility_timeout = None

    def __repr__(self):
        return 'Queue(%s)' % self.url

    def _id(self):
        if self.url:
            val = urllib.parse.urlparse(self.url)[2]
        else:
            val = self.url
        return val
    id = property(_id)

    def _name(self):
        if self.url:
            val = urllib.parse.urlparse(self.url)[2].split('/')[2]
        else:
            val = self.url
        return  val
    name = property(_name)

    def _arn(self):
        parts = self.id.split('/')
        if self.connection.region.name == 'cn-north-1':
            partition = 'aws-cn'
        else:
            partition = 'aws'
        return 'arn:%s:sqs:%s:%s:%s' % (
            partition, self.connection.region.name, parts[1], parts[2])
    arn = property(_arn)

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'QueueUrl':
            self.url = value
        elif name == 'VisibilityTimeout':
            self.visibility_timeout = int(value)
        else:
            setattr(self, name, value)

    def set_message_class(self, message_class):
        """
        Set the message class that should be used when instantiating
        messages read from the queue.  By default, the class
        :class:`boto.sqs.message.Message` is used but this can be overriden
        with any class that behaves like a message.

        :type message_class: Message-like class
        :param message_class:  The new Message class
        """
        self.message_class = message_class

    def get_attributes(self, attributes='All'):
        """
        Retrieves attributes about this queue object and returns
        them in an Attribute instance (subclass of a Dictionary).

        :type attributes: string
        :param attributes: String containing one of:
                           ApproximateNumberOfMessages,
                           ApproximateNumberOfMessagesNotVisible,
                           VisibilityTimeout,
                           CreatedTimestamp,
                           LastModifiedTimestamp,
                           Policy
                           ReceiveMessageWaitTimeSeconds
        :rtype: Attribute object
        :return: An Attribute object which is a mapping type holding the
                 requested name/value pairs
        """
        return self.connection.get_queue_attributes(self, attributes)

    def set_attribute(self, attribute, value):
        """
        Set a new value for an attribute of the Queue.

        :type attribute: String
        :param attribute: The name of the attribute you want to set.

        :param value: The new value for the attribute must be:


            * For `DelaySeconds` the value must be an integer number of
            seconds from 0 to 900 (15 minutes).
                >>> queue.set_attribute('DelaySeconds', 900)

            * For `MaximumMessageSize` the value must be an integer number of
            bytes from 1024 (1 KiB) to 262144 (256 KiB).
                >>> queue.set_attribute('MaximumMessageSize', 262144)

            * For `MessageRetentionPeriod` the value must be an integer number of
            seconds from 60 (1 minute) to 1209600 (14 days).
                >>> queue.set_attribute('MessageRetentionPeriod', 1209600)

            * For `Policy` the value must be an string that contains JSON formatted
            parameters and values.
                >>> queue.set_attribute('Policy', json.dumps({
                ...     'Version': '2008-10-17',
                ...     'Id': '/123456789012/testQueue/SQSDefaultPolicy',
                ...     'Statement': [
                ...        {
                ...            'Sid': 'Queue1ReceiveMessage',
                ...            'Effect': 'Allow',
                ...            'Principal': {
                ...                'AWS': '*'
                ...            },
                ...            'Action': 'SQS:ReceiveMessage',
                ...            'Resource': 'arn:aws:aws:sqs:us-east-1:123456789012:testQueue'
                ...        }
                ...    ]
                ... }))

            * For `ReceiveMessageWaitTimeSeconds` the value must be an integer number of
            seconds from 0 to 20.
                >>> queue.set_attribute('ReceiveMessageWaitTimeSeconds', 20)

            * For `VisibilityTimeout` the value must be an integer number of
            seconds from 0 to 43200 (12 hours).
                >>> queue.set_attribute('VisibilityTimeout', 43200)

            * For `RedrivePolicy` the value must be an string that contains JSON formatted
            parameters and values. You can set maxReceiveCount to a value between 1 and 1000.
            The deadLetterTargetArn value is the Amazon Resource Name (ARN) of the queue that
            will receive the dead letter messages.
                >>> queue.set_attribute('RedrivePolicy', json.dumps({
                ...    'maxReceiveCount': 5,
                ...    'deadLetterTargetArn': "arn:aws:aws:sqs:us-east-1:123456789012:testDeadLetterQueue"
                ... }))

        :rtype: bool
        :return: True if successful, otherwise False.
        """
        return self.connection.set_queue_attribute(self, attribute, value)

    def get_timeout(self):
        """
        Get the visibility timeout for the queue.

        :rtype: int
        :return: The number of seconds as an integer.
        """
        a = self.get_attributes('VisibilityTimeout')
        return int(a['VisibilityTimeout'])

    def set_timeout(self, visibility_timeout):
        """
        Set the visibility timeout for the queue.

        :type visibility_timeout: int
        :param visibility_timeout: The desired timeout in seconds
        """
        retval = self.set_attribute('VisibilityTimeout', visibility_timeout)
        if retval:
            self.visibility_timeout = visibility_timeout
        return retval

    def add_permission(self, label, aws_account_id, action_name):
        """
        Add a permission to a queue.

        :type label: str or unicode
        :param label: A unique identification of the permission you are setting.
            Maximum of 80 characters ``[0-9a-zA-Z_-]``
            Example, AliceSendMessage

        :type aws_account_id: str or unicode
        :param principal_id: The AWS account number of the principal who
            will be given permission.  The principal must have an AWS account,
            but does not need to be signed up for Amazon SQS. For information
            about locating the AWS account identification.

        :type action_name: str or unicode
        :param action_name: The action.  Valid choices are:
            SendMessage|ReceiveMessage|DeleteMessage|
            ChangeMessageVisibility|GetQueueAttributes|*

        :rtype: bool
        :return: True if successful, False otherwise.

        """
        return self.connection.add_permission(self, label, aws_account_id,
                                              action_name)

    def remove_permission(self, label):
        """
        Remove a permission from a queue.

        :type label: str or unicode
        :param label: The unique label associated with the permission
            being removed.

        :rtype: bool
        :return: True if successful, False otherwise.
        """
        return self.connection.remove_permission(self, label)

    def read(self, visibility_timeout=None, wait_time_seconds=None,
             message_attributes=None):
        """
        Read a single message from the queue.

        :type visibility_timeout: int
        :param visibility_timeout: The timeout for this message in seconds

        :type wait_time_seconds: int
        :param wait_time_seconds: The duration (in seconds) for which the call
            will wait for a message to arrive in the queue before returning.
            If a message is available, the call will return sooner than
            wait_time_seconds.

        :type message_attributes: list
        :param message_attributes: The name(s) of additional message
            attributes to return. The default is to return no additional
            message attributes. Use ``['All']`` or ``['.*']`` to return all.

        :rtype: :class:`boto.sqs.message.Message`
        :return: A single message or None if queue is empty
        """
        rs = self.get_messages(1, visibility_timeout,
                               wait_time_seconds=wait_time_seconds,
                               message_attributes=message_attributes)
        if len(rs) == 1:
            return rs[0]
        else:
            return None

    def write(self, message, delay_seconds=None):
        """
        Add a single message to the queue.

        :type message: Message
        :param message: The message to be written to the queue

        :rtype: :class:`boto.sqs.message.Message`
        :return: The :class:`boto.sqs.message.Message` object that was written.
        """
        new_msg = self.connection.send_message(self,
            message.get_body_encoded(), delay_seconds=delay_seconds,
            message_attributes=message.message_attributes)
        message.id = new_msg.id
        message.md5 = new_msg.md5
        return message

    def write_batch(self, messages):
        """
        Delivers up to 10 messages in a single request.

        :type messages: List of lists.
        :param messages: A list of lists or tuples.  Each inner
            tuple represents a single message to be written
            and consists of and ID (string) that must be unique
            within the list of messages, the message body itself
            which can be a maximum of 64K in length, an
            integer which represents the delay time (in seconds)
            for the message (0-900) before the message will
            be delivered to the queue, and an optional dict of
            message attributes like those passed to ``send_message``
            in the connection class.
        """
        return self.connection.send_message_batch(self, messages)

    def new_message(self, body='', **kwargs):
        """
        Create new message of appropriate class.

        :type body: message body
        :param body: The body of the newly created message (optional).

        :rtype: :class:`boto.sqs.message.Message`
        :return: A new Message object
        """
        m = self.message_class(self, body, **kwargs)
        m.queue = self
        return m

    # get a variable number of messages, returns a list of messages
    def get_messages(self, num_messages=1, visibility_timeout=None,
                     attributes=None, wait_time_seconds=None,
                     message_attributes=None):
        """
        Get a variable number of messages.

        :type num_messages: int
        :param num_messages: The maximum number of messages to read from
            the queue.

        :type visibility_timeout: int
        :param visibility_timeout: The VisibilityTimeout for the messages read.

        :type attributes: str
        :param attributes: The name of additional attribute to return
            with response or All if you want all attributes.  The
            default is to return no additional attributes.  Valid
            values: All SenderId SentTimestamp ApproximateReceiveCount
            ApproximateFirstReceiveTimestamp

        :type wait_time_seconds: int
        :param wait_time_seconds: The duration (in seconds) for which the call
            will wait for a message to arrive in the queue before returning.
            If a message is available, the call will return sooner than
            wait_time_seconds.

        :type message_attributes: list
        :param message_attributes: The name(s) of additional message
            attributes to return. The default is to return no additional
            message attributes. Use ``['All']`` or ``['.*']`` to return all.

        :rtype: list
        :return: A list of :class:`boto.sqs.message.Message` objects.
        """
        return self.connection.receive_message(
            self, number_messages=num_messages,
            visibility_timeout=visibility_timeout, attributes=attributes,
            wait_time_seconds=wait_time_seconds,
            message_attributes=message_attributes)

    def delete_message(self, message):
        """
        Delete a message from the queue.

        :type message: :class:`boto.sqs.message.Message`
        :param message: The :class:`boto.sqs.message.Message` object to delete.

        :rtype: bool
        :return: True if successful, False otherwise
        """
        return self.connection.delete_message(self, message)

    def delete_message_batch(self, messages):
        """
        Deletes a list of messages in a single request.

        :type messages: List of :class:`boto.sqs.message.Message` objects.
        :param messages: A list of message objects.
        """
        return self.connection.delete_message_batch(self, messages)

    def change_message_visibility_batch(self, messages):
        """
        A batch version of change_message_visibility that can act
        on up to 10 messages at a time.

        :type messages: List of tuples.
        :param messages: A list of tuples where each tuple consists
            of a :class:`boto.sqs.message.Message` object and an integer
            that represents the new visibility timeout for that message.
        """
        return self.connection.change_message_visibility_batch(self, messages)

    def delete(self):
        """
        Delete the queue.
        """
        return self.connection.delete_queue(self)

    def purge(self):
        """
        Purge all messages in the queue.
        """
        return self.connection.purge_queue(self)

    def clear(self, page_size=10, vtimeout=10):
        """Deprecated utility function to remove all messages from a queue"""
        return self.purge()

    def count(self, page_size=10, vtimeout=10):
        """
        Utility function to count the number of messages in a queue.
        Note: This function now calls GetQueueAttributes to obtain
        an 'approximate' count of the number of messages in a queue.
        """
        a = self.get_attributes('ApproximateNumberOfMessages')
        return int(a['ApproximateNumberOfMessages'])

    def count_slow(self, page_size=10, vtimeout=10):
        """
        Deprecated.  This is the old 'count' method that actually counts
        the messages by reading them all.  This gives an accurate count but
        is very slow for queues with non-trivial number of messasges.
        Instead, use get_attributes('ApproximateNumberOfMessages') to take
        advantage of the new SQS capability.  This is retained only for
        the unit tests.
        """
        n = 0
        l = self.get_messages(page_size, vtimeout)
        while l:
            for m in l:
                n += 1
            l = self.get_messages(page_size, vtimeout)
        return n

    def dump(self, file_name, page_size=10, vtimeout=10, sep='\n'):
        """Utility function to dump the messages in a queue to a file
        NOTE: Page size must be < 10 else SQS errors"""
        fp = open(file_name, 'wb')
        n = 0
        l = self.get_messages(page_size, vtimeout)
        while l:
            for m in l:
                fp.write(m.get_body())
                if sep:
                    fp.write(sep)
                n += 1
            l = self.get_messages(page_size, vtimeout)
        fp.close()
        return n

    def save_to_file(self, fp, sep='\n'):
        """
        Read all messages from the queue and persist them to file-like object.
        Messages are written to the file and the 'sep' string is written
        in between messages.  Messages are deleted from the queue after
        being written to the file.
        Returns the number of messages saved.
        """
        n = 0
        m = self.read()
        while m:
            n += 1
            fp.write(m.get_body())
            if sep:
                fp.write(sep)
            self.delete_message(m)
            m = self.read()
        return n

    def save_to_filename(self, file_name, sep='\n'):
        """
        Read all messages from the queue and persist them to local file.
        Messages are written to the file and the 'sep' string is written
        in between messages.  Messages are deleted from the queue after
        being written to the file.
        Returns the number of messages saved.
        """
        fp = open(file_name, 'wb')
        n = self.save_to_file(fp, sep)
        fp.close()
        return n

    # for backwards compatibility
    save = save_to_filename

    def save_to_s3(self, bucket):
        """
        Read all messages from the queue and persist them to S3.
        Messages are stored in the S3 bucket using a naming scheme of::

            <queue_id>/<message_id>

        Messages are deleted from the queue after being saved to S3.
        Returns the number of messages saved.
        """
        n = 0
        m = self.read()
        while m:
            n += 1
            key = bucket.new_key('%s/%s' % (self.id, m.id))
            key.set_contents_from_string(m.get_body())
            self.delete_message(m)
            m = self.read()
        return n

    def load_from_s3(self, bucket, prefix=None):
        """
        Load messages previously saved to S3.
        """
        n = 0
        if prefix:
            prefix = '%s/' % prefix
        else:
            prefix = '%s/' % self.id[1:]
        rs = bucket.list(prefix=prefix)
        for key in rs:
            n += 1
            m = self.new_message(key.get_contents_as_string())
            self.write(m)
        return n

    def load_from_file(self, fp, sep='\n'):
        """Utility function to load messages from a file-like object to a queue"""
        n = 0
        body = ''
        l = fp.readline()
        while l:
            if l == sep:
                m = Message(self, body)
                self.write(m)
                n += 1
                print('writing message %d' % n)
                body = ''
            else:
                body = body + l
            l = fp.readline()
        return n

    def load_from_filename(self, file_name, sep='\n'):
        """Utility function to load messages from a local filename to a queue"""
        fp = open(file_name, 'rb')
        n = self.load_from_file(fp, sep)
        fp.close()
        return n

    # for backward compatibility
    load = load_from_filename

