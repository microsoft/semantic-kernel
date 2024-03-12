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

from boto.ec2.instancestatus import Status, Details


class Event(object):
    """
    A status event for an instance.

    :ivar type: The type of the event.
    :ivar id: The ID of the event.
    :ivar description: A string describing the reason for the event.
    :ivar not_before: A datestring describing the earliest time for
        the event.
    :ivar not_after: A datestring describing the latest time for
        the event.
    """

    def __init__(self, type=None, id=None, description=None,
                 not_before=None, not_after=None):
        self.type = type
        self.id = id
        self.description = description
        self.not_before = not_before
        self.not_after = not_after

    def __repr__(self):
        return 'Event:%s' % self.type

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'eventType':
            self.type = value
        elif name == 'eventId':
            self.id = value
        elif name == 'description':
            self.description = value
        elif name == 'notBefore':
            self.not_before = value
        elif name == 'notAfter':
            self.not_after = value
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


class Action(object):
    """
    An action for an instance.

    :ivar code: The code for the type of the action.
    :ivar id: The ID of the event.
    :ivar type: The type of the event.
    :ivar description: A description of the action.
    """

    def __init__(self, code=None, id=None, description=None, type=None):
        self.code = code
        self.id = id
        self.type = type
        self.description = description

    def __repr__(self):
        return 'Action:%s' % self.code

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'eventType':
            self.type = value
        elif name == 'eventId':
            self.id = value
        elif name == 'description':
            self.description = value
        elif name == 'code':
            self.code = value
        else:
            setattr(self, name, value)


class ActionSet(list):

    def startElement(self, name, attrs, connection):
        if name == 'item':
            action = Action()
            self.append(action)
            return action
        else:
            return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)


class VolumeStatus(object):
    """
    Represents an EC2 Volume status as reported by
    DescribeVolumeStatus request.

    :ivar id: The volume identifier.
    :ivar zone: The availability zone of the volume
    :ivar volume_status: A Status object that reports impaired
        functionality that arises from problems internal to the instance.
    :ivar events: A list of events relevant to the instance.
    :ivar actions: A list of events relevant to the instance.
    """

    def __init__(self, id=None, zone=None):
        self.id = id
        self.zone = zone
        self.volume_status = Status()
        self.events = None
        self.actions = None

    def __repr__(self):
        return 'VolumeStatus:%s' % self.id

    def startElement(self, name, attrs, connection):
        if name == 'eventsSet':
            self.events = EventSet()
            return self.events
        elif name == 'actionsSet':
            self.actions = ActionSet()
            return self.actions
        elif name == 'volumeStatus':
            return self.volume_status
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'volumeId':
            self.id = value
        elif name == 'availabilityZone':
            self.zone = value
        else:
            setattr(self, name, value)


class VolumeStatusSet(list):
    """
    A list object that contains the results of a call to
    DescribeVolumeStatus request.  Each element of the
    list will be an VolumeStatus object.

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
            status = VolumeStatus()
            self.append(status)
            return status
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'NextToken':
            self.next_token = value
        setattr(self, name, value)
