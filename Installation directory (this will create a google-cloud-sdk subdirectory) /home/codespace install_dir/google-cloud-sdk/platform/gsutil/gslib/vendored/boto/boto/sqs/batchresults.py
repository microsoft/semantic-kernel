# Copyright (c) 2011 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2011 Eucalyptus Systems, Inc.
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
A set of results returned by SendMessageBatch.
"""

class ResultEntry(dict):
    """
    The result (successful or unsuccessful) of a single
    message within a send_message_batch request.

    In the case of a successful result, this dict-like
    object will contain the following items:

    :ivar id: A string containing the user-supplied ID of the message.
    :ivar message_id: A string containing the SQS ID of the new message.
    :ivar message_md5: A string containing the MD5 hash of the message body.

    In the case of an error, this object will contain the following
    items:

    :ivar id: A string containing the user-supplied ID of the message.
    :ivar sender_fault: A boolean value.
    :ivar error_code: A string containing a short description of the error.
    :ivar error_message: A string containing a description of the error.
    """

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Id':
            self['id'] = value
        elif name == 'MessageId':
            self['message_id'] = value
        elif name == 'MD5OfMessageBody':
            self['message_md5'] = value
        elif name == 'SenderFault':
            self['sender_fault'] = value
        elif name == 'Code':
            self['error_code'] = value
        elif name == 'Message':
            self['error_message'] = value
    
class BatchResults(object):
    """
    A container for the results of a send_message_batch request.

    :ivar results: A list of successful results.  Each item in the
        list will be an instance of :class:`ResultEntry`.

    :ivar errors: A list of unsuccessful results.  Each item in the
        list will be an instance of :class:`ResultEntry`.
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.results = []
        self.errors = []

    def startElement(self, name, attrs, connection):
        if name.endswith('MessageBatchResultEntry'):
            entry = ResultEntry()
            self.results.append(entry)
            return entry
        if name == 'BatchResultErrorEntry':
            entry = ResultEntry()
            self.errors.append(entry)
            return entry
        return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)

        
