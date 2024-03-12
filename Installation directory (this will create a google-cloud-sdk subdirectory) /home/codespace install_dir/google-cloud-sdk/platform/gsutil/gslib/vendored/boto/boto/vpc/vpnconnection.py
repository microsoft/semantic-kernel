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
import boto
from datetime import datetime
from boto.resultset import ResultSet

"""
Represents a VPN Connectionn
"""

from boto.ec2.ec2object import TaggedEC2Object

class VpnConnectionOptions(object):
    """
    Represents VPN connection options

    :ivar static_routes_only: Indicates whether the VPN connection uses static
        routes only.  Static routes must be used for devices that don't support
        BGP.

    """
    def __init__(self, static_routes_only=None):
        self.static_routes_only = static_routes_only

    def __repr__(self):
        return 'VpnConnectionOptions'

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'staticRoutesOnly':
            self.static_routes_only = True if value == 'true' else False
        else:
            setattr(self, name, value)

class VpnStaticRoute(object):
    """
    Represents a static route for a VPN connection.

    :ivar destination_cidr_block: The CIDR block associated with the local
        subnet of the customer data center.
    :ivar source: Indicates how the routes were provided.
    :ivar state: The current state of the static route.
    """
    def __init__(self, destination_cidr_block=None, source=None, state=None):
        self.destination_cidr_block = destination_cidr_block
        self.source = source
        self.available = state

    def __repr__(self):
        return 'VpnStaticRoute: %s' % self.destination_cidr_block

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'destinationCidrBlock':
            self.destination_cidr_block = value
        elif name == 'source':
            self.source = value
        elif name == 'state':
            self.state = value
        else:
            setattr(self, name, value)

class VpnTunnel(object):
    """
    Represents telemetry for a VPN tunnel

    :ivar outside_ip_address: The Internet-routable IP address of the
        virtual private gateway's outside interface.
    :ivar status: The status of the VPN tunnel. Valid values: UP | DOWN
    :ivar last_status_change: The date and time of the last change in status.
    :ivar status_message: If an error occurs, a description of the error.
    :ivar accepted_route_count: The number of accepted routes.
    """
    def __init__(self, outside_ip_address=None, status=None, last_status_change=None,
                 status_message=None, accepted_route_count=None):
        self.outside_ip_address = outside_ip_address
        self.status = status
        self.last_status_change = last_status_change
        self.status_message = status_message
        self.accepted_route_count = accepted_route_count

    def __repr__(self):
        return 'VpnTunnel: %s' % self.outside_ip_address

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'outsideIpAddress':
            self.outside_ip_address = value
        elif name == 'status':
            self.status = value
        elif name == 'lastStatusChange':
            self.last_status_change =  datetime.strptime(value,
                                        '%Y-%m-%dT%H:%M:%S.%fZ')
        elif name == 'statusMessage':
            self.status_message = value
        elif name == 'acceptedRouteCount':
            try:
                value = int(value)
            except ValueError:
                boto.log.warning('Error converting code (%s) to int' % value)
            self.accepted_route_count = value
        else:
            setattr(self, name, value)

class VpnConnection(TaggedEC2Object):
    """
    Represents a VPN Connection

    :ivar id: The ID of the VPN connection.
    :ivar state: The current state of the VPN connection.
        Valid values: pending | available | deleting | deleted
    :ivar customer_gateway_configuration: The configuration information for the
        VPN connection's customer gateway (in the native XML format). This
        element is always present in the
        :class:`boto.vpc.VPCConnection.create_vpn_connection` response;
        however, it's present in the
        :class:`boto.vpc.VPCConnection.get_all_vpn_connections` response only
        if the VPN connection is in the pending or available state.
    :ivar type: The type of VPN connection (ipsec.1).
    :ivar customer_gateway_id: The ID of the customer gateway at your end of
        the VPN connection.
    :ivar vpn_gateway_id: The ID of the virtual private gateway
        at the AWS side of the VPN connection.
    :ivar tunnels: A list of the vpn tunnels (always 2)
    :ivar options: The option set describing the VPN connection.
    :ivar static_routes: A list of static routes associated with a VPN
        connection.

    """
    def __init__(self, connection=None):
        super(VpnConnection, self).__init__(connection)
        self.id = None
        self.state = None
        self.customer_gateway_configuration = None
        self.type = None
        self.customer_gateway_id = None
        self.vpn_gateway_id = None
        self.tunnels = []
        self.options = None
        self.static_routes = []

    def __repr__(self):
        return 'VpnConnection:%s' % self.id

    def startElement(self, name, attrs, connection):
        retval = super(VpnConnection, self).startElement(name, attrs, connection)
        if retval is not None:
            return retval
        if name == 'vgwTelemetry':
            self.tunnels = ResultSet([('item', VpnTunnel)])
            return self.tunnels
        elif name == 'routes':
            self.static_routes = ResultSet([('item', VpnStaticRoute)])
            return self.static_routes
        elif name == 'options':
            self.options = VpnConnectionOptions()
            return self.options
        return None

    def endElement(self, name, value, connection):
        if name == 'vpnConnectionId':
            self.id = value
        elif name == 'state':
            self.state = value
        elif name == 'customerGatewayConfiguration':
            self.customer_gateway_configuration = value
        elif name == 'type':
            self.type = value
        elif name == 'customerGatewayId':
            self.customer_gateway_id = value
        elif name == 'vpnGatewayId':
            self.vpn_gateway_id = value
        else:
            setattr(self, name, value)

    def delete(self, dry_run=False):
        return self.connection.delete_vpn_connection(
            self.id,
            dry_run=dry_run
        )
