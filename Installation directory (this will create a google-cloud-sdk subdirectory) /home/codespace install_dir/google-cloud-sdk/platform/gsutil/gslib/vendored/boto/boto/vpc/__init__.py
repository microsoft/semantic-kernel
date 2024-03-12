# Copyright (c) 2009 Mitch Garnaat http://garnaat.org/
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
Represents a connection to the EC2 service.
"""

from boto.ec2.connection import EC2Connection
from boto.resultset import ResultSet
from boto.vpc.vpc import VPC
from boto.vpc.customergateway import CustomerGateway
from boto.vpc.networkacl import NetworkAcl
from boto.vpc.routetable import RouteTable
from boto.vpc.internetgateway import InternetGateway
from boto.vpc.vpngateway import VpnGateway, Attachment
from boto.vpc.dhcpoptions import DhcpOptions
from boto.vpc.subnet import Subnet
from boto.vpc.vpnconnection import VpnConnection
from boto.vpc.vpc_peering_connection import VpcPeeringConnection
from boto.ec2 import RegionData
from boto.regioninfo import RegionInfo, get_regions
from boto.regioninfo import connect


def regions(**kw_params):
    """
    Get all available regions for the EC2 service.
    You may pass any of the arguments accepted by the VPCConnection
    object's constructor as keyword arguments and they will be
    passed along to the VPCConnection object.

    :rtype: list
    :return: A list of :class:`boto.ec2.regioninfo.RegionInfo`
    """
    return get_regions('ec2', connection_cls=VPCConnection)


def connect_to_region(region_name, **kw_params):
    """
    Given a valid region name, return a
    :class:`boto.vpc.VPCConnection`.
    Any additional parameters after the region_name are passed on to
    the connect method of the region object.

    :type: str
    :param region_name: The name of the region to connect to.

    :rtype: :class:`boto.vpc.VPCConnection` or ``None``
    :return: A connection to the given region, or None if an invalid region
             name is given
    """
    return connect('ec2', region_name, connection_cls=VPCConnection,
                   **kw_params)


class VPCConnection(EC2Connection):

    # VPC methods

    def get_all_vpcs(self, vpc_ids=None, filters=None, dry_run=False):
        """
        Retrieve information about your VPCs.  You can filter results to
        return information only about those VPCs that match your search
        parameters.  Otherwise, all VPCs associated with your account
        are returned.

        :type vpc_ids: list
        :param vpc_ids: A list of strings with the desired VPC ID's

        :type filters: list of tuples or dict
        :param filters: A list of tuples or dict containing filters.  Each tuple
            or dict item consists of a filter key and a filter value.
            Possible filter keys are:

            * *state* - a list of states of the VPC (pending or available)
            * *cidrBlock* - a list CIDR blocks of the VPC
            * *dhcpOptionsId* - a list of IDs of a set of DHCP options

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.vpc.vpc.VPC`
        """
        params = {}
        if vpc_ids:
            self.build_list_params(params, vpc_ids, 'VpcId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeVpcs', params, [('item', VPC)])

    def create_vpc(self, cidr_block, instance_tenancy=None, dry_run=False):
        """
        Create a new Virtual Private Cloud.

        :type cidr_block: str
        :param cidr_block: A valid CIDR block

        :type instance_tenancy: str
        :param instance_tenancy: The supported tenancy options for instances
            launched into the VPC. Valid values are 'default' and 'dedicated'.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: The newly created VPC
        :return: A :class:`boto.vpc.vpc.VPC` object
        """
        params = {'CidrBlock': cidr_block}
        if instance_tenancy:
            params['InstanceTenancy'] = instance_tenancy
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateVpc', params, VPC)

    def delete_vpc(self, vpc_id, dry_run=False):
        """
        Delete a Virtual Private Cloud.

        :type vpc_id: str
        :param vpc_id: The ID of the vpc to be deleted.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'VpcId': vpc_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteVpc', params)

    def modify_vpc_attribute(self, vpc_id,
                             enable_dns_support=None,
                             enable_dns_hostnames=None, dry_run=False):
        """
        Modifies the specified attribute of the specified VPC.
        You can only modify one attribute at a time.

        :type vpc_id: str
        :param vpc_id: The ID of the vpc to be deleted.

        :type enable_dns_support: bool
        :param enable_dns_support: Specifies whether the DNS server
            provided by Amazon is enabled for the VPC.

        :type enable_dns_hostnames: bool
        :param enable_dns_hostnames: Specifies whether DNS hostnames are
            provided for the instances launched in this VPC. You can only
            set this attribute to ``true`` if EnableDnsSupport
            is also ``true``.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'VpcId': vpc_id}
        if enable_dns_support is not None:
            if enable_dns_support:
                params['EnableDnsSupport.Value'] = 'true'
            else:
                params['EnableDnsSupport.Value'] = 'false'
        if enable_dns_hostnames is not None:
            if enable_dns_hostnames:
                params['EnableDnsHostnames.Value'] = 'true'
            else:
                params['EnableDnsHostnames.Value'] = 'false'
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('ModifyVpcAttribute', params)

    # Route Tables

    def get_all_route_tables(self, route_table_ids=None, filters=None,
                             dry_run=False):
        """
        Retrieve information about your routing tables. You can filter results
        to return information only about those route tables that match your
        search parameters. Otherwise, all route tables associated with your
        account are returned.

        :type route_table_ids: list
        :param route_table_ids: A list of strings with the desired route table
                                IDs.

        :type filters: list of tuples or dict
        :param filters: A list of tuples or dict containing filters. Each tuple
                        or dict item consists of a filter key and a filter value.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.vpc.routetable.RouteTable`
        """
        params = {}
        if route_table_ids:
            self.build_list_params(params, route_table_ids, "RouteTableId")
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeRouteTables', params,
                             [('item', RouteTable)])

    def associate_route_table(self, route_table_id, subnet_id, dry_run=False):
        """
        Associates a route table with a specific subnet.

        :type route_table_id: str
        :param route_table_id: The ID of the route table to associate.

        :type subnet_id: str
        :param subnet_id: The ID of the subnet to associate with.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: str
        :return: The ID of the association created
        """
        params = {
            'RouteTableId': route_table_id,
            'SubnetId': subnet_id
        }
        if dry_run:
            params['DryRun'] = 'true'
        result = self.get_object('AssociateRouteTable', params, ResultSet)
        return result.associationId

    def disassociate_route_table(self, association_id, dry_run=False):
        """
        Removes an association from a route table. This will cause all subnets
        that would've used this association to now use the main routing
        association instead.

        :type association_id: str
        :param association_id: The ID of the association to disassociate.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'AssociationId': association_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DisassociateRouteTable', params)

    def create_route_table(self, vpc_id, dry_run=False):
        """
        Creates a new route table.

        :type vpc_id: str
        :param vpc_id: The VPC ID to associate this route table with.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: The newly created route table
        :return: A :class:`boto.vpc.routetable.RouteTable` object
        """
        params = {'VpcId': vpc_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateRouteTable', params, RouteTable)

    def delete_route_table(self, route_table_id, dry_run=False):
        """
        Delete a route table.

        :type route_table_id: str
        :param route_table_id: The ID of the route table to delete.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'RouteTableId': route_table_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteRouteTable', params)

    def _replace_route_table_association(self, association_id,
                                        route_table_id, dry_run=False):
        """
        Helper function for replace_route_table_association and
        replace_route_table_association_with_assoc. Should not be used directly.

        :type association_id: str
        :param association_id: The ID of the existing association to replace.

        :type route_table_id: str
        :param route_table_id: The route table to ID to be used in the
            association.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: ResultSet
        :return: ResultSet of Amazon resposne
        """
        params = {
            'AssociationId': association_id,
            'RouteTableId': route_table_id
        }
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('ReplaceRouteTableAssociation', params,
                               ResultSet)

    def replace_route_table_assocation(self, association_id,
                                       route_table_id, dry_run=False):
        """
        Replaces a route association with a new route table.  This can be
        used to replace the 'main' route table by using the main route
        table association instead of the more common subnet type
        association.

        NOTE: It may be better to use replace_route_table_association_with_assoc
        instead of this function; this function does not return the new
        association ID. This function is retained for backwards compatibility.


        :type association_id: str
        :param association_id: The ID of the existing association to replace.

        :type route_table_id: str
        :param route_table_id: The route table to ID to be used in the
            association.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        return self._replace_route_table_association(
            association_id, route_table_id, dry_run=dry_run).status

    def replace_route_table_association_with_assoc(self, association_id,
                                                   route_table_id,
                                                   dry_run=False):
        """
        Replaces a route association with a new route table.  This can be
        used to replace the 'main' route table by using the main route
        table association instead of the more common subnet type
        association. Returns the new association ID.

        :type association_id: str
        :param association_id: The ID of the existing association to replace.

        :type route_table_id: str
        :param route_table_id: The route table to ID to be used in the
            association.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: str
        :return: New association ID
        """
        return self._replace_route_table_association(
            association_id, route_table_id, dry_run=dry_run).newAssociationId

    def create_route(self, route_table_id, destination_cidr_block,
                     gateway_id=None, instance_id=None, interface_id=None,
                     vpc_peering_connection_id=None,
                     dry_run=False):
        """
        Creates a new route in the route table within a VPC. The route's target
        can be either a gateway attached to the VPC or a NAT instance in the
        VPC.

        :type route_table_id: str
        :param route_table_id: The ID of the route table for the route.

        :type destination_cidr_block: str
        :param destination_cidr_block: The CIDR address block used for the
                                       destination match.

        :type gateway_id: str
        :param gateway_id: The ID of the gateway attached to your VPC.

        :type instance_id: str
        :param instance_id: The ID of a NAT instance in your VPC.

        :type interface_id: str
        :param interface_id: Allows routing to network interface attachments.

        :type vpc_peering_connection_id: str
        :param vpc_peering_connection_id: Allows routing to VPC peering
                                          connection.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {
            'RouteTableId': route_table_id,
            'DestinationCidrBlock': destination_cidr_block
        }

        if gateway_id is not None:
            params['GatewayId'] = gateway_id
        elif instance_id is not None:
            params['InstanceId'] = instance_id
        elif interface_id is not None:
            params['NetworkInterfaceId'] = interface_id
        elif vpc_peering_connection_id is not None:
            params['VpcPeeringConnectionId'] = vpc_peering_connection_id
        if dry_run:
            params['DryRun'] = 'true'

        return self.get_status('CreateRoute', params)

    def replace_route(self, route_table_id, destination_cidr_block,
                      gateway_id=None, instance_id=None, interface_id=None,
                      vpc_peering_connection_id=None,
                      dry_run=False):
        """
        Replaces an existing route within a route table in a VPC.

        :type route_table_id: str
        :param route_table_id: The ID of the route table for the route.

        :type destination_cidr_block: str
        :param destination_cidr_block: The CIDR address block used for the
                                       destination match.

        :type gateway_id: str
        :param gateway_id: The ID of the gateway attached to your VPC.

        :type instance_id: str
        :param instance_id: The ID of a NAT instance in your VPC.

        :type interface_id: str
        :param interface_id: Allows routing to network interface attachments.

        :type vpc_peering_connection_id: str
        :param vpc_peering_connection_id: Allows routing to VPC peering
                                          connection.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {
            'RouteTableId': route_table_id,
            'DestinationCidrBlock': destination_cidr_block
        }

        if gateway_id is not None:
            params['GatewayId'] = gateway_id
        elif instance_id is not None:
            params['InstanceId'] = instance_id
        elif interface_id is not None:
            params['NetworkInterfaceId'] = interface_id
        elif vpc_peering_connection_id is not None:
            params['VpcPeeringConnectionId'] = vpc_peering_connection_id
        if dry_run:
            params['DryRun'] = 'true'

        return self.get_status('ReplaceRoute', params)

    def delete_route(self, route_table_id, destination_cidr_block,
                     dry_run=False):
        """
        Deletes a route from a route table within a VPC.

        :type route_table_id: str
        :param route_table_id: The ID of the route table with the route.

        :type destination_cidr_block: str
        :param destination_cidr_block: The CIDR address block used for
                                       destination match.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {
            'RouteTableId': route_table_id,
            'DestinationCidrBlock': destination_cidr_block
        }
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteRoute', params)

    #Network ACLs

    def get_all_network_acls(self, network_acl_ids=None, filters=None):
        """
        Retrieve information about your network acls. You can filter results
        to return information only about those network acls that match your
        search parameters. Otherwise, all network acls associated with your
        account are returned.

        :type network_acl_ids: list
        :param network_acl_ids: A list of strings with the desired network ACL
                                IDs.

        :type filters: list of tuples or dict
        :param filters: A list of tuples or dict containing filters. Each tuple
                        or dict item consists of a filter key and a filter value.

        :rtype: list
        :return: A list of :class:`boto.vpc.networkacl.NetworkAcl`
        """
        params = {}
        if network_acl_ids:
            self.build_list_params(params, network_acl_ids, "NetworkAclId")
        if filters:
            self.build_filter_params(params, filters)
        return self.get_list('DescribeNetworkAcls', params,
                             [('item', NetworkAcl)])

    def associate_network_acl(self, network_acl_id, subnet_id):
        """
        Associates a network acl with a specific subnet.

        :type network_acl_id: str
        :param network_acl_id: The ID of the network ACL to associate.

        :type subnet_id: str
        :param subnet_id: The ID of the subnet to associate with.

        :rtype: str
        :return: The ID of the association created
        """

        acl = self.get_all_network_acls(filters=[('association.subnet-id', subnet_id)])[0]
        association = [ association for association in acl.associations if association.subnet_id == subnet_id ][0]

        params = {
            'AssociationId': association.id,
            'NetworkAclId': network_acl_id
        }

        result = self.get_object('ReplaceNetworkAclAssociation', params, ResultSet)
        return result.newAssociationId

    def disassociate_network_acl(self, subnet_id, vpc_id=None):
        """
        Figures out what the default ACL is for the VPC, and associates
        current network ACL with the default.

        :type subnet_id: str
        :param subnet_id: The ID of the subnet to which the ACL belongs.

        :type vpc_id: str
        :param vpc_id: The ID of the VPC to which the ACL/subnet belongs. Queries EC2 if omitted.

        :rtype: str
        :return: The ID of the association created
        """
        if not vpc_id:
            vpc_id = self.get_all_subnets([subnet_id])[0].vpc_id
        acls = self.get_all_network_acls(filters=[('vpc-id', vpc_id), ('default', 'true')])
        default_acl_id = acls[0].id

        return self.associate_network_acl(default_acl_id, subnet_id)

    def create_network_acl(self, vpc_id):
        """
        Creates a new network ACL.

        :type vpc_id: str
        :param vpc_id: The VPC ID to associate this network ACL with.

        :rtype: The newly created network ACL
        :return: A :class:`boto.vpc.networkacl.NetworkAcl` object
        """
        params = {'VpcId': vpc_id}
        return self.get_object('CreateNetworkAcl', params, NetworkAcl)

    def delete_network_acl(self, network_acl_id):
        """
        Delete a network ACL

        :type network_acl_id: str
        :param network_acl_id: The ID of the network_acl to delete.

        :rtype: bool
        :return: True if successful
        """
        params = {'NetworkAclId': network_acl_id}
        return self.get_status('DeleteNetworkAcl', params)

    def create_network_acl_entry(self, network_acl_id, rule_number, protocol, rule_action,
                                 cidr_block, egress=None, icmp_code=None, icmp_type=None,
                                 port_range_from=None, port_range_to=None):
        """
        Creates a new network ACL entry in a network ACL within a VPC.

        :type network_acl_id: str
        :param network_acl_id: The ID of the network ACL for this network ACL entry.

        :type rule_number: int
        :param rule_number: The rule number to assign to the entry (for example, 100).

        :type protocol: int
        :param protocol: Valid values: -1 or a protocol number
        (http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml)

        :type rule_action: str
        :param rule_action: Indicates whether to allow or deny traffic that matches the rule.

        :type cidr_block: str
        :param cidr_block: The CIDR range to allow or deny, in CIDR notation (for example,
        172.16.0.0/24).

        :type egress: bool
        :param egress: Indicates whether this rule applies to egress traffic from the subnet (true)
        or ingress traffic to the subnet (false).

        :type icmp_type: int
        :param icmp_type: For the ICMP protocol, the ICMP type. You can use -1 to specify
         all ICMP types.

        :type icmp_code: int
        :param icmp_code: For the ICMP protocol, the ICMP code. You can use -1 to specify
        all ICMP codes for the given ICMP type.

        :type port_range_from: int
        :param port_range_from: The first port in the range.

        :type port_range_to: int
        :param port_range_to: The last port in the range.


        :rtype: bool
        :return: True if successful
        """
        params = {
            'NetworkAclId': network_acl_id,
            'RuleNumber': rule_number,
            'Protocol': protocol,
            'RuleAction': rule_action,
            'CidrBlock': cidr_block
        }

        if egress is not None:
            if isinstance(egress, bool):
                egress = str(egress).lower()
            params['Egress'] = egress
        if icmp_code is not None:
            params['Icmp.Code'] = icmp_code
        if icmp_type is not None:
            params['Icmp.Type'] = icmp_type
        if port_range_from is not None:
            params['PortRange.From'] = port_range_from
        if port_range_to is not None:
            params['PortRange.To'] = port_range_to

        return self.get_status('CreateNetworkAclEntry', params)

    def replace_network_acl_entry(self, network_acl_id, rule_number, protocol, rule_action,
                                  cidr_block, egress=None, icmp_code=None, icmp_type=None,
                                  port_range_from=None, port_range_to=None):
        """
        Creates a new network ACL entry in a network ACL within a VPC.

        :type network_acl_id: str
        :param network_acl_id: The ID of the network ACL for the id you want to replace

        :type rule_number: int
        :param rule_number: The rule number that you want to replace(for example, 100).

        :type protocol: int
        :param protocol: Valid values: -1 or a protocol number
        (http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml)

        :type rule_action: str
        :param rule_action: Indicates whether to allow or deny traffic that matches the rule.

        :type cidr_block: str
        :param cidr_block: The CIDR range to allow or deny, in CIDR notation (for example,
        172.16.0.0/24).

        :type egress: bool
        :param egress: Indicates whether this rule applies to egress traffic from the subnet (true)
        or ingress traffic to the subnet (false).

        :type icmp_type: int
        :param icmp_type: For the ICMP protocol, the ICMP type. You can use -1 to specify
         all ICMP types.

        :type icmp_code: int
        :param icmp_code: For the ICMP protocol, the ICMP code. You can use -1 to specify
        all ICMP codes for the given ICMP type.

        :type port_range_from: int
        :param port_range_from: The first port in the range.

        :type port_range_to: int
        :param port_range_to: The last port in the range.


        :rtype: bool
        :return: True if successful
        """
        params = {
            'NetworkAclId': network_acl_id,
            'RuleNumber': rule_number,
            'Protocol': protocol,
            'RuleAction': rule_action,
            'CidrBlock': cidr_block
        }

        if egress is not None:
            if isinstance(egress, bool):
                egress = str(egress).lower()
            params['Egress'] = egress
        if icmp_code is not None:
            params['Icmp.Code'] = icmp_code
        if icmp_type is not None:
            params['Icmp.Type'] = icmp_type
        if port_range_from is not None:
            params['PortRange.From'] = port_range_from
        if port_range_to is not None:
            params['PortRange.To'] = port_range_to

        return self.get_status('ReplaceNetworkAclEntry', params)

    def delete_network_acl_entry(self, network_acl_id, rule_number, egress=None):
        """
        Deletes a network ACL entry from a network ACL within a VPC.

        :type network_acl_id: str
        :param network_acl_id: The ID of the network ACL with the network ACL entry.

        :type rule_number: int
        :param rule_number: The rule number for the entry to delete.

        :type egress: bool
        :param egress: Specifies whether the rule to delete is an egress rule (true)
        or ingress rule (false).

        :rtype: bool
        :return: True if successful
        """
        params = {
            'NetworkAclId': network_acl_id,
            'RuleNumber': rule_number
        }

        if egress is not None:
            if isinstance(egress, bool):
                egress = str(egress).lower()
            params['Egress'] = egress

        return self.get_status('DeleteNetworkAclEntry', params)

    # Internet Gateways

    def get_all_internet_gateways(self, internet_gateway_ids=None,
                                  filters=None, dry_run=False):
        """
        Get a list of internet gateways. You can filter results to return information
        about only those gateways that you're interested in.

        :type internet_gateway_ids: list
        :param internet_gateway_ids: A list of strings with the desired gateway IDs.

        :type filters: list of tuples or dict
        :param filters: A list of tuples or dict containing filters.  Each tuple
                        or dict item consists of a filter key and a filter value.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {}

        if internet_gateway_ids:
            self.build_list_params(params, internet_gateway_ids,
                                   'InternetGatewayId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeInternetGateways', params,
                             [('item', InternetGateway)])

    def create_internet_gateway(self, dry_run=False):
        """
        Creates an internet gateway for VPC.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: Newly created internet gateway.
        :return: `boto.vpc.internetgateway.InternetGateway`
        """
        params = {}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateInternetGateway', params, InternetGateway)

    def delete_internet_gateway(self, internet_gateway_id, dry_run=False):
        """
        Deletes an internet gateway from the VPC.

        :type internet_gateway_id: str
        :param internet_gateway_id: The ID of the internet gateway to delete.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: Bool
        :return: True if successful
        """
        params = {'InternetGatewayId': internet_gateway_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteInternetGateway', params)

    def attach_internet_gateway(self, internet_gateway_id, vpc_id,
                                dry_run=False):
        """
        Attach an internet gateway to a specific VPC.

        :type internet_gateway_id: str
        :param internet_gateway_id: The ID of the internet gateway to attach.

        :type vpc_id: str
        :param vpc_id: The ID of the VPC to attach to.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: Bool
        :return: True if successful
        """
        params = {
            'InternetGatewayId': internet_gateway_id,
            'VpcId': vpc_id
        }
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('AttachInternetGateway', params)

    def detach_internet_gateway(self, internet_gateway_id, vpc_id,
                                dry_run=False):
        """
        Detach an internet gateway from a specific VPC.

        :type internet_gateway_id: str
        :param internet_gateway_id: The ID of the internet gateway to detach.

        :type vpc_id: str
        :param vpc_id: The ID of the VPC to attach to.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: Bool
        :return: True if successful
        """
        params = {
            'InternetGatewayId': internet_gateway_id,
            'VpcId': vpc_id
        }
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DetachInternetGateway', params)

    # Customer Gateways

    def get_all_customer_gateways(self, customer_gateway_ids=None,
                                  filters=None, dry_run=False):
        """
        Retrieve information about your CustomerGateways.  You can filter
        results to return information only about those CustomerGateways that
        match your search parameters.  Otherwise, all CustomerGateways
        associated with your account are returned.

        :type customer_gateway_ids: list
        :param customer_gateway_ids: A list of strings with the desired
            CustomerGateway ID's.

        :type filters: list of tuples or dict
        :param filters: A list of tuples or dict containing filters.  Each tuple
                        or dict item consists of a filter key and a filter value.
                        Possible filter keys are:

                         - *state*, the state of the CustomerGateway
                           (pending,available,deleting,deleted)
                         - *type*, the type of customer gateway (ipsec.1)
                         - *ipAddress* the IP address of customer gateway's
                           internet-routable external inteface

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.vpc.customergateway.CustomerGateway`
        """
        params = {}
        if customer_gateway_ids:
            self.build_list_params(params, customer_gateway_ids,
                                   'CustomerGatewayId')
        if filters:
            self.build_filter_params(params, filters)

        if dry_run:
            params['DryRun'] = 'true'

        return self.get_list('DescribeCustomerGateways', params,
                             [('item', CustomerGateway)])

    def create_customer_gateway(self, type, ip_address, bgp_asn, dry_run=False):
        """
        Create a new Customer Gateway

        :type type: str
        :param type: Type of VPN Connection.  Only valid value currently is 'ipsec.1'

        :type ip_address: str
        :param ip_address: Internet-routable IP address for customer's gateway.
                           Must be a static address.

        :type bgp_asn: int
        :param bgp_asn: Customer gateway's Border Gateway Protocol (BGP)
                        Autonomous System Number (ASN)

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: The newly created CustomerGateway
        :return: A :class:`boto.vpc.customergateway.CustomerGateway` object
        """
        params = {'Type': type,
                  'IpAddress': ip_address,
                  'BgpAsn': bgp_asn}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateCustomerGateway', params, CustomerGateway)

    def delete_customer_gateway(self, customer_gateway_id, dry_run=False):
        """
        Delete a Customer Gateway.

        :type customer_gateway_id: str
        :param customer_gateway_id: The ID of the customer_gateway to be deleted.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'CustomerGatewayId': customer_gateway_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteCustomerGateway', params)

    # VPN Gateways

    def get_all_vpn_gateways(self, vpn_gateway_ids=None, filters=None,
                             dry_run=False):
        """
        Retrieve information about your VpnGateways.  You can filter results to
        return information only about those VpnGateways that match your search
        parameters.  Otherwise, all VpnGateways associated with your account
        are returned.

        :type vpn_gateway_ids: list
        :param vpn_gateway_ids: A list of strings with the desired VpnGateway ID's

        :type filters: list of tuples or dict
        :param filters: A list of tuples or dict containing filters.  Each tuple
                        or dict item consists of a filter key and a filter value.
                        Possible filter keys are:

                        - *state*, a list of states of the VpnGateway
                          (pending,available,deleting,deleted)
                        - *type*, a list types of customer gateway (ipsec.1)
                        - *availabilityZone*, a list of  Availability zones the
                          VPN gateway is in.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.vpc.customergateway.VpnGateway`
        """
        params = {}
        if vpn_gateway_ids:
            self.build_list_params(params, vpn_gateway_ids, 'VpnGatewayId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeVpnGateways', params,
                             [('item', VpnGateway)])

    def create_vpn_gateway(self, type, availability_zone=None, dry_run=False):
        """
        Create a new Vpn Gateway

        :type type: str
        :param type: Type of VPN Connection.  Only valid value currently is 'ipsec.1'

        :type availability_zone: str
        :param availability_zone: The Availability Zone where you want the VPN gateway.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: The newly created VpnGateway
        :return: A :class:`boto.vpc.vpngateway.VpnGateway` object
        """
        params = {'Type': type}
        if availability_zone:
            params['AvailabilityZone'] = availability_zone
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateVpnGateway', params, VpnGateway)

    def delete_vpn_gateway(self, vpn_gateway_id, dry_run=False):
        """
        Delete a Vpn Gateway.

        :type vpn_gateway_id: str
        :param vpn_gateway_id: The ID of the vpn_gateway to be deleted.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'VpnGatewayId': vpn_gateway_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteVpnGateway', params)

    def attach_vpn_gateway(self, vpn_gateway_id, vpc_id, dry_run=False):
        """
        Attaches a VPN gateway to a VPC.

        :type vpn_gateway_id: str
        :param vpn_gateway_id: The ID of the vpn_gateway to attach

        :type vpc_id: str
        :param vpc_id: The ID of the VPC you want to attach the gateway to.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: An attachment
        :return: a :class:`boto.vpc.vpngateway.Attachment`
        """
        params = {'VpnGatewayId': vpn_gateway_id,
                  'VpcId': vpc_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('AttachVpnGateway', params, Attachment)

    def detach_vpn_gateway(self, vpn_gateway_id, vpc_id, dry_run=False):
        """
        Detaches a VPN gateway from a VPC.

        :type vpn_gateway_id: str
        :param vpn_gateway_id: The ID of the vpn_gateway to detach

        :type vpc_id: str
        :param vpc_id: The ID of the VPC you want to detach the gateway from.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'VpnGatewayId': vpn_gateway_id,
                  'VpcId': vpc_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DetachVpnGateway', params)

    # Subnets

    def get_all_subnets(self, subnet_ids=None, filters=None, dry_run=False):
        """
        Retrieve information about your Subnets.  You can filter results to
        return information only about those Subnets that match your search
        parameters.  Otherwise, all Subnets associated with your account
        are returned.

        :type subnet_ids: list
        :param subnet_ids: A list of strings with the desired Subnet ID's

        :type filters: list of tuples or dict
        :param filters: A list of tuples or dict containing filters.  Each tuple
                        or dict item consists of a filter key and a filter value.
                        Possible filter keys are:

                        - *state*, a list of states of the Subnet
                          (pending,available)
                        - *vpcId*, a list of IDs of the VPC that the subnet is in.
                        - *cidrBlock*, a list of CIDR blocks of the subnet
                        - *availabilityZone*, list of the Availability Zones
                          the subnet is in.


        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.vpc.subnet.Subnet`
        """
        params = {}
        if subnet_ids:
            self.build_list_params(params, subnet_ids, 'SubnetId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeSubnets', params, [('item', Subnet)])

    def create_subnet(self, vpc_id, cidr_block, availability_zone=None,
                      dry_run=False):
        """
        Create a new Subnet

        :type vpc_id: str
        :param vpc_id: The ID of the VPC where you want to create the subnet.

        :type cidr_block: str
        :param cidr_block: The CIDR block you want the subnet to cover.

        :type availability_zone: str
        :param availability_zone: The AZ you want the subnet in

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: The newly created Subnet
        :return: A :class:`boto.vpc.customergateway.Subnet` object
        """
        params = {'VpcId': vpc_id,
                  'CidrBlock': cidr_block}
        if availability_zone:
            params['AvailabilityZone'] = availability_zone
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateSubnet', params, Subnet)

    def delete_subnet(self, subnet_id, dry_run=False):
        """
        Delete a subnet.

        :type subnet_id: str
        :param subnet_id: The ID of the subnet to be deleted.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'SubnetId': subnet_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteSubnet', params)

    # DHCP Options

    def get_all_dhcp_options(self, dhcp_options_ids=None, filters=None, dry_run=False):
        """
        Retrieve information about your DhcpOptions.

        :type dhcp_options_ids: list
        :param dhcp_options_ids: A list of strings with the desired DhcpOption ID's

        :type filters: list of tuples or dict
        :param filters: A list of tuples or dict containing filters.  Each tuple
            or dict item consists of a filter key and a filter value.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.vpc.dhcpoptions.DhcpOptions`
        """
        params = {}
        if dhcp_options_ids:
            self.build_list_params(params, dhcp_options_ids, 'DhcpOptionsId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeDhcpOptions', params,
                             [('item', DhcpOptions)])

    def create_dhcp_options(self, domain_name=None, domain_name_servers=None,
                            ntp_servers=None, netbios_name_servers=None,
                            netbios_node_type=None, dry_run=False):
        """
        Create a new DhcpOption

        This corresponds to
        http://docs.amazonwebservices.com/AWSEC2/latest/APIReference/ApiReference-query-CreateDhcpOptions.html

        :type domain_name: str
        :param domain_name: A domain name of your choice (for example,
            example.com)

        :type domain_name_servers: list of strings
        :param domain_name_servers: The IP address of a domain name server. You
            can specify up to four addresses.

        :type ntp_servers: list of strings
        :param ntp_servers: The IP address of a Network Time Protocol (NTP)
            server. You can specify up to four addresses.

        :type netbios_name_servers: list of strings
        :param netbios_name_servers: The IP address of a NetBIOS name server.
            You can specify up to four addresses.

        :type netbios_node_type: str
        :param netbios_node_type: The NetBIOS node type (1, 2, 4, or 8). For
            more information about the values, see RFC 2132. We recommend you
            only use 2 at this time (broadcast and multicast are currently not
            supported).

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: The newly created DhcpOption
        :return: A :class:`boto.vpc.customergateway.DhcpOption` object
        """

        key_counter = 1
        params = {}

        def insert_option(params, name, value):
            params['DhcpConfiguration.%d.Key' % (key_counter,)] = name
            if isinstance(value, (list, tuple)):
                for idx, value in enumerate(value, 1):
                    key_name = 'DhcpConfiguration.%d.Value.%d' % (
                        key_counter, idx)
                    params[key_name] = value
            else:
                key_name = 'DhcpConfiguration.%d.Value.1' % (key_counter,)
                params[key_name] = value

            return key_counter + 1

        if domain_name:
            key_counter = insert_option(params,
                                        'domain-name', domain_name)
        if domain_name_servers:
            key_counter = insert_option(params,
                                        'domain-name-servers', domain_name_servers)
        if ntp_servers:
            key_counter = insert_option(params,
                                        'ntp-servers', ntp_servers)
        if netbios_name_servers:
            key_counter = insert_option(params,
                                        'netbios-name-servers', netbios_name_servers)
        if netbios_node_type:
            key_counter = insert_option(params,
                                        'netbios-node-type', netbios_node_type)
        if dry_run:
            params['DryRun'] = 'true'

        return self.get_object('CreateDhcpOptions', params, DhcpOptions)

    def delete_dhcp_options(self, dhcp_options_id, dry_run=False):
        """
        Delete a DHCP Options

        :type dhcp_options_id: str
        :param dhcp_options_id: The ID of the DHCP Options to be deleted.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'DhcpOptionsId': dhcp_options_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteDhcpOptions', params)

    def associate_dhcp_options(self, dhcp_options_id, vpc_id, dry_run=False):
        """
        Associate a set of Dhcp Options with a VPC.

        :type dhcp_options_id: str
        :param dhcp_options_id: The ID of the Dhcp Options

        :type vpc_id: str
        :param vpc_id: The ID of the VPC.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'DhcpOptionsId': dhcp_options_id,
                  'VpcId': vpc_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('AssociateDhcpOptions', params)

    # VPN Connection

    def get_all_vpn_connections(self, vpn_connection_ids=None, filters=None,
                                dry_run=False):
        """
        Retrieve information about your VPN_CONNECTIONs.  You can filter results to
        return information only about those VPN_CONNECTIONs that match your search
        parameters.  Otherwise, all VPN_CONNECTIONs associated with your account
        are returned.

        :type vpn_connection_ids: list
        :param vpn_connection_ids: A list of strings with the desired VPN_CONNECTION ID's

        :type filters: list of tuples or dict
        :param filters: A list of tuples or dict containing filters.  Each tuple
                        or dict item consists of a filter key and a filter value.
                        Possible filter keys are:

                        - *state*, a list of states of the VPN_CONNECTION
                          pending,available,deleting,deleted
                        - *type*, a list of types of connection, currently 'ipsec.1'
                        - *customerGatewayId*, a list of IDs of the customer gateway
                          associated with the VPN
                        - *vpnGatewayId*, a list of IDs of the VPN gateway associated
                          with the VPN connection

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.vpn_connection.vpnconnection.VpnConnection`
        """
        params = {}
        if vpn_connection_ids:
            self.build_list_params(params, vpn_connection_ids,
                                   'VpnConnectionId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeVpnConnections', params,
                             [('item', VpnConnection)])

    def create_vpn_connection(self, type, customer_gateway_id, vpn_gateway_id,
                              static_routes_only=None, dry_run=False):
        """
        Create a new VPN Connection.

        :type type: str
        :param type: The type of VPN Connection.  Currently only 'ipsec.1'
                     is supported

        :type customer_gateway_id: str
        :param customer_gateway_id: The ID of the customer gateway.

        :type vpn_gateway_id: str
        :param vpn_gateway_id: The ID of the VPN gateway.

        :type static_routes_only: bool
        :param static_routes_only: Indicates whether the VPN connection
        requires static routes. If you are creating a VPN connection
        for a device that does not support BGP, you must specify true.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: The newly created VpnConnection
        :return: A :class:`boto.vpc.vpnconnection.VpnConnection` object
        """
        params = {'Type': type,
                  'CustomerGatewayId': customer_gateway_id,
                  'VpnGatewayId': vpn_gateway_id}
        if static_routes_only is not None:
            if isinstance(static_routes_only, bool):
                static_routes_only = str(static_routes_only).lower()
            params['Options.StaticRoutesOnly'] = static_routes_only
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateVpnConnection', params, VpnConnection)

    def delete_vpn_connection(self, vpn_connection_id, dry_run=False):
        """
        Delete a VPN Connection.

        :type vpn_connection_id: str
        :param vpn_connection_id: The ID of the vpn_connection to be deleted.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'VpnConnectionId': vpn_connection_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteVpnConnection', params)

    def disable_vgw_route_propagation(self, route_table_id, gateway_id,
                                      dry_run=False):
        """
        Disables a virtual private gateway (VGW) from propagating routes to the
        routing tables of an Amazon VPC.

        :type route_table_id: str
        :param route_table_id: The ID of the routing table.

        :type gateway_id: str
        :param gateway_id: The ID of the virtual private gateway.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {
            'RouteTableId': route_table_id,
            'GatewayId': gateway_id,
        }
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DisableVgwRoutePropagation', params)

    def enable_vgw_route_propagation(self, route_table_id, gateway_id,
                                     dry_run=False):
        """
        Enables a virtual private gateway (VGW) to propagate routes to the
        routing tables of an Amazon VPC.

        :type route_table_id: str
        :param route_table_id: The ID of the routing table.

        :type gateway_id: str
        :param gateway_id: The ID of the virtual private gateway.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {
            'RouteTableId': route_table_id,
            'GatewayId': gateway_id,
        }
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('EnableVgwRoutePropagation', params)

    def create_vpn_connection_route(self, destination_cidr_block,
                                    vpn_connection_id, dry_run=False):
        """
        Creates a new static route associated with a VPN connection between an
        existing virtual private gateway and a VPN customer gateway. The static
        route allows traffic to be routed from the virtual private gateway to
        the VPN customer gateway.

        :type destination_cidr_block: str
        :param destination_cidr_block: The CIDR block associated with the local
            subnet of the customer data center.

        :type vpn_connection_id: str
        :param vpn_connection_id: The ID of the VPN connection.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {
            'DestinationCidrBlock': destination_cidr_block,
            'VpnConnectionId': vpn_connection_id,
        }
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('CreateVpnConnectionRoute', params)

    def delete_vpn_connection_route(self, destination_cidr_block,
                                    vpn_connection_id, dry_run=False):
        """
        Deletes a static route associated with a VPN connection between an
        existing virtual private gateway and a VPN customer gateway. The static
        route allows traffic to be routed from the virtual private gateway to
        the VPN customer gateway.

        :type destination_cidr_block: str
        :param destination_cidr_block: The CIDR block associated with the local
            subnet of the customer data center.

        :type vpn_connection_id: str
        :param vpn_connection_id: The ID of the VPN connection.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {
            'DestinationCidrBlock': destination_cidr_block,
            'VpnConnectionId': vpn_connection_id,
        }
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteVpnConnectionRoute', params)

    def get_all_vpc_peering_connections(self, vpc_peering_connection_ids=None, 
                                        filters=None, dry_run=False):
        """
        Retrieve information about your VPC peering connections. You
        can filter results to return information only about those VPC
        peering connections that match your search parameters.
        Otherwise, all VPC peering connections associated with your
        account are returned.

        :type vpc_peering_connection_ids: list
        :param vpc_peering_connection_ids: A list of strings with the desired VPC
            peering connection ID's

        :type filters: list of tuples
        :param filters: A list of tuples containing filters. Each tuple
            consists of a filter key and a filter value.
            Possible filter keys are:

            * *accepter-vpc-info.cidr-block* - The CIDR block of the peer VPC.
            * *accepter-vpc-info.owner-id* - The AWS account ID of the owner 
                of the peer VPC.
            * *accepter-vpc-info.vpc-id* - The ID of the peer VPC.
            * *expiration-time* - The expiration date and time for the VPC 
                peering connection.
            * *requester-vpc-info.cidr-block* - The CIDR block of the 
                requester's VPC.
            * *requester-vpc-info.owner-id* - The AWS account ID of the 
                owner of the requester VPC.
            * *requester-vpc-info.vpc-id* - The ID of the requester VPC.
            * *status-code* - The status of the VPC peering connection.
            * *status-message* - A message that provides more information 
                about the status of the VPC peering connection, if applicable.
            
        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.vpc.vpc.VPC`
        """
        params = {}
        if vpc_peering_connection_ids:
            self.build_list_params(params, vpc_peering_connection_ids, 'VpcPeeringConnectionId')
        if filters:
            self.build_filter_params(params, dict(filters))
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeVpcPeeringConnections', params, [('item', VpcPeeringConnection)])
    
    def create_vpc_peering_connection(self, vpc_id, peer_vpc_id, 
                                      peer_owner_id=None, dry_run=False):
        """
        Create a new VPN Peering connection.

        :type vpc_id: str
        :param vpc_id: The ID of the requester VPC.

        :type peer_vpc_id: str
        :param vpc_peer_id: The ID of the VPC with which you are creating the peering connection.

        :type peer_owner_id: str
        :param peer_owner_id: The AWS account ID of the owner of the peer VPC.

        :rtype: The newly created VpcPeeringConnection
        :return: A :class:`boto.vpc.vpc_peering_connection.VpcPeeringConnection` object
        """
        params = {'VpcId': vpc_id,
                  'PeerVpcId': peer_vpc_id }
        if peer_owner_id is not None:
            params['PeerOwnerId'] = peer_owner_id
        if dry_run:
            params['DryRun'] = 'true'

        return self.get_object('CreateVpcPeeringConnection', params, 
                               VpcPeeringConnection)

    def delete_vpc_peering_connection(self, vpc_peering_connection_id, dry_run=False):
        """
        Deletes a VPC peering connection. Either the owner of the requester 
        VPC or the owner of the peer VPC can delete the VPC peering connection 
        if it's in the active state. The owner of the requester VPC can delete 
        a VPC peering connection in the pending-acceptance state.

        :type vpc_peering_connection_id: str
        :param vpc_peering_connection_id: The ID of the VPC peering connection.

        :rtype: bool
        :return: True if successful
        """
        params = {
            'VpcPeeringConnectionId': vpc_peering_connection_id
        }

        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteVpcPeeringConnection', params)

    def reject_vpc_peering_connection(self, vpc_peering_connection_id, dry_run=False):
        """
        Rejects a VPC peering connection request. The VPC peering connection 
        must be in the pending-acceptance state. 

        :type vpc_peering_connection_id: str
        :param vpc_peering_connection_id: The ID of the VPC peering connection.

        :rtype: bool
        :return: True if successful
        """
        params = {
            'VpcPeeringConnectionId': vpc_peering_connection_id
        }

        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('RejectVpcPeeringConnection', params)

    def accept_vpc_peering_connection(self, vpc_peering_connection_id, dry_run=False):
        """
        Acceptss a VPC peering connection request. The VPC peering connection 
        must be in the pending-acceptance state. 

        :type vpc_peering_connection_id: str
        :param vpc_peering_connection_id: The ID of the VPC peering connection.

        :rtype: Accepted VpcPeeringConnection
        :return: A :class:`boto.vpc.vpc_peering_connection.VpcPeeringConnection` object
        """
        params = {
            'VpcPeeringConnectionId': vpc_peering_connection_id
        }

        if dry_run:
            params['DryRun'] = 'true'

        return self.get_object('AcceptVpcPeeringConnection', params, 
                               VpcPeeringConnection)

    def get_all_classic_link_vpcs(self, vpc_ids=None, filters=None,
                                   dry_run=False):
        """
        Describes the ClassicLink status of one or more VPCs.

        :type vpc_ids: list
        :param vpc_ids: A list of strings with the desired VPC ID's

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :type filters: list of tuples or dict
        :param filters: A list of tuples or dict containing filters. Each tuple
            or dict item consists of a filter key and a filter value.

        :rtype: list
        :return: A list of :class:`boto.vpc.vpc.VPC`
        """
        params = {}
        if vpc_ids:
            self.build_list_params(params, vpc_ids, 'VpcId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeVpcClassicLink', params, [('item', VPC)],
                             verb='POST')

    def attach_classic_link_vpc(self, vpc_id, instance_id, groups,
                                dry_run=False):
        """
        Links  an EC2-Classic instance to a ClassicLink-enabled VPC through one
        or more of the VPC's security groups. You cannot link an EC2-Classic
        instance to more than one VPC at a time. You can only link an instance
        that's in the running state. An instance is automatically unlinked from
        a VPC when it's stopped. You can link it to the VPC again when you
        restart it.

        After you've linked an instance, you cannot  change  the VPC security
        groups  that are associated with it. To change the security groups, you
        must first unlink the instance, and then link it again.

        Linking your instance to a VPC is sometimes referred  to  as  attaching
        your instance.

        :type vpc_id: str
        :param vpc_id: The ID of a ClassicLink-enabled VPC.

        :type intance_id: str
        :param instance_is: The ID of a ClassicLink-enabled VPC.

        :tye groups: list
        :param groups: The ID of one or more of the VPC's security groups.
            You cannot specify security groups from a different VPC. The
            members of the list can be
            :class:`boto.ec2.securitygroup.SecurityGroup` objects or
            strings of the id's of the security groups.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'VpcId': vpc_id, 'InstanceId': instance_id}
        if dry_run:
            params['DryRun'] = 'true'
        l = []
        for group in groups:
            if hasattr(group, 'id'):
                l.append(group.id)
            else:
                l.append(group)
        self.build_list_params(params, l, 'SecurityGroupId')
        return self.get_status('AttachClassicLinkVpc', params)

    def detach_classic_link_vpc(self, vpc_id, instance_id, dry_run=False):
        """
        Unlinks a linked EC2-Classic instance from a VPC. After the instance
        has been unlinked, the VPC security groups are no longer associated
        with it. An instance is automatically unlinked from a VPC when
        it's stopped.

        :type vpc_id: str
        :param vpc_id: The ID of the instance to unlink from the VPC.

        :type intance_id: str
        :param instance_is: The ID of the VPC to which the instance is linked.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'VpcId': vpc_id, 'InstanceId': instance_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DetachClassicLinkVpc', params)

    def disable_vpc_classic_link(self, vpc_id, dry_run=False):
        """
        Disables  ClassicLink  for  a VPC. You cannot disable ClassicLink for a
        VPC that has EC2-Classic instances linked to it.

        :type vpc_id: str
        :param vpc_id: The ID of the VPC.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'VpcId': vpc_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DisableVpcClassicLink', params)

    def enable_vpc_classic_link(self, vpc_id, dry_run=False):
        """
        Enables a VPC for ClassicLink. You can then link EC2-Classic instances
        to your ClassicLink-enabled VPC to allow communication over private IP
        addresses. You cannot enable your VPC for ClassicLink if any of your
        VPC's route tables have existing routes for address ranges within the
        10.0.0.0/8 IP address range, excluding local routes for VPCs in the
        10.0.0.0/16 and 10.1.0.0/16 IP address ranges.

        :type vpc_id: str
        :param vpc_id: The ID of the VPC.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'VpcId': vpc_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('EnableVpcClassicLink', params)
