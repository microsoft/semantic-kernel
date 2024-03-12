# Copyright (c) 2013 Franc Carter - franc.carter@gmail.com
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
Represents an DBSubnetGroup
"""

class DBSubnetGroup(object):
    """
    Represents an RDS database subnet group

    Properties reference available from the AWS documentation at http://docs.amazonwebservices.com/AmazonRDS/latest/APIReference/API_DeleteDBSubnetGroup.html

    :ivar status: The current status of the subnet group. Possibile values are [ active, ? ]. Reference documentation lacks specifics of possibilities
    :ivar connection: boto.rds.RDSConnection associated with the current object
    :ivar description: The description of the subnet group
    :ivar subnet_ids: List of subnet identifiers in the group
    :ivar name: Name of the subnet group
    :ivar vpc_id: The ID of the VPC the subnets are inside
    """
    def __init__(self, connection=None, name=None, description=None, subnet_ids=None):
        self.connection = connection
        self.name = name
        self.description = description
        if subnet_ids is not None:
            self.subnet_ids = subnet_ids
        else:
            self.subnet_ids = []
        self.vpc_id = None
        self.status = None

    def __repr__(self):
        return 'DBSubnetGroup:%s' % self.name

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'SubnetIdentifier':
            self.subnet_ids.append(value)
        elif name == 'DBSubnetGroupName':
            self.name = value
        elif name == 'DBSubnetGroupDescription':
            self.description = value
        elif name == 'VpcId':
            self.vpc_id = value
        elif name == 'SubnetGroupStatus':
            self.status = value
        else:
            setattr(self, name, value)

