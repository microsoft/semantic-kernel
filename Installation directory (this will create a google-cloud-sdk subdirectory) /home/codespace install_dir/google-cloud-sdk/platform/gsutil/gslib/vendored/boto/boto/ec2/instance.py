# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
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
Represents an EC2 Instance
"""
import boto
from boto.ec2.ec2object import EC2Object, TaggedEC2Object
from boto.resultset import ResultSet
from boto.ec2.address import Address
from boto.ec2.blockdevicemapping import BlockDeviceMapping
from boto.ec2.image import ProductCodes
from boto.ec2.networkinterface import NetworkInterface
from boto.ec2.group import Group
import base64


class InstanceState(object):
    """
    The state of the instance.

    :ivar code: The low byte represents the state. The high byte is an
        opaque internal value and should be ignored.  Valid values:

        * 0 (pending)
        * 16 (running)
        * 32 (shutting-down)
        * 48 (terminated)
        * 64 (stopping)
        * 80 (stopped)

    :ivar name: The name of the state of the instance.  Valid values:

        * "pending"
        * "running"
        * "shutting-down"
        * "terminated"
        * "stopping"
        * "stopped"
    """
    def __init__(self, code=0, name=None):
        self.code = code
        self.name = name

    def __repr__(self):
        return '%s(%d)' % (self.name, self.code)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'code':
            self.code = int(value)
        elif name == 'name':
            self.name = value
        else:
            setattr(self, name, value)


class InstancePlacement(object):
    """
    The location where the instance launched.

    :ivar zone: The Availability Zone of the instance.
    :ivar group_name: The name of the placement group the instance is
        in (for cluster compute instances).
    :ivar tenancy: The tenancy of the instance (if the instance is
        running within a VPC). An instance with a tenancy of dedicated
        runs on single-tenant hardware.
    """
    def __init__(self, zone=None, group_name=None, tenancy=None):
        self.zone = zone
        self.group_name = group_name
        self.tenancy = tenancy

    def __repr__(self):
        return self.zone

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'availabilityZone':
            self.zone = value
        elif name == 'groupName':
            self.group_name = value
        elif name == 'tenancy':
            self.tenancy = value
        else:
            setattr(self, name, value)


class Reservation(EC2Object):
    """
    Represents a Reservation response object.

    :ivar id: The unique ID of the Reservation.
    :ivar owner_id: The unique ID of the owner of the Reservation.
    :ivar groups: A list of Group objects representing the security
                  groups associated with launched instances.
    :ivar instances: A list of Instance objects launched in this
                     Reservation.
    """
    def __init__(self, connection=None):
        super(Reservation, self).__init__(connection)
        self.id = None
        self.owner_id = None
        self.groups = []
        self.instances = []

    def __repr__(self):
        return 'Reservation:%s' % self.id

    def startElement(self, name, attrs, connection):
        if name == 'instancesSet':
            self.instances = ResultSet([('item', Instance)])
            return self.instances
        elif name == 'groupSet':
            self.groups = ResultSet([('item', Group)])
            return self.groups
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'reservationId':
            self.id = value
        elif name == 'ownerId':
            self.owner_id = value
        else:
            setattr(self, name, value)

    def stop_all(self, dry_run=False):
        for instance in self.instances:
            instance.stop(dry_run=dry_run)


class Instance(TaggedEC2Object):
    """
    Represents an instance.

    :ivar id: The unique ID of the Instance.
    :ivar groups: A list of Group objects representing the security
                  groups associated with the instance.
    :ivar public_dns_name: The public dns name of the instance.
    :ivar private_dns_name: The private dns name of the instance.
    :ivar state: The string representation of the instance's current state.
    :ivar state_code: An integer representation of the instance's
        current state.
    :ivar previous_state: The string representation of the instance's
        previous state.
    :ivar previous_state_code: An integer representation of the
        instance's current state.
    :ivar key_name: The name of the SSH key associated with the instance.
    :ivar instance_type: The type of instance (e.g. m1.small).
    :ivar launch_time: The time the instance was launched.
    :ivar image_id: The ID of the AMI used to launch this instance.
    :ivar placement: The availability zone in which the instance is running.
    :ivar placement_group: The name of the placement group the instance
        is in (for cluster compute instances).
    :ivar placement_tenancy: The tenancy of the instance, if the instance
        is running within a VPC.  An instance with a tenancy of dedicated
        runs on a single-tenant hardware.
    :ivar kernel: The kernel associated with the instance.
    :ivar ramdisk: The ramdisk associated with the instance.
    :ivar architecture: The architecture of the image (i386|x86_64).
    :ivar hypervisor: The hypervisor used.
    :ivar virtualization_type: The type of virtualization used.
    :ivar product_codes: A list of product codes associated with this instance.
    :ivar ami_launch_index: This instances position within it's launch group.
    :ivar monitored: A boolean indicating whether monitoring is enabled or not.
    :ivar monitoring_state: A string value that contains the actual value
        of the monitoring element returned by EC2.
    :ivar spot_instance_request_id: The ID of the spot instance request
        if this is a spot instance.
    :ivar subnet_id: The VPC Subnet ID, if running in VPC.
    :ivar vpc_id: The VPC ID, if running in VPC.
    :ivar private_ip_address: The private IP address of the instance.
    :ivar ip_address: The public IP address of the instance.
    :ivar platform: Platform of the instance (e.g. Windows)
    :ivar root_device_name: The name of the root device.
    :ivar root_device_type: The root device type (ebs|instance-store).
    :ivar block_device_mapping: The Block Device Mapping for the instance.
    :ivar state_reason: The reason for the most recent state transition.
    :ivar interfaces: List of Elastic Network Interfaces associated with
        this instance.
    :ivar ebs_optimized: Whether instance is using optimized EBS volumes
        or not.
    :ivar instance_profile: A Python dict containing the instance
        profile id and arn associated with this instance.
    """

    def __init__(self, connection=None):
        super(Instance, self).__init__(connection)
        self.id = None
        self.dns_name = None
        self.public_dns_name = None
        self.private_dns_name = None
        self.key_name = None
        self.instance_type = None
        self.launch_time = None
        self.image_id = None
        self.kernel = None
        self.ramdisk = None
        self.product_codes = ProductCodes()
        self.ami_launch_index = None
        self.monitored = False
        self.monitoring_state = None
        self.spot_instance_request_id = None
        self.subnet_id = None
        self.vpc_id = None
        self.private_ip_address = None
        self.ip_address = None
        self.requester_id = None
        self._in_monitoring_element = False
        self.persistent = False
        self.root_device_name = None
        self.root_device_type = None
        self.block_device_mapping = None
        self.state_reason = None
        self.group_name = None
        self.client_token = None
        self.eventsSet = None
        self.groups = []
        self.platform = None
        self.interfaces = []
        self.hypervisor = None
        self.virtualization_type = None
        self.architecture = None
        self.instance_profile = None
        self._previous_state = None
        self._state = InstanceState()
        self._placement = InstancePlacement()

    def __repr__(self):
        return 'Instance:%s' % self.id

    @property
    def state(self):
        return self._state.name

    @property
    def state_code(self):
        return self._state.code

    @property
    def previous_state(self):
        if self._previous_state:
            return self._previous_state.name
        return None

    @property
    def previous_state_code(self):
        if self._previous_state:
            return self._previous_state.code
        return 0

    @property
    def placement(self):
        return self._placement.zone

    @property
    def placement_group(self):
        return self._placement.group_name

    @property
    def placement_tenancy(self):
        return self._placement.tenancy

    def startElement(self, name, attrs, connection):
        retval = super(Instance, self).startElement(name, attrs, connection)
        if retval is not None:
            return retval
        if name == 'monitoring':
            self._in_monitoring_element = True
        elif name == 'blockDeviceMapping':
            self.block_device_mapping = BlockDeviceMapping()
            return self.block_device_mapping
        elif name == 'productCodes':
            return self.product_codes
        elif name == 'stateReason':
            self.state_reason = SubParse('stateReason')
            return self.state_reason
        elif name == 'groupSet':
            self.groups = ResultSet([('item', Group)])
            return self.groups
        elif name == "eventsSet":
            self.eventsSet = SubParse('eventsSet')
            return self.eventsSet
        elif name == 'networkInterfaceSet':
            self.interfaces = ResultSet([('item', NetworkInterface)])
            return self.interfaces
        elif name == 'iamInstanceProfile':
            self.instance_profile = SubParse('iamInstanceProfile')
            return self.instance_profile
        elif name == 'currentState':
            return self._state
        elif name == 'previousState':
            self._previous_state = InstanceState()
            return self._previous_state
        elif name == 'instanceState':
            return self._state
        elif name == 'placement':
            return self._placement
        return None

    def endElement(self, name, value, connection):
        if name == 'instanceId':
            self.id = value
        elif name == 'imageId':
            self.image_id = value
        elif name == 'dnsName' or name == 'publicDnsName':
            self.dns_name = value           # backwards compatibility
            self.public_dns_name = value
        elif name == 'privateDnsName':
            self.private_dns_name = value
        elif name == 'keyName':
            self.key_name = value
        elif name == 'amiLaunchIndex':
            self.ami_launch_index = value
        elif name == 'previousState':
            self.previous_state = value
        elif name == 'instanceType':
            self.instance_type = value
        elif name == 'rootDeviceName':
            self.root_device_name = value
        elif name == 'rootDeviceType':
            self.root_device_type = value
        elif name == 'launchTime':
            self.launch_time = value
        elif name == 'platform':
            self.platform = value
        elif name == 'kernelId':
            self.kernel = value
        elif name == 'ramdiskId':
            self.ramdisk = value
        elif name == 'state':
            if self._in_monitoring_element:
                self.monitoring_state = value
                if value == 'enabled':
                    self.monitored = True
                self._in_monitoring_element = False
        elif name == 'spotInstanceRequestId':
            self.spot_instance_request_id = value
        elif name == 'subnetId':
            self.subnet_id = value
        elif name == 'vpcId':
            self.vpc_id = value
        elif name == 'privateIpAddress':
            self.private_ip_address = value
        elif name == 'ipAddress':
            self.ip_address = value
        elif name == 'requesterId':
            self.requester_id = value
        elif name == 'persistent':
            if value == 'true':
                self.persistent = True
            else:
                self.persistent = False
        elif name == 'groupName':
            if self._in_monitoring_element:
                self.group_name = value
        elif name == 'clientToken':
            self.client_token = value
        elif name == "eventsSet":
            self.events = value
        elif name == 'hypervisor':
            self.hypervisor = value
        elif name == 'virtualizationType':
            self.virtualization_type = value
        elif name == 'architecture':
            self.architecture = value
        elif name == 'ebsOptimized':
            self.ebs_optimized = (value == 'true')
        else:
            setattr(self, name, value)

    def _update(self, updated):
        self.__dict__.update(updated.__dict__)

    def update(self, validate=False, dry_run=False):
        """
        Update the instance's state information by making a call to fetch
        the current instance attributes from the service.

        :type validate: bool
        :param validate: By default, if EC2 returns no data about the
                         instance the update method returns quietly.  If
                         the validate param is True, however, it will
                         raise a ValueError exception if no data is
                         returned from EC2.
        """
        rs = self.connection.get_all_reservations([self.id], dry_run=dry_run)
        if len(rs) > 0:
            r = rs[0]
            for i in r.instances:
                if i.id == self.id:
                    self._update(i)
        elif validate:
            raise ValueError('%s is not a valid Instance ID' % self.id)
        return self.state

    def terminate(self, dry_run=False):
        """
        Terminate the instance
        """
        rs = self.connection.terminate_instances([self.id], dry_run=dry_run)
        if len(rs) > 0:
            self._update(rs[0])

    def stop(self, force=False, dry_run=False):
        """
        Stop the instance

        :type force: bool
        :param force: Forces the instance to stop

        :rtype: list
        :return: A list of the instances stopped
        """
        rs = self.connection.stop_instances([self.id], force, dry_run=dry_run)
        if len(rs) > 0:
            self._update(rs[0])

    def start(self, dry_run=False):
        """
        Start the instance.
        """
        rs = self.connection.start_instances([self.id], dry_run=dry_run)
        if len(rs) > 0:
            self._update(rs[0])

    def reboot(self, dry_run=False):
        return self.connection.reboot_instances([self.id], dry_run=dry_run)

    def get_console_output(self, dry_run=False):
        """
        Retrieves the console output for the instance.

        :rtype: :class:`boto.ec2.instance.ConsoleOutput`
        :return: The console output as a ConsoleOutput object
        """
        return self.connection.get_console_output(self.id, dry_run=dry_run)

    def confirm_product(self, product_code, dry_run=False):
        return self.connection.confirm_product_instance(
            self.id,
            product_code,
            dry_run=dry_run
        )

    def use_ip(self, ip_address, dry_run=False):
        """
        Associates an Elastic IP to the instance.

        :type ip_address: Either an instance of
            :class:`boto.ec2.address.Address` or a string.
        :param ip_address: The IP address to associate
            with the instance.

        :rtype: bool
        :return: True if successful
        """

        if isinstance(ip_address, Address):
            ip_address = ip_address.public_ip
        return self.connection.associate_address(
            self.id,
            ip_address,
            dry_run=dry_run
        )

    def monitor(self, dry_run=False):
        return self.connection.monitor_instance(self.id, dry_run=dry_run)

    def unmonitor(self, dry_run=False):
        return self.connection.unmonitor_instance(self.id, dry_run=dry_run)

    def get_attribute(self, attribute, dry_run=False):
        """
        Gets an attribute from this instance.

        :type attribute: string
        :param attribute: The attribute you need information about
            Valid choices are:

            * instanceType
            * kernel
            * ramdisk
            * userData
            * disableApiTermination
            * instanceInitiatedShutdownBehavior
            * rootDeviceName
            * blockDeviceMapping
            * productCodes
            * sourceDestCheck
            * groupSet
            * ebsOptimized

        :rtype: :class:`boto.ec2.image.InstanceAttribute`
        :return: An InstanceAttribute object representing the value of the
                 attribute requested
        """
        return self.connection.get_instance_attribute(
            self.id,
            attribute,
            dry_run=dry_run
        )

    def modify_attribute(self, attribute, value, dry_run=False):
        """
        Changes an attribute of this instance

        :type attribute: string
        :param attribute: The attribute you wish to change.

            * instanceType - A valid instance type (m1.small)
            * kernel - Kernel ID (None)
            * ramdisk - Ramdisk ID (None)
            * userData - Base64 encoded String (None)
            * disableApiTermination - Boolean (true)
            * instanceInitiatedShutdownBehavior - stop|terminate
            * sourceDestCheck - Boolean (true)
            * groupSet - Set of Security Groups or IDs
            * ebsOptimized - Boolean (false)

        :type value: string
        :param value: The new value for the attribute

        :rtype: bool
        :return: Whether the operation succeeded or not
        """
        return self.connection.modify_instance_attribute(
            self.id,
            attribute,
            value,
            dry_run=dry_run
        )

    def reset_attribute(self, attribute, dry_run=False):
        """
        Resets an attribute of this instance to its default value.

        :type attribute: string
        :param attribute: The attribute to reset. Valid values are:
                          kernel|ramdisk

        :rtype: bool
        :return: Whether the operation succeeded or not
        """
        return self.connection.reset_instance_attribute(
            self.id,
            attribute,
            dry_run=dry_run
        )

    def create_image(self, name, description=None, no_reboot=False,
                     dry_run=False):
        """
        Will create an AMI from the instance in the running or stopped
        state.

        :type name: string
        :param name: The name of the new image

        :type description: string
        :param description: An optional human-readable string describing
                            the contents and purpose of the AMI.

        :type no_reboot: bool
        :param no_reboot: An optional flag indicating that the bundling process
                          should not attempt to shutdown the instance before
                          bundling.  If this flag is True, the responsibility
                          of maintaining file system integrity is left to the
                          owner of the instance.

        :rtype: string
        :return: The new image id
        """
        return self.connection.create_image(
            self.id,
            name,
            description,
            no_reboot,
            dry_run=dry_run
        )


class ConsoleOutput(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.instance_id = None
        self.timestamp = None
        self.output = None

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'instanceId':
            self.instance_id = value
        elif name == 'timestamp':
            self.timestamp = value
        elif name == 'output':
            self.output = base64.b64decode(value)
        else:
            setattr(self, name, value)


class InstanceAttribute(dict):
    ValidValues = ['instanceType', 'kernel', 'ramdisk', 'userData',
                   'disableApiTermination',
                   'instanceInitiatedShutdownBehavior',
                   'rootDeviceName', 'blockDeviceMapping', 'sourceDestCheck',
                   'groupSet']

    def __init__(self, parent=None):
        dict.__init__(self)
        self.instance_id = None
        self.request_id = None
        self._current_value = None

    def startElement(self, name, attrs, connection):
        if name == 'blockDeviceMapping':
            self[name] = BlockDeviceMapping()
            return self[name]
        elif name == 'groupSet':
            self[name] = ResultSet([('item', Group)])
            return self[name]
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'instanceId':
            self.instance_id = value
        elif name == 'requestId':
            self.request_id = value
        elif name == 'value':
            if value == 'true':
                value = True
            elif value == 'false':
                value = False
            self._current_value = value
        elif name in self.ValidValues:
            self[name] = self._current_value


class SubParse(dict):
    def __init__(self, section, parent=None):
        dict.__init__(self)
        self.section = section

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name != self.section:
            self[name] = value
