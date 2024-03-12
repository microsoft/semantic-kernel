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

"""
Represents an EC2 Availability Zone
"""
from boto.ec2.ec2object import EC2Object


class MessageSet(list):
    """
    A list object that contains messages associated with
    an availability zone.
    """

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'message':
            self.append(value)
        else:
            setattr(self, name, value)


class Zone(EC2Object):
    """
    Represents an Availability Zone.

    :ivar name: The name of the zone.
    :ivar state: The current state of the zone.
    :ivar region_name: The name of the region the zone is associated with.
    :ivar messages: A list of messages related to the zone.
    """

    def __init__(self, connection=None):
        super(Zone, self).__init__(connection)
        self.name = None
        self.state = None
        self.region_name = None
        self.messages = None

    def __repr__(self):
        return 'Zone:%s' % self.name

    def startElement(self, name, attrs, connection):
        if name == 'messageSet':
            self.messages = MessageSet()
            return self.messages
        return None

    def endElement(self, name, value, connection):
        if name == 'zoneName':
            self.name = value
        elif name == 'zoneState':
            self.state = value
        elif name == 'regionName':
            self.region_name = value
        else:
            setattr(self, name, value)
