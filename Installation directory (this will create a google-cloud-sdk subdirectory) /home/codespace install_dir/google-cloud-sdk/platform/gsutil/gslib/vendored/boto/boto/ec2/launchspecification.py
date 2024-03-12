# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
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
Represents a launch specification for Spot instances.
"""

from boto.ec2.ec2object import EC2Object
from boto.resultset import ResultSet
from boto.ec2.blockdevicemapping import BlockDeviceMapping
from boto.ec2.group import Group
from boto.ec2.instance import SubParse


class GroupList(list):

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'groupId':
            self.append(value)


class LaunchSpecification(EC2Object):

    def __init__(self, connection=None):
        super(LaunchSpecification, self).__init__(connection)
        self.key_name = None
        self.instance_type = None
        self.image_id = None
        self.groups = []
        self.placement = None
        self.kernel = None
        self.ramdisk = None
        self.monitored = False
        self.subnet_id = None
        self._in_monitoring_element = False
        self.block_device_mapping = None
        self.instance_profile = None
        self.ebs_optimized = False

    def __repr__(self):
        return 'LaunchSpecification(%s)' % self.image_id

    def startElement(self, name, attrs, connection):
        if name == 'groupSet':
            self.groups = ResultSet([('item', Group)])
            return self.groups
        elif name == 'monitoring':
            self._in_monitoring_element = True
        elif name == 'blockDeviceMapping':
            self.block_device_mapping = BlockDeviceMapping()
            return self.block_device_mapping
        elif name == 'iamInstanceProfile':
            self.instance_profile = SubParse('iamInstanceProfile')
            return self.instance_profile
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'imageId':
            self.image_id = value
        elif name == 'keyName':
            self.key_name = value
        elif name == 'instanceType':
            self.instance_type = value
        elif name == 'availabilityZone':
            self.placement = value
        elif name == 'placement':
            pass
        elif name == 'kernelId':
            self.kernel = value
        elif name == 'ramdiskId':
            self.ramdisk = value
        elif name == 'subnetId':
            self.subnet_id = value
        elif name == 'state':
            if self._in_monitoring_element:
                if value == 'enabled':
                    self.monitored = True
                self._in_monitoring_element = False
        elif name == 'ebsOptimized':
            self.ebs_optimized = (value == 'true')
        else:
            setattr(self, name, value)
