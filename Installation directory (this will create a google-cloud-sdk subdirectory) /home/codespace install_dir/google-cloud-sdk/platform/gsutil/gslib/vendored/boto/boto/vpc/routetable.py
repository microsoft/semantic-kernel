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
Represents a Route Table
"""

from boto.ec2.ec2object import TaggedEC2Object
from boto.resultset import ResultSet

class RouteTable(TaggedEC2Object):

    def __init__(self, connection=None):
        super(RouteTable, self).__init__(connection)
        self.id = None
        self.vpc_id = None
        self.routes = []
        self.associations = []

    def __repr__(self):
        return 'RouteTable:%s' % self.id

    def startElement(self, name, attrs, connection):
        result = super(RouteTable, self).startElement(name, attrs, connection)

        if result is not None:
            # Parent found an interested element, just return it
            return result

        if name == 'routeSet':
            self.routes = ResultSet([('item', Route)])
            return self.routes
        elif name == 'associationSet':
            self.associations = ResultSet([('item', RouteAssociation)])
            return self.associations
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'routeTableId':
            self.id = value
        elif name == 'vpcId':
            self.vpc_id = value
        else:
            setattr(self, name, value)

class Route(object):
    def __init__(self, connection=None):
        self.destination_cidr_block = None
        self.gateway_id = None
        self.instance_id = None
        self.interface_id = None
        self.vpc_peering_connection_id = None
        self.state = None
        self.origin = None

    def __repr__(self):
        return 'Route:%s' % self.destination_cidr_block

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'destinationCidrBlock':
            self.destination_cidr_block = value
        elif name == 'gatewayId':
            self.gateway_id = value
        elif name == 'instanceId':
            self.instance_id = value
        elif name == 'networkInterfaceId':
            self.interface_id = value
        elif name == 'vpcPeeringConnectionId':
            self.vpc_peering_connection_id = value
        elif name == 'state':
            self.state = value
        elif name == 'origin':
            self.origin = value

class RouteAssociation(object):
    def __init__(self, connection=None):
        self.id = None
        self.route_table_id = None
        self.subnet_id = None
        self.main = False

    def __repr__(self):
        return 'RouteAssociation:%s' % self.id

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'routeTableAssociationId':
            self.id = value
        elif name == 'routeTableId':
            self.route_table_id = value
        elif name == 'subnetId':
            self.subnet_id = value
        elif name == 'main':
            self.main = value == 'true'
