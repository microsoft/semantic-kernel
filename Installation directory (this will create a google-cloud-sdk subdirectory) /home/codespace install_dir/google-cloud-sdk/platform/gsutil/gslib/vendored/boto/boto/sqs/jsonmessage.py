# Copyright (c) 2006-2008 Mitch Garnaat http://garnaat.org/
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
import base64

from boto.sqs.message import MHMessage
from boto.exception import SQSDecodeError
from boto.compat import json


class JSONMessage(MHMessage):
    """
    Acts like a dictionary but encodes it's data as a Base64 encoded JSON payload.
    """

    def decode(self, value):
        try:
            value = base64.b64decode(value.encode('utf-8')).decode('utf-8')
            value = json.loads(value)
        except:
            raise SQSDecodeError('Unable to decode message', self)
        return value

    def encode(self, value):
        value = json.dumps(value)
        return base64.b64encode(value.encode('utf-8')).decode('utf-8')
