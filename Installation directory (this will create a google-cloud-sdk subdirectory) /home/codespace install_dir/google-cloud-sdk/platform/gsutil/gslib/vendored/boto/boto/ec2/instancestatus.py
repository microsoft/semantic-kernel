# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.
# All Rights Reserved
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


class Details(dict):
    """
    A dict object that contains name/value pairs which provide
    more detailed information about the status of the system
    or the instance.
    """

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'name':
            self._name = value
        elif name == 'status':
            self[self._name] = value
        else:
            setattr(self, name, value)


class Event(object):
    """
    A status event for an instance.

    :ivar code: A string indicating the event type.
    :ivar description: A string describing the reason for the event.
    :ivar not_before: A datestring describing the earliest time for
        the event.
    :ivar not_after: A datestring describing the latest time for
        the event.
    """

    def __init__(self, code=None, description=None,
                 not_before=None, not_after=None):
        self.code = code
        self.description = description
        self.not_before = not_before
        self.not_after = not_after

    def __repr__(self):
        return 'Event:%s' % self.code

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'code':
            self.code = value
        elif name == 'description':
            self.description = value
        elif name == 'notBefore':
            self.not_before = value
        elif name == 'notAfter':
            self.not_after = value
        else:
            setattr(self, name, value)


class Status(object):
    """
    A generic Status object used for system status and instance status.

    :ivar status: A string indicating overall status.
    :ivar details: A dict containing name-value pairs which provide
        more details about the current status.
    """

    def __init__(self, status=None, details=None):
        self.status = status
        if not details:
            details = Details()
        self.details = details

    def __repr__(self):
        return 'Status:%s' % self.status

    def startElement(self, name, attrs, connection):
        if name == 'details':
            return self.details
        return None

    def endElement(self, name, value, connection):
        if name == 'status':
            self.status = value
        else:
            setattr(self, name, value)


class EventSet(list):

    def startElement(self, name, attrs, connection):
        if name == 'item':
            event = Event()
            self.append(event)
            return event
        else:
            return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)


class InstanceStatus(object):
    """
    Represents an EC2 Instance status as reported by
    DescribeInstanceStatus request.

    :ivar id: The instance identifier.
    :ivar zone: The availability zone of the instance.
    :ivar events: A list of events relevant to the instance.
    :ivar state_code: An integer representing the current state
        of the instance.
    :ivar state_name: A string describing the current state
        of the instance.
    :ivar system_status: A Status object that reports impaired
        functionality that stems from issues related to the systems
        that support an instance, such as such as hardware failures
        and network connectivity problems.
    :ivar instance_status: A Status object that reports impaired
        functionality that arises from problems internal to the instance.
    """

    def __init__(self, id=None, zone=None, events=None,
                 state_code=None, state_name=None):
        self.id = id
        self.zone = zone
        self.events = events
        self.state_code = state_code
        self.state_name = state_name
        self.system_status = Status()
        self.instance_status = Status()

    def __repr__(self):
        return 'InstanceStatus:%s' % self.id

    def startElement(self, name, attrs, connection):
        if name == 'eventsSet':
            self.events = EventSet()
            return self.events
        elif name == 'systemStatus':
            return self.system_status
        elif name == 'instanceStatus':
            return self.instance_status
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'instanceId':
            self.id = value
        elif name == 'availabilityZone':
            self.zone = value
        elif name == 'code':
            self.state_code = int(value)
        elif name == 'name':
            self.state_name = value
        else:
            setattr(self, name, value)


class InstanceStatusSet(list):
    """
    A list object that contains the results of a call to
    DescribeInstanceStatus request.  Each element of the
    list will be an InstanceStatus object.

    :ivar next_token: If the response was truncated by
        the EC2 service, the next_token attribute of the
        object will contain the string that needs to be
        passed in to the next request to retrieve the next
        set of results.
    """

    def __init__(self, connection=None):
        list.__init__(self)
        self.connection = connection
        self.next_token = None

    def startElement(self, name, attrs, connection):
        if name == 'item':
            status = InstanceStatus()
            self.append(status)
            return status
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'nextToken':
            self.next_token = value
        setattr(self, name, value)
