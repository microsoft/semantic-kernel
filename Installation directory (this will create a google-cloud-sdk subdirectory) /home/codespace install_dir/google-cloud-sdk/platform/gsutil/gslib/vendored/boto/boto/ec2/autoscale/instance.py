# Copyright (c) 2009 Reza Lotun http://reza.lotun.name/
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


class Instance(object):
    def __init__(self, connection=None):
        self.connection = connection
        self.instance_id = None
        self.health_status = None
        self.launch_config_name = None
        self.lifecycle_state = None
        self.availability_zone = None
        self.group_name = None

    def __repr__(self):
        r = 'Instance<id:%s, state:%s, health:%s' % (self.instance_id,
                                                     self.lifecycle_state,
                                                     self.health_status)
        if self.group_name:
            r += ' group:%s' % self.group_name
        r += '>'
        return r

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'InstanceId':
            self.instance_id = value
        elif name == 'HealthStatus':
            self.health_status = value
        elif name == 'LaunchConfigurationName':
            self.launch_config_name = value
        elif name == 'LifecycleState':
            self.lifecycle_state = value
        elif name == 'AvailabilityZone':
            self.availability_zone = value
        elif name == 'AutoScalingGroupName':
            self.group_name = value
        else:
            setattr(self, name, value)
