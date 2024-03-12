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
Represents a Vpn Gateway
"""

from boto.ec2.ec2object import TaggedEC2Object

class Attachment(object):

    def __init__(self, connection=None):
        self.vpc_id = None
        self.state = None

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'vpcId':
            self.vpc_id = value
        elif name == 'state':
            self.state = value
        else:
            setattr(self, name, value)

class VpnGateway(TaggedEC2Object):

    def __init__(self, connection=None):
        super(VpnGateway, self).__init__(connection)
        self.id = None
        self.type = None
        self.state = None
        self.availability_zone = None
        self.attachments = []

    def __repr__(self):
        return 'VpnGateway:%s' % self.id

    def startElement(self, name, attrs, connection):
        retval = super(VpnGateway, self).startElement(name, attrs, connection)
        if retval is not None:
            return retval
        if name == 'item':
            att = Attachment()
            self.attachments.append(att)
            return att

    def endElement(self, name, value, connection):
        if name == 'vpnGatewayId':
            self.id = value
        elif name == 'type':
            self.type = value
        elif name == 'state':
            self.state = value
        elif name == 'availabilityZone':
            self.availability_zone = value
        elif name == 'attachments':
            pass
        else:
            setattr(self, name, value)

    def attach(self, vpc_id, dry_run=False):
        return self.connection.attach_vpn_gateway(
            self.id,
            vpc_id,
            dry_run=dry_run
        )

