# Copyright (c) 2006-2010 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
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
Represents an EC2 Spot Instance Request
"""

from boto.ec2.ec2object import TaggedEC2Object
from boto.ec2.launchspecification import LaunchSpecification


class SpotInstanceStateFault(object):
    """
    The fault codes for the Spot Instance request, if any.

    :ivar code: The reason code for the Spot Instance state change.
    :ivar message: The message for the Spot Instance state change.
    """

    def __init__(self, code=None, message=None):
        self.code = code
        self.message = message

    def __repr__(self):
        return '(%s, %s)' % (self.code, self.message)

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'code':
            self.code = value
        elif name == 'message':
            self.message = value
        setattr(self, name, value)


class SpotInstanceStatus(object):
    """
    Contains the status of a Spot Instance Request.

    :ivar code: Status code of the request.
    :ivar message: The description for the status code for the Spot request.
    :ivar update_time: Time the status was stated.
    """

    def __init__(self, code=None, update_time=None, message=None):
        self.code = code
        self.update_time = update_time
        self.message = message

    def __repr__(self):
        return '<Status: %s>' % self.code

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'code':
            self.code = value
        elif name == 'message':
            self.message = value
        elif name == 'updateTime':
            self.update_time = value


class SpotInstanceRequest(TaggedEC2Object):
    """

    :ivar id: The ID of the Spot Instance Request.
    :ivar price: The maximum hourly price for any Spot Instance launched to
        fulfill the request.
    :ivar type: The Spot Instance request type.
    :ivar state: The state of the Spot Instance request.
    :ivar fault: The fault codes for the Spot Instance request, if any.
    :ivar valid_from: The start date of the request. If this is a one-time
        request, the request becomes active at this date and time and remains
        active until all instances launch, the request expires, or the request is
        canceled. If the request is persistent, the request becomes active at this
        date and time and remains active until it expires or is canceled.
    :ivar valid_until: The end date of the request. If this is a one-time
        request, the request remains active until all instances launch, the request
        is canceled, or this date is reached. If the request is persistent, it
        remains active until it is canceled or this date is reached.
    :ivar launch_group: The instance launch group. Launch groups are Spot
        Instances that launch together and terminate together.
    :ivar launched_availability_zone: foo
    :ivar product_description: The Availability Zone in which the bid is
        launched.
    :ivar availability_zone_group: The Availability Zone group. If you specify
        the same Availability Zone group for all Spot Instance requests, all Spot
        Instances are launched in the same Availability Zone.
    :ivar create_time: The time stamp when the Spot Instance request was
        created.
    :ivar launch_specification: Additional information for launching instances.
    :ivar instance_id: The instance ID, if an instance has been launched to
        fulfill the Spot Instance request.
    :ivar status: The status code and status message describing the Spot
        Instance request.

    """

    def __init__(self, connection=None):
        super(SpotInstanceRequest, self).__init__(connection)
        self.id = None
        self.price = None
        self.type = None
        self.state = None
        self.fault = None
        self.valid_from = None
        self.valid_until = None
        self.launch_group = None
        self.launched_availability_zone = None
        self.product_description = None
        self.availability_zone_group = None
        self.create_time = None
        self.launch_specification = None
        self.instance_id = None
        self.status = None

    def __repr__(self):
        return 'SpotInstanceRequest:%s' % self.id

    def startElement(self, name, attrs, connection):
        retval = super(SpotInstanceRequest, self).startElement(name, attrs,
            connection)
        if retval is not None:
            return retval
        if name == 'launchSpecification':
            self.launch_specification = LaunchSpecification(connection)
            return self.launch_specification
        elif name == 'fault':
            self.fault = SpotInstanceStateFault()
            return self.fault
        elif name == 'status':
            self.status = SpotInstanceStatus()
            return self.status
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'spotInstanceRequestId':
            self.id = value
        elif name == 'spotPrice':
            self.price = float(value)
        elif name == 'type':
            self.type = value
        elif name == 'state':
            self.state = value
        elif name == 'validFrom':
            self.valid_from = value
        elif name == 'validUntil':
            self.valid_until = value
        elif name == 'launchGroup':
            self.launch_group = value
        elif name == 'availabilityZoneGroup':
            self.availability_zone_group = value
        elif name == 'launchedAvailabilityZone':
            self.launched_availability_zone = value
        elif name == 'instanceId':
            self.instance_id = value
        elif name == 'createTime':
            self.create_time = value
        elif name == 'productDescription':
            self.product_description = value
        else:
            setattr(self, name, value)

    def cancel(self, dry_run=False):
        self.connection.cancel_spot_instance_requests(
            [self.id],
            dry_run=dry_run
        )
