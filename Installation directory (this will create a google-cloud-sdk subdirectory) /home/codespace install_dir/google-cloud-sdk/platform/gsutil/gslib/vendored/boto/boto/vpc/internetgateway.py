# Copyright (c) 2009-2010 Mitch Garnaat http://garnaat.org/
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
Represents an Internet Gateway
"""

from boto.ec2.ec2object import TaggedEC2Object
from boto.resultset import ResultSet

class InternetGateway(TaggedEC2Object):
    def __init__(self, connection=None):
        super(InternetGateway, self).__init__(connection)
        self.id = None
        self.attachments = []

    def __repr__(self):
        return 'InternetGateway:%s' % self.id

    def startElement(self, name, attrs, connection):
        result = super(InternetGateway, self).startElement(name, attrs, connection)

        if result is not None:
            # Parent found an interested element, just return it
            return result

        if name == 'attachmentSet':
            self.attachments = ResultSet([('item', InternetGatewayAttachment)])
            return self.attachments
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'internetGatewayId':
            self.id = value
        else:
            setattr(self, name, value)

class InternetGatewayAttachment(object):
    def __init__(self, connection=None):
        self.vpc_id = None
        self.state = None

    def __repr__(self):
        return 'InternetGatewayAttachment:%s' % self.vpc_id

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'vpcId':
            self.vpc_id = value
        elif name == 'state':
            self.state = value
