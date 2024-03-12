# Copyright (c) 2011 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
Represents an EC2 Elastic Network Interface
"""
from boto.exception import BotoClientError
from boto.ec2.ec2object import TaggedEC2Object
from boto.resultset import ResultSet
from boto.ec2.group import Group


class Attachment(object):
    """
    :ivar id: The ID of the attachment.
    :ivar instance_id: The ID of the instance.
    :ivar device_index: The index of this device.
    :ivar status: The status of the device.
    :ivar attach_time: The time the device was attached.
    :ivar delete_on_termination: Whether the device will be deleted
        when the instance is terminated.
    """

    def __init__(self):
        self.id = None
        self.instance_id = None
        self.instance_owner_id = None
        self.device_index = 0
        self.status = None
        self.attach_time = None
        self.delete_on_termination = False

    def __repr__(self):
        return 'Attachment:%s' % self.id

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'attachmentId':
            self.id = value
        elif name == 'instanceId':
            self.instance_id = value
        elif name == 'deviceIndex':
            self.device_index = int(value)
        elif name == 'instanceOwnerId':
            self.instance_owner_id = value
        elif name == 'status':
            self.status = value
        elif name == 'attachTime':
            self.attach_time = value
        elif name == 'deleteOnTermination':
            if value.lower() == 'true':
                self.delete_on_termination = True
            else:
                self.delete_on_termination = False
        else:
            setattr(self, name, value)


class NetworkInterface(TaggedEC2Object):
    """
    An Elastic Network Interface.

    :ivar id: The ID of the ENI.
    :ivar subnet_id: The ID of the VPC subnet.
    :ivar vpc_id: The ID of the VPC.
    :ivar description: The description.
    :ivar owner_id: The ID of the owner of the ENI.
    :ivar requester_managed:
    :ivar status: The interface's status (available|in-use).
    :ivar mac_address: The MAC address of the interface.
    :ivar private_ip_address: The IP address of the interface within
        the subnet.
    :ivar source_dest_check: Flag to indicate whether to validate
        network traffic to or from this network interface.
    :ivar groups: List of security groups associated with the interface.
    :ivar attachment: The attachment object.
    :ivar private_ip_addresses: A list of PrivateIPAddress objects.
    """

    def __init__(self, connection=None):
        super(NetworkInterface, self).__init__(connection)
        self.id = None
        self.subnet_id = None
        self.vpc_id = None
        self.availability_zone = None
        self.description = None
        self.owner_id = None
        self.requester_managed = False
        self.status = None
        self.mac_address = None
        self.private_ip_address = None
        self.source_dest_check = None
        self.groups = []
        self.attachment = None
        self.private_ip_addresses = []

    def __repr__(self):
        return 'NetworkInterface:%s' % self.id

    def startElement(self, name, attrs, connection):
        retval = super(NetworkInterface, self).startElement(name, attrs, connection)
        if retval is not None:
            return retval
        if name == 'groupSet':
            self.groups = ResultSet([('item', Group)])
            return self.groups
        elif name == 'attachment':
            self.attachment = Attachment()
            return self.attachment
        elif name == 'privateIpAddressesSet':
            self.private_ip_addresses = ResultSet([('item', PrivateIPAddress)])
            return self.private_ip_addresses
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'networkInterfaceId':
            self.id = value
        elif name == 'subnetId':
            self.subnet_id = value
        elif name == 'vpcId':
            self.vpc_id = value
        elif name == 'availabilityZone':
            self.availability_zone = value
        elif name == 'description':
            self.description = value
        elif name == 'ownerId':
            self.owner_id = value
        elif name == 'requesterManaged':
            if value.lower() == 'true':
                self.requester_managed = True
            else:
                self.requester_managed = False
        elif name == 'status':
            self.status = value
        elif name == 'macAddress':
            self.mac_address = value
        elif name == 'privateIpAddress':
            self.private_ip_address = value
        elif name == 'sourceDestCheck':
            if value.lower() == 'true':
                self.source_dest_check = True
            else:
                self.source_dest_check = False
        else:
            setattr(self, name, value)

    def _update(self, updated):
        self.__dict__.update(updated.__dict__)

    def update(self, validate=False, dry_run=False):
        """
        Update the data associated with this ENI by querying EC2.

        :type validate: bool
        :param validate: By default, if EC2 returns no data about the
                         ENI the update method returns quietly.  If
                         the validate param is True, however, it will
                         raise a ValueError exception if no data is
                         returned from EC2.
        """
        rs = self.connection.get_all_network_interfaces(
            [self.id],
            dry_run=dry_run
        )
        if len(rs) > 0:
            self._update(rs[0])
        elif validate:
            raise ValueError('%s is not a valid ENI ID' % self.id)
        return self.status

    def attach(self, instance_id, device_index, dry_run=False):
        """
        Attach this ENI to an EC2 instance.

        :type instance_id: str
        :param instance_id: The ID of the EC2 instance to which it will
                            be attached.

        :type device_index: int
        :param device_index: The interface nunber, N, on the instance (eg. ethN)

        :rtype: bool
        :return: True if successful
        """
        return self.connection.attach_network_interface(
            self.id,
            instance_id,
            device_index,
            dry_run=dry_run
        )

    def detach(self, force=False, dry_run=False):
        """
        Detach this ENI from an EC2 instance.

        :type force: bool
        :param force: Forces detachment if the previous detachment
                      attempt did not occur cleanly.

        :rtype: bool
        :return: True if successful
        """
        attachment_id = getattr(self.attachment, 'id', None)

        return self.connection.detach_network_interface(
            attachment_id,
            force,
            dry_run=dry_run
        )

    def delete(self, dry_run=False):
        return self.connection.delete_network_interface(
            self.id,
            dry_run=dry_run
        )


class PrivateIPAddress(object):
    def __init__(self, connection=None, private_ip_address=None,
                 primary=None):
        self.connection = connection
        self.private_ip_address = private_ip_address
        self.primary = primary

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'privateIpAddress':
            self.private_ip_address = value
        elif name == 'primary':
            self.primary = True if value.lower() == 'true' else False

    def __repr__(self):
        return "PrivateIPAddress(%s, primary=%s)" % (self.private_ip_address,
                                                     self.primary)


class NetworkInterfaceCollection(list):
    def __init__(self, *interfaces):
        self.extend(interfaces)

    def build_list_params(self, params, prefix=''):
        for i, spec in enumerate(self):
            full_prefix = '%sNetworkInterface.%s.' % (prefix, i)
            if spec.network_interface_id is not None:
                params[full_prefix + 'NetworkInterfaceId'] = \
                        str(spec.network_interface_id)
            if spec.device_index is not None:
                params[full_prefix + 'DeviceIndex'] = \
                        str(spec.device_index)
            else:
                params[full_prefix + 'DeviceIndex'] = 0
            if spec.subnet_id is not None:
                params[full_prefix + 'SubnetId'] = str(spec.subnet_id)
            if spec.description is not None:
                params[full_prefix + 'Description'] = str(spec.description)
            if spec.delete_on_termination is not None:
                params[full_prefix + 'DeleteOnTermination'] = \
                        'true' if spec.delete_on_termination else 'false'
            if spec.secondary_private_ip_address_count is not None:
                params[full_prefix + 'SecondaryPrivateIpAddressCount'] = \
                        str(spec.secondary_private_ip_address_count)
            if spec.private_ip_address is not None:
                params[full_prefix + 'PrivateIpAddress'] = \
                        str(spec.private_ip_address)
            if spec.groups is not None:
                for j, group_id in enumerate(spec.groups):
                    query_param_key = '%sSecurityGroupId.%s' % (full_prefix, j)
                    params[query_param_key] = str(group_id)
            if spec.private_ip_addresses is not None:
                for k, ip_addr in enumerate(spec.private_ip_addresses):
                    query_param_key_prefix = (
                        '%sPrivateIpAddresses.%s' % (full_prefix, k))
                    params[query_param_key_prefix + '.PrivateIpAddress'] = \
                            str(ip_addr.private_ip_address)
                    if ip_addr.primary is not None:
                        params[query_param_key_prefix + '.Primary'] = \
                                'true' if ip_addr.primary else 'false'

            # Associating Public IPs have special logic around them:
            #
            # * Only assignable on an device_index of ``0``
            # * Only on one interface
            # * Only if there are no other interfaces being created
            # * Only if it's a new interface (which we can't really guard
            #   against)
            #
            # More details on http://docs.aws.amazon.com/AWSEC2/latest/APIReference/ApiReference-query-RunInstances.html
            if spec.associate_public_ip_address is not None:
                if not params[full_prefix + 'DeviceIndex'] in (0, '0'):
                    raise BotoClientError(
                        "Only the interface with device index of 0 can " + \
                        "be provided when using " + \
                        "'associate_public_ip_address'."
                    )

                if len(self) > 1:
                    raise BotoClientError(
                        "Only one interface can be provided when using " + \
                        "'associate_public_ip_address'."
                    )

                key = full_prefix + 'AssociatePublicIpAddress'

                if spec.associate_public_ip_address:
                    params[key] = 'true'
                else:
                    params[key] = 'false'


class NetworkInterfaceSpecification(object):
    def __init__(self, network_interface_id=None, device_index=None,
                 subnet_id=None, description=None, private_ip_address=None,
                 groups=None, delete_on_termination=None,
                 private_ip_addresses=None,
                 secondary_private_ip_address_count=None,
                 associate_public_ip_address=None):
        self.network_interface_id = network_interface_id
        self.device_index = device_index
        self.subnet_id = subnet_id
        self.description = description
        self.private_ip_address = private_ip_address
        self.groups = groups
        self.delete_on_termination = delete_on_termination
        self.private_ip_addresses = private_ip_addresses
        self.secondary_private_ip_address_count = \
                secondary_private_ip_address_count
        self.associate_public_ip_address = associate_public_ip_address
