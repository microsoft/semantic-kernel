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
Represents a Virtual Private Cloud.
"""

from boto.ec2.ec2object import TaggedEC2Object

class VPC(TaggedEC2Object):

    def __init__(self, connection=None):
        """
        Represents a VPC.

        :ivar id: The unique ID of the VPC.
        :ivar dhcp_options_id: The ID of the set of DHCP options you've associated with the VPC
                                (or default if the default options are associated with the VPC).
        :ivar state: The current state of the VPC.
        :ivar cidr_block: The CIDR block for the VPC.
        :ivar is_default: Indicates whether the VPC is the default VPC.
        :ivar instance_tenancy: The allowed tenancy of instances launched into the VPC.
        :ivar classic_link_enabled: Indicates whether ClassicLink is enabled.
        """
        super(VPC, self).__init__(connection)
        self.id = None
        self.dhcp_options_id = None
        self.state = None
        self.cidr_block = None
        self.is_default = None
        self.instance_tenancy = None
        self.classic_link_enabled = None

    def __repr__(self):
        return 'VPC:%s' % self.id

    def endElement(self, name, value, connection):
        if name == 'vpcId':
            self.id = value
        elif name == 'dhcpOptionsId':
            self.dhcp_options_id = value
        elif name == 'state':
            self.state = value
        elif name == 'cidrBlock':
            self.cidr_block = value
        elif name == 'isDefault':
            self.is_default = True if value == 'true' else False
        elif name == 'instanceTenancy':
            self.instance_tenancy = value
        elif name == 'classicLinkEnabled':
            self.classic_link_enabled = value
        else:
            setattr(self, name, value)

    def delete(self):
        return self.connection.delete_vpc(self.id)

    def _update(self, updated):
        self.__dict__.update(updated.__dict__)

    def _get_status_then_update_vpc(self, get_status_method, validate=False,
                                    dry_run=False):
        vpc_list = get_status_method(
            [self.id],
            dry_run=dry_run
        )
        if len(vpc_list):
            updated_vpc = vpc_list[0]
            self._update(updated_vpc)
        elif validate:
            raise ValueError('%s is not a valid VPC ID' % (self.id,))

    def update(self, validate=False, dry_run=False):
        self._get_status_then_update_vpc(
            self.connection.get_all_vpcs,
            validate=validate,
            dry_run=dry_run
        )
        return self.state

    def update_classic_link_enabled(self, validate=False, dry_run=False):
        """
        Updates instance's classic_link_enabled attribute

        :rtype: bool
        :return: self.classic_link_enabled after update has occurred.
        """
        self._get_status_then_update_vpc(
            self.connection.get_all_classic_link_vpcs,
            validate=validate,
            dry_run=dry_run
        )
        return self.classic_link_enabled

    def disable_classic_link(self, dry_run=False):
        """
        Disables  ClassicLink  for  a VPC. You cannot disable ClassicLink for a
        VPC that has EC2-Classic instances linked to it.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        return self.connection.disable_vpc_classic_link(self.id,
                                                        dry_run=dry_run)

    def enable_classic_link(self, dry_run=False):
        """
        Enables a VPC for ClassicLink. You can then link EC2-Classic instances
        to your ClassicLink-enabled VPC to allow communication over private IP
        addresses. You cannot enable your VPC for ClassicLink if any of your
        VPC's route tables have existing routes for address ranges within the
        10.0.0.0/8 IP address range, excluding local routes for VPCs in the
        10.0.0.0/16 and 10.1.0.0/16 IP address ranges.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        return self.connection.enable_vpc_classic_link(self.id,
                                                       dry_run=dry_run)

    def attach_classic_instance(self, instance_id, groups, dry_run=False):
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
        return self.connection.attach_classic_link_vpc(
            vpc_id=self.id,
            instance_id=instance_id,
            groups=groups,
            dry_run=dry_run
        )

    def detach_classic_instance(self, instance_id, dry_run=False):
        """
        Unlinks a linked EC2-Classic instance from a VPC. After the instance
        has been unlinked, the VPC security groups are no longer associated
        with it. An instance is automatically unlinked from a VPC when
        it's stopped.

        :type intance_id: str
        :param instance_is: The ID of the VPC to which the instance is linked.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        return self.connection.detach_classic_link_vpc(
            vpc_id=self.id,
            instance_id=instance_id,
            dry_run=dry_run
        )
