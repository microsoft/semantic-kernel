# Copyright (c) 2006,2007 Chris Moyer
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
This module was contributed by Chris Moyer.  It provides a subclass of the
SQS Message class that supports YAML as the body of the message.

This module requires the yaml module.
"""
from boto.sqs.message import Message
import yaml


class YAMLMessage(Message):
    """
    The YAMLMessage class provides a YAML compatible message. Encoding and
    decoding are handled automaticaly.

    Access this message data like such:

    m.data = [ 1, 2, 3]
    m.data[0] # Returns 1

    This depends on the PyYAML package
    """

    def __init__(self, queue=None, body='', xml_attrs=None):
        self.data = None
        super(YAMLMessage, self).__init__(queue, body)

    def set_body(self, body):
        self.data = yaml.safe_load(body)

    def get_body(self):
        return yaml.dump(self.data)
