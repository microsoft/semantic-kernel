# Copyright (c) 2006,2007 Mitch Garnaat http://garnaat.org/
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
Provides NotificationMessage and Event classes, with utility methods, for
implementations of the Mechanical Turk Notification API.
"""

import hmac
try:
    from hashlib import sha1 as sha
except ImportError:
    import sha
import base64
import re

class NotificationMessage(object):

    NOTIFICATION_WSDL = "http://mechanicalturk.amazonaws.com/AWSMechanicalTurk/2006-05-05/AWSMechanicalTurkRequesterNotification.wsdl"
    NOTIFICATION_VERSION = '2006-05-05'

    SERVICE_NAME = "AWSMechanicalTurkRequesterNotification"
    OPERATION_NAME = "Notify"

    EVENT_PATTERN = r"Event\.(?P<n>\d+)\.(?P<param>\w+)"
    EVENT_RE = re.compile(EVENT_PATTERN)

    def __init__(self, d):
        """
        Constructor; expects parameter d to be a dict of string parameters from a REST transport notification message
        """
        self.signature = d['Signature'] # vH6ZbE0NhkF/hfNyxz2OgmzXYKs=
        self.timestamp = d['Timestamp'] # 2006-05-23T23:22:30Z
        self.version = d['Version'] # 2006-05-05
        assert d['method'] == NotificationMessage.OPERATION_NAME, "Method should be '%s'" % NotificationMessage.OPERATION_NAME

        # Build Events
        self.events = []
        events_dict = {}
        if 'Event' in d:
            # TurboGears surprised me by 'doing the right thing' and making { 'Event': { '1': { 'EventType': ... } } } etc.
            events_dict = d['Event']
        else:
            for k in d:
                v = d[k]
                if k.startswith('Event.'):
                    ed = NotificationMessage.EVENT_RE.search(k).groupdict()
                    n = int(ed['n'])
                    param = str(ed['param'])
                    if n not in events_dict:
                        events_dict[n] = {}
                    events_dict[n][param] = v
        for n in events_dict:
            self.events.append(Event(events_dict[n]))

    def verify(self, secret_key):
        """
        Verifies the authenticity of a notification message.

        TODO: This is doing a form of authentication and
              this functionality should really be merged
              with the pluggable authentication mechanism
              at some point.
        """
        verification_input = NotificationMessage.SERVICE_NAME
        verification_input += NotificationMessage.OPERATION_NAME
        verification_input += self.timestamp
        h = hmac.new(key=secret_key, digestmod=sha)
        h.update(verification_input)
        signature_calc = base64.b64encode(h.digest())
        return self.signature == signature_calc

class Event(object):
    def __init__(self, d):
        self.event_type = d['EventType']
        self.event_time_str = d['EventTime']
        self.hit_type = d['HITTypeId']
        self.hit_id = d['HITId']
        if 'AssignmentId' in d:   # Not present in all event types
            self.assignment_id = d['AssignmentId']

        #TODO: build self.event_time datetime from string self.event_time_str

    def __repr__(self):
        return "<boto.mturk.notification.Event: %s for HIT # %s>" % (self.event_type, self.hit_id)
