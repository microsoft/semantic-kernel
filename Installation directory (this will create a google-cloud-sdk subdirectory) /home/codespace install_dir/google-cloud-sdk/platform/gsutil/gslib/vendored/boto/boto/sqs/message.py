# Copyright (c) 2006,2007 Mitch Garnaat http://garnaat.org/
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
SQS Message

A Message represents the data stored in an SQS queue.  The rules for what is allowed within an SQS
Message are here:

    http://docs.amazonwebservices.com/AWSSimpleQueueService/2008-01-01/SQSDeveloperGuide/Query_QuerySendMessage.html

So, at it's simplest level a Message just needs to allow a developer to store bytes in it and get the bytes
back out.  However, to allow messages to have richer semantics, the Message class must support the
following interfaces:

The constructor for the Message class must accept a keyword parameter "queue" which is an instance of a
boto Queue object and represents the queue that the message will be stored in.  The default value for
this parameter is None.

The constructor for the Message class must accept a keyword parameter "body" which represents the
content or body of the message.  The format of this parameter will depend on the behavior of the
particular Message subclass.  For example, if the Message subclass provides dictionary-like behavior to the
user the body passed to the constructor should be a dict-like object that can be used to populate
the initial state of the message.

The Message class must provide an encode method that accepts a value of the same type as the body
parameter of the constructor and returns a string of characters that are able to be stored in an
SQS message body (see rules above).

The Message class must provide a decode method that accepts a string of characters that can be
stored (and probably were stored!) in an SQS message and return an object of a type that is consistent
with the "body" parameter accepted on the class constructor.

The Message class must provide a __len__ method that will return the size of the encoded message
that would be stored in SQS based on the current state of the Message object.

The Message class must provide a get_body method that will return the body of the message in the
same format accepted in the constructor of the class.

The Message class must provide a set_body method that accepts a message body in the same format
accepted by the constructor of the class.  This method should alter to the internal state of the
Message object to reflect the state represented in the message body parameter.

The Message class must provide a get_body_encoded method that returns the current body of the message
in the format in which it would be stored in SQS.
"""

import base64

import boto

from boto.compat import StringIO
from boto.compat import six
from boto.sqs.attributes import Attributes
from boto.sqs.messageattributes import MessageAttributes
from boto.exception import SQSDecodeError

class RawMessage(object):
    """
    Base class for SQS messages.  RawMessage does not encode the message
    in any way.  Whatever you store in the body of the message is what
    will be written to SQS and whatever is returned from SQS is stored
    directly into the body of the message.
    """

    def __init__(self, queue=None, body=''):
        self.queue = queue
        self.set_body(body)
        self.id = None
        self.receipt_handle = None
        self.md5 = None
        self.attributes = Attributes(self)
        self.message_attributes = MessageAttributes(self)
        self.md5_message_attributes = None

    def __len__(self):
        return len(self.encode(self._body))

    def startElement(self, name, attrs, connection):
        if name == 'Attribute':
            return self.attributes
        if name == 'MessageAttribute':
            return self.message_attributes
        return None

    def endElement(self, name, value, connection):
        if name == 'Body':
            self.set_body(value)
        elif name == 'MessageId':
            self.id = value
        elif name == 'ReceiptHandle':
            self.receipt_handle = value
        elif name == 'MD5OfBody':
            self.md5 = value
        elif name == 'MD5OfMessageAttributes':
            self.md5_message_attributes = value
        else:
            setattr(self, name, value)

    def endNode(self, connection):
        self.set_body(self.decode(self.get_body()))

    def encode(self, value):
        """Transform body object into serialized byte array format."""
        return value

    def decode(self, value):
        """Transform seralized byte array into any object."""
        return value

    def set_body(self, body):
        """Override the current body for this object, using decoded format."""
        self._body = body

    def get_body(self):
        return self._body

    def get_body_encoded(self):
        """
        This method is really a semi-private method used by the Queue.write
        method when writing the contents of the message to SQS.
        You probably shouldn't need to call this method in the normal course of events.
        """
        return self.encode(self.get_body())

    def delete(self):
        if self.queue:
            return self.queue.delete_message(self)

    def change_visibility(self, visibility_timeout):
        if self.queue:
            self.queue.connection.change_message_visibility(self.queue,
                                                            self.receipt_handle,
                                                            visibility_timeout)

class Message(RawMessage):
    """
    The default Message class used for SQS queues.  This class automatically
    encodes/decodes the message body using Base64 encoding to avoid any
    illegal characters in the message body.  See:

    https://forums.aws.amazon.com/thread.jspa?threadID=13067

    for details on why this is a good idea.  The encode/decode is meant to
    be transparent to the end-user.
    """

    def encode(self, value):
        if not isinstance(value, six.binary_type):
            value = value.encode('utf-8')
        return base64.b64encode(value).decode('utf-8')

    def decode(self, value):
        try:
            value = base64.b64decode(value.encode('utf-8')).decode('utf-8')
        except:
            boto.log.warning('Unable to decode message')
            return value
        return value

class MHMessage(Message):
    """
    The MHMessage class provides a message that provides RFC821-like
    headers like this:

    HeaderName: HeaderValue

    The encoding/decoding of this is handled automatically and after
    the message body has been read, the message instance can be treated
    like a mapping object, i.e. m['HeaderName'] would return 'HeaderValue'.
    """

    def __init__(self, queue=None, body=None, xml_attrs=None):
        if body is None or body == '':
            body = {}
        super(MHMessage, self).__init__(queue, body)

    def decode(self, value):
        try:
            msg = {}
            fp = StringIO(value)
            line = fp.readline()
            while line:
                delim = line.find(':')
                key = line[0:delim]
                value = line[delim+1:].strip()
                msg[key.strip()] = value.strip()
                line = fp.readline()
        except:
            raise SQSDecodeError('Unable to decode message', self)
        return msg

    def encode(self, value):
        s = ''
        for item in value.items():
            s = s + '%s: %s\n' % (item[0], item[1])
        return s

    def __contains__(self, key):
        return key in self._body

    def __getitem__(self, key):
        if key in self._body:
            return self._body[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        self._body[key] = value
        self.set_body(self._body)

    def keys(self):
        return self._body.keys()

    def values(self):
        return self._body.values()

    def items(self):
        return self._body.items()

    def has_key(self, key):
        return key in self._body

    def update(self, d):
        self._body.update(d)
        self.set_body(self._body)

    def get(self, key, default=None):
        return self._body.get(key, default)

class EncodedMHMessage(MHMessage):
    """
    The EncodedMHMessage class provides a message that provides RFC821-like
    headers like this:

    HeaderName: HeaderValue

    This variation encodes/decodes the body of the message in base64 automatically.
    The message instance can be treated like a mapping object,
    i.e. m['HeaderName'] would return 'HeaderValue'.
    """

    def decode(self, value):
        try:
            value = base64.b64decode(value.encode('utf-8')).decode('utf-8')
        except:
            raise SQSDecodeError('Unable to decode message', self)
        return super(EncodedMHMessage, self).decode(value)

    def encode(self, value):
        value = super(EncodedMHMessage, self).encode(value)
        return base64.b64encode(value.encode('utf-8')).decode('utf-8')

