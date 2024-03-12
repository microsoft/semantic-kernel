# Copyright (c) 2009 Reza Lotun http://reza.lotun.name/
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

from boto.ec2.elb.listelement import ListElement
# Namespacing issue with deprecated local class
from boto.ec2.blockdevicemapping import BlockDeviceMapping as BDM
from boto.resultset import ResultSet
import boto.utils
import base64


# this should use the corresponding object from boto.ec2
# Currently in use by deprecated local BlockDeviceMapping class
class Ebs(object):
    def __init__(self, connection=None, snapshot_id=None, volume_size=None):
        self.connection = connection
        self.snapshot_id = snapshot_id
        self.volume_size = volume_size

    def __repr__(self):
        return 'Ebs(%s, %s)' % (self.snapshot_id, self.volume_size)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'SnapshotId':
            self.snapshot_id = value
        elif name == 'VolumeSize':
            self.volume_size = value


class InstanceMonitoring(object):
    def __init__(self, connection=None, enabled='false'):
        self.connection = connection
        self.enabled = enabled

    def __repr__(self):
        return 'InstanceMonitoring(%s)' % self.enabled

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Enabled':
            self.enabled = value


# this should use the BlockDeviceMapping from boto.ec2.blockdevicemapping
# Currently in use by deprecated code for backwards compatability
# Removing this class can also remove the Ebs class in this same file
class BlockDeviceMapping(object):
    def __init__(self, connection=None, device_name=None, virtual_name=None,
                 ebs=None, no_device=None):
        self.connection = connection
        self.device_name = device_name
        self.virtual_name = virtual_name
        self.ebs = ebs
        self.no_device = no_device

    def __repr__(self):
        return 'BlockDeviceMapping(%s, %s)' % (self.device_name,
                                               self.virtual_name)

    def startElement(self, name, attrs, connection):
        if name == 'Ebs':
            self.ebs = Ebs(self)
            return self.ebs

    def endElement(self, name, value, connection):
        if name == 'DeviceName':
            self.device_name = value
        elif name == 'VirtualName':
            self.virtual_name = value
        elif name == 'NoDevice':
            self.no_device = bool(value)


class LaunchConfiguration(object):
    def __init__(self, connection=None, name=None, image_id=None,
                 key_name=None, security_groups=None, user_data=None,
                 instance_type='m1.small', kernel_id=None,
                 ramdisk_id=None, block_device_mappings=None,
                 instance_monitoring=False, spot_price=None,
                 instance_profile_name=None, ebs_optimized=False,
                 associate_public_ip_address=None, volume_type=None,
                 delete_on_termination=True, iops=None,
                 use_block_device_types=False, classic_link_vpc_id=None,
                 classic_link_vpc_security_groups=None):
        """
        A launch configuration.

        :type name: str
        :param name: Name of the launch configuration to create.

        :type image_id: str
        :param image_id: Unique ID of the Amazon Machine Image (AMI) which was
            assigned during registration.

        :type key_name: str
        :param key_name: The name of the EC2 key pair.

        :type security_groups: list
        :param security_groups: Names or security group id's of the security
            groups with which to associate the EC2 instances or VPC instances,
            respectively.

        :type user_data: str
        :param user_data: The user data available to launched EC2 instances.

        :type instance_type: str
        :param instance_type: The instance type

        :type kernel_id: str
        :param kernel_id: Kernel id for instance

        :type ramdisk_id: str
        :param ramdisk_id: RAM disk id for instance

        :type block_device_mappings: list
        :param block_device_mappings: Specifies how block devices are exposed
            for instances

        :type instance_monitoring: bool
        :param instance_monitoring: Whether instances in group are launched
            with detailed monitoring.

        :type spot_price: float
        :param spot_price: The spot price you are bidding.  Only applies
            if you are building an autoscaling group with spot instances.

        :type instance_profile_name: string
        :param instance_profile_name: The name or the Amazon Resource
            Name (ARN) of the instance profile associated with the IAM
            role for the instance.

        :type ebs_optimized: bool
        :param ebs_optimized: Specifies whether the instance is optimized
            for EBS I/O (true) or not (false).


        :type associate_public_ip_address: bool
        :param associate_public_ip_address: Used for Auto Scaling groups that launch instances into an Amazon Virtual Private Cloud.
            Specifies whether to assign a public IP address to each instance launched in a Amazon VPC.

        :type classic_link_vpc_id: str
        :param classic_link_vpc_id: ID of ClassicLink enabled VPC.

        :type classic_link_vpc_security_groups: list
        :param classic_link_vpc_security_groups: Security group
            id's of the security groups with which to associate the
            ClassicLink VPC instances.
        """
        self.connection = connection
        self.name = name
        self.instance_type = instance_type
        self.block_device_mappings = block_device_mappings
        self.key_name = key_name
        sec_groups = security_groups or []
        self.security_groups = ListElement(sec_groups)
        self.image_id = image_id
        self.ramdisk_id = ramdisk_id
        self.created_time = None
        self.kernel_id = kernel_id
        self.user_data = user_data
        self.created_time = None
        self.instance_monitoring = instance_monitoring
        self.spot_price = spot_price
        self.instance_profile_name = instance_profile_name
        self.launch_configuration_arn = None
        self.ebs_optimized = ebs_optimized
        self.associate_public_ip_address = associate_public_ip_address
        self.volume_type = volume_type
        self.delete_on_termination = delete_on_termination
        self.iops = iops
        self.use_block_device_types = use_block_device_types
        self.classic_link_vpc_id = classic_link_vpc_id
        classic_link_vpc_sec_groups = classic_link_vpc_security_groups or []
        self.classic_link_vpc_security_groups = \
            ListElement(classic_link_vpc_sec_groups)

        if connection is not None:
            self.use_block_device_types = connection.use_block_device_types

    def __repr__(self):
        return 'LaunchConfiguration:%s' % self.name

    def startElement(self, name, attrs, connection):
        if name == 'SecurityGroups':
            return self.security_groups
        elif name == 'ClassicLinkVPCSecurityGroups':
            return self.classic_link_vpc_security_groups
        elif name == 'BlockDeviceMappings':
            if self.use_block_device_types:
                self.block_device_mappings = BDM()
            else:
                self.block_device_mappings = ResultSet([('member', BlockDeviceMapping)])
            return self.block_device_mappings
        elif name == 'InstanceMonitoring':
            self.instance_monitoring = InstanceMonitoring(self)
            return self.instance_monitoring

    def endElement(self, name, value, connection):
        if name == 'InstanceType':
            self.instance_type = value
        elif name == 'LaunchConfigurationName':
            self.name = value
        elif name == 'KeyName':
            self.key_name = value
        elif name == 'ImageId':
            self.image_id = value
        elif name == 'CreatedTime':
            self.created_time = boto.utils.parse_ts(value)
        elif name == 'KernelId':
            self.kernel_id = value
        elif name == 'RamdiskId':
            self.ramdisk_id = value
        elif name == 'UserData':
            try:
                self.user_data = base64.b64decode(value)
            except TypeError:
                self.user_data = value
        elif name == 'LaunchConfigurationARN':
            self.launch_configuration_arn = value
        elif name == 'InstanceMonitoring':
            self.instance_monitoring = value
        elif name == 'SpotPrice':
            self.spot_price = float(value)
        elif name == 'IamInstanceProfile':
            self.instance_profile_name = value
        elif name == 'EbsOptimized':
            self.ebs_optimized = True if value.lower() == 'true' else False
        elif name == 'AssociatePublicIpAddress':
            self.associate_public_ip_address = True if value.lower() == 'true' else False
        elif name == 'VolumeType':
            self.volume_type = value
        elif name == 'DeleteOnTermination':
            if value.lower() == 'true':
                self.delete_on_termination = True
            else:
                self.delete_on_termination = False
        elif name == 'Iops':
            self.iops = int(value)
        elif name == 'ClassicLinkVPCId':
            self.classic_link_vpc_id = value
        else:
            setattr(self, name, value)

    def delete(self):
        """ Delete this launch configuration. """
        return self.connection.delete_launch_configuration(self.name)
