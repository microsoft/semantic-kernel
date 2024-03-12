# Copyright (c) 2013 Anthony Tonns http://www.corsis.com/
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
Represents a VPCSecurityGroupMembership
"""


class VPCSecurityGroupMembership(object):
    """
    Represents VPC Security Group that this RDS database is a member of

    Properties reference available from the AWS documentation at
    http://docs.aws.amazon.com/AmazonRDS/latest/APIReference/\
    API_VpcSecurityGroupMembership.html

    Example::
        pri = "sg-abcdefgh"
        sec = "sg-hgfedcba"

        # Create with list of str
        db = c.create_dbinstance(... vpc_security_groups=[pri], ... )

        # Modify with list of str
        db.modify(... vpc_security_groups=[pri,sec], ... )

        # Create with objects
        memberships = []
        membership = VPCSecurityGroupMembership()
        membership.vpc_group = pri
        memberships.append(membership)

        db = c.create_dbinstance(... vpc_security_groups=memberships, ... )

        # Modify with objects
        memberships = d.vpc_security_groups
        membership = VPCSecurityGroupMembership()
        membership.vpc_group = sec
        memberships.append(membership)

        db.modify(...  vpc_security_groups=memberships, ... )

    :ivar connection: :py:class:`boto.rds.RDSConnection` associated with the
        current object
    :ivar vpc_group: This id of the VPC security group
    :ivar status: Status of the VPC security group membership
        <boto.ec2.securitygroup.SecurityGroup>` objects that this RDS Instance
        is a member of
    """
    def __init__(self, connection=None, status=None, vpc_group=None):
        self.connection = connection
        self.status = status
        self.vpc_group = vpc_group

    def __repr__(self):
        return 'VPCSecurityGroupMembership:%s' % self.vpc_group

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'VpcSecurityGroupId':
            self.vpc_group = value
        elif name == 'Status':
            self.status = value
        else:
            setattr(self, name, value)
