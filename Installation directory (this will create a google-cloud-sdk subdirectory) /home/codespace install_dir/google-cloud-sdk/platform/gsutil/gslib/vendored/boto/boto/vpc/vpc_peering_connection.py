# Copyright (c) 2014 Skytap http://skytap.com/
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
Represents a VPC Peering Connection.
"""

from boto.ec2.ec2object import TaggedEC2Object

class VpcInfo(object):
    def __init__(self):
        """
        Information on peer Vpc.
        
        :ivar id: The unique ID of peer Vpc.
        :ivar owner_id: Owner of peer Vpc.
        :ivar cidr_block: CIDR Block of peer Vpc.
        """

        self.vpc_id = None
        self.owner_id = None
        self.cidr_block = None

    def __repr__(self):
        return 'VpcInfo:%s' % self.vpc_id

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'vpcId':
            self.vpc_id = value
        elif name == 'ownerId':
            self.owner_id = value
        elif name == 'cidrBlock':
            self.cidr_block = value
        else:
            setattr(self, name, value)

class VpcPeeringConnectionStatus(object):
    """
    The status of VPC peering connection.

    :ivar code: The status of the VPC peering connection. Valid values are:

        * pending-acceptance
        * failed
        * expired
        * provisioning
        * active
        * deleted
        * rejected

    :ivar message: A message that provides more information about the status of the VPC peering connection, if applicable.
    """
    def __init__(self, code=0, message=None):
        self.code = code
        self.message = message

    def __repr__(self):
        return '%s(%d)' % (self.code, self.message)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'code':
            self.code = value
        elif name == 'message':
            self.message = value
        else:
            setattr(self, name, value)

    

class VpcPeeringConnection(TaggedEC2Object):

    def __init__(self, connection=None):
        """
        Represents a VPC peering connection.

        :ivar id: The unique ID of the VPC peering connection.
        :ivar accepter_vpc_info: Information on peer Vpc.
        :ivar requester_vpc_info: Information on requester Vpc.
        :ivar expiration_time: The expiration date and time for the VPC peering connection.
        :ivar status_code: The status of the VPC peering connection.
        :ivar status_message: A message that provides more information about the status of the VPC peering connection, if applicable.
        """
        super(VpcPeeringConnection, self).__init__(connection)
        self.id = None
        self.accepter_vpc_info = VpcInfo()
        self.requester_vpc_info = VpcInfo()
        self.expiration_time = None
        self._status = VpcPeeringConnectionStatus()

    @property
    def status_code(self):
        return self._status.code

    @property
    def status_message(self):
        return self._status.message

    def __repr__(self):
        return 'VpcPeeringConnection:%s' % self.id

    def startElement(self, name, attrs, connection):
        retval = super(VpcPeeringConnection, self).startElement(name, attrs, connection)
        if retval is not None:
            return retval
        
        if name == 'requesterVpcInfo':
            return self.requester_vpc_info
        elif name == 'accepterVpcInfo':
            return self.accepter_vpc_info
        elif name == 'status':
            return self._status

        return None

    def endElement(self, name, value, connection):
        if name == 'vpcPeeringConnectionId':
            self.id = value
        elif name == 'expirationTime':
            self.expiration_time = value
        else:
            setattr(self, name, value)

    def delete(self):
        return self.connection.delete_vpc_peering_connection(self.id)

    def _update(self, updated):
        self.__dict__.update(updated.__dict__)

    def update(self, validate=False, dry_run=False):
        vpc_peering_connection_list = self.connection.get_all_vpc_peering_connections(
            [self.id],
            dry_run=dry_run
        )
        if len(vpc_peering_connection_list):
            updated_vpc_peering_connection = vpc_peering_connection_list[0]
            self._update(updated_vpc_peering_connection)
        elif validate:
            raise ValueError('%s is not a valid VpcPeeringConnection ID' % (self.id,))
        return self.status_code
