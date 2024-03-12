# Copyright (c) 2006-2011 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2011, Eucalyptus Systems, Inc.
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
Represents an EC2 Security Group
"""
from boto.ec2.ec2object import TaggedEC2Object
from boto.exception import BotoClientError


class SecurityGroup(TaggedEC2Object):

    def __init__(self, connection=None, owner_id=None,
                 name=None, description=None, id=None):
        super(SecurityGroup, self).__init__(connection)
        self.id = id
        self.owner_id = owner_id
        self.name = name
        self.description = description
        self.vpc_id = None
        self.rules = IPPermissionsList()
        self.rules_egress = IPPermissionsList()

    def __repr__(self):
        return 'SecurityGroup:%s' % self.name

    def startElement(self, name, attrs, connection):
        retval = super(SecurityGroup, self).startElement(name, attrs, connection)
        if retval is not None:
            return retval
        if name == 'ipPermissions':
            return self.rules
        elif name == 'ipPermissionsEgress':
            return self.rules_egress
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'ownerId':
            self.owner_id = value
        elif name == 'groupId':
            self.id = value
        elif name == 'groupName':
            self.name = value
        elif name == 'vpcId':
            self.vpc_id = value
        elif name == 'groupDescription':
            self.description = value
        elif name == 'ipRanges':
            pass
        elif name == 'return':
            if value == 'false':
                self.status = False
            elif value == 'true':
                self.status = True
            else:
                raise Exception(
                    'Unexpected value of status %s for group %s' % (
                        value,
                        self.name
                    )
                )
        else:
            setattr(self, name, value)

    def delete(self, dry_run=False):
        if self.vpc_id:
            return self.connection.delete_security_group(
                group_id=self.id,
                dry_run=dry_run
            )
        else:
            return self.connection.delete_security_group(
                self.name,
                dry_run=dry_run
            )

    def add_rule(self, ip_protocol, from_port, to_port,
                 src_group_name, src_group_owner_id, cidr_ip,
                 src_group_group_id, dry_run=False):
        """
        Add a rule to the SecurityGroup object.  Note that this method
        only changes the local version of the object.  No information
        is sent to EC2.
        """
        rule = IPPermissions(self)
        rule.ip_protocol = ip_protocol
        rule.from_port = from_port
        rule.to_port = to_port
        self.rules.append(rule)
        rule.add_grant(
            src_group_name,
            src_group_owner_id,
            cidr_ip,
            src_group_group_id,
            dry_run=dry_run
        )

    def remove_rule(self, ip_protocol, from_port, to_port,
                    src_group_name, src_group_owner_id, cidr_ip,
                    src_group_group_id, dry_run=False):
        """
        Remove a rule to the SecurityGroup object.  Note that this method
        only changes the local version of the object.  No information
        is sent to EC2.
        """
        if not self.rules:
            raise ValueError("The security group has no rules")

        target_rule = None
        for rule in self.rules:
            if rule.ip_protocol == ip_protocol:
                if rule.from_port == from_port:
                    if rule.to_port == to_port:
                        target_rule = rule
                        target_grant = None
                        for grant in rule.grants:
                            if grant.name == src_group_name or grant.group_id == src_group_group_id:
                                if grant.owner_id == src_group_owner_id:
                                    if grant.cidr_ip == cidr_ip:
                                        target_grant = grant
                        if target_grant:
                            rule.grants.remove(target_grant)
            if len(rule.grants) == 0:
                self.rules.remove(target_rule)

    def authorize(self, ip_protocol=None, from_port=None, to_port=None,
                  cidr_ip=None, src_group=None, dry_run=False):
        """
        Add a new rule to this security group.
        You need to pass in either src_group_name
        OR ip_protocol, from_port, to_port,
        and cidr_ip.  In other words, either you are authorizing another
        group or you are authorizing some ip-based rule.

        :type ip_protocol: string
        :param ip_protocol: Either tcp | udp | icmp

        :type from_port: int
        :param from_port: The beginning port number you are enabling

        :type to_port: int
        :param to_port: The ending port number you are enabling

        :type cidr_ip: string or list of strings
        :param cidr_ip: The CIDR block you are providing access to.
                        See http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing

        :type src_group: :class:`boto.ec2.securitygroup.SecurityGroup` or
                         :class:`boto.ec2.securitygroup.GroupOrCIDR`
        :param src_group: The Security Group you are granting access to.

        :rtype: bool
        :return: True if successful.
        """
        group_name = None
        if not self.vpc_id:
            group_name = self.name
        group_id = None
        if self.vpc_id:
            group_id = self.id
        src_group_name = None
        src_group_owner_id = None
        src_group_group_id = None
        if src_group:
            cidr_ip = None
            src_group_owner_id = src_group.owner_id
            if not self.vpc_id:
                src_group_name = src_group.name
            else:
                if hasattr(src_group, 'group_id'):
                    src_group_group_id = src_group.group_id
                else:
                    src_group_group_id = src_group.id
        status = self.connection.authorize_security_group(group_name,
                                                          src_group_name,
                                                          src_group_owner_id,
                                                          ip_protocol,
                                                          from_port,
                                                          to_port,
                                                          cidr_ip,
                                                          group_id,
                                                          src_group_group_id,
                                                          dry_run=dry_run)
        if status:
            if not isinstance(cidr_ip, list):
                cidr_ip = [cidr_ip]
            for single_cidr_ip in cidr_ip:
                self.add_rule(ip_protocol, from_port, to_port, src_group_name,
                              src_group_owner_id, single_cidr_ip,
                              src_group_group_id, dry_run=dry_run)
        return status

    def revoke(self, ip_protocol=None, from_port=None, to_port=None,
               cidr_ip=None, src_group=None, dry_run=False):
        group_name = None
        if not self.vpc_id:
            group_name = self.name
        group_id = None
        if self.vpc_id:
            group_id = self.id
        src_group_name = None
        src_group_owner_id = None
        src_group_group_id = None
        if src_group:
            cidr_ip = None
            src_group_owner_id = src_group.owner_id
            if not self.vpc_id:
                src_group_name = src_group.name
            else:
                if hasattr(src_group, 'group_id'):
                    src_group_group_id = src_group.group_id
                else:
                    src_group_group_id = src_group.id
        status = self.connection.revoke_security_group(group_name,
                                                       src_group_name,
                                                       src_group_owner_id,
                                                       ip_protocol,
                                                       from_port,
                                                       to_port,
                                                       cidr_ip,
                                                       group_id,
                                                       src_group_group_id,
                                                       dry_run=dry_run)
        if status:
            self.remove_rule(ip_protocol, from_port, to_port, src_group_name,
                             src_group_owner_id, cidr_ip, src_group_group_id,
                             dry_run=dry_run)
        return status

    def copy_to_region(self, region, name=None, dry_run=False):
        """
        Create a copy of this security group in another region.
        Note that the new security group will be a separate entity
        and will not stay in sync automatically after the copy
        operation.

        :type region: :class:`boto.ec2.regioninfo.RegionInfo`
        :param region: The region to which this security group will be copied.

        :type name: string
        :param name: The name of the copy.  If not supplied, the copy
                     will have the same name as this security group.

        :rtype: :class:`boto.ec2.securitygroup.SecurityGroup`
        :return: The new security group.
        """
        if region.name == self.region:
            raise BotoClientError('Unable to copy to the same Region')
        conn_params = self.connection.get_params()
        rconn = region.connect(**conn_params)
        sg = rconn.create_security_group(
            name or self.name,
            self.description,
            dry_run=dry_run
        )
        source_groups = []
        for rule in self.rules:
            for grant in rule.grants:
                grant_nom = grant.name or grant.group_id
                if grant_nom:
                    if grant_nom not in source_groups:
                        source_groups.append(grant_nom)
                        sg.authorize(None, None, None, None, grant,
                                     dry_run=dry_run)
                else:
                    sg.authorize(rule.ip_protocol, rule.from_port, rule.to_port,
                                 grant.cidr_ip, dry_run=dry_run)
        return sg

    def instances(self, dry_run=False):
        """
        Find all of the current instances that are running within this
        security group.

        :rtype: list of :class:`boto.ec2.instance.Instance`
        :return: A list of Instance objects
        """
        rs = []
        if self.vpc_id:
            rs.extend(self.connection.get_all_reservations(
                filters={'instance.group-id': self.id},
                dry_run=dry_run
            ))
        else:
            rs.extend(self.connection.get_all_reservations(
                filters={'group-id': self.id},
                dry_run=dry_run
            ))
        instances = [i for r in rs for i in r.instances]
        return instances


class IPPermissionsList(list):

    def startElement(self, name, attrs, connection):
        if name == 'item':
            self.append(IPPermissions(self))
            return self[-1]
        return None

    def endElement(self, name, value, connection):
        pass


class IPPermissions(object):

    def __init__(self, parent=None):
        self.parent = parent
        self.ip_protocol = None
        self.from_port = None
        self.to_port = None
        self.grants = []

    def __repr__(self):
        return 'IPPermissions:%s(%s-%s)' % (self.ip_protocol,
                                            self.from_port, self.to_port)

    def startElement(self, name, attrs, connection):
        if name == 'item':
            self.grants.append(GroupOrCIDR(self))
            return self.grants[-1]
        return None

    def endElement(self, name, value, connection):
        if name == 'ipProtocol':
            self.ip_protocol = value
        elif name == 'fromPort':
            self.from_port = value
        elif name == 'toPort':
            self.to_port = value
        else:
            setattr(self, name, value)

    def add_grant(self, name=None, owner_id=None, cidr_ip=None, group_id=None,
                  dry_run=False):
        grant = GroupOrCIDR(self)
        grant.owner_id = owner_id
        grant.group_id = group_id
        grant.name = name
        grant.cidr_ip = cidr_ip
        self.grants.append(grant)
        return grant


class GroupOrCIDR(object):

    def __init__(self, parent=None):
        self.owner_id = None
        self.group_id = None
        self.name = None
        self.cidr_ip = None

    def __repr__(self):
        if self.cidr_ip:
            return '%s' % self.cidr_ip
        else:
            return '%s-%s' % (self.name or self.group_id, self.owner_id)

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'userId':
            self.owner_id = value
        elif name == 'groupId':
            self.group_id = value
        elif name == 'groupName':
            self.name = value
        if name == 'cidrIp':
            self.cidr_ip = value
        else:
            setattr(self, name, value)
